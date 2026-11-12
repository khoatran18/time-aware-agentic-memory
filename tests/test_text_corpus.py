"""Kho text thuần và công cụ của agent kiểu A (`tam.tools.text_corpus`). Không cần LLM, Qdrant hay embedding."""
import json

import pytest

from tam.ingestion.chunking import chunk_document
from tam.ingestion.loaders.timeqa import load_pages
from tam.tools.text_corpus import (
    HARD_MAX_HITS,
    TextCorpus,
    ToolError,
    build_corpus,
    file_name,
    page_id_of,
)

PAGES = [
    {"page_id": "/wiki/Alpha_FC", "context": "", "paragraphs": [
        {"title": "Alpha FC", "text": "Alpha FC is a club founded in 1900."},
        {"title": "History", "text": ""},  # rỗng: bị bỏ nhưng chỉ số 2 vẫn là 2
        {"title": "History", "text": "In 1950 the club won the league.\n\nIn 1960 it was relegated."},
        {"title": "Honours", "text": "League: 1950, 1951."},
    ]},
    {"page_id": "/wiki/Escadron_1/2_Cigognes", "context": "", "paragraphs": [{"title": "Escadron 1/2", "text": "A French squadron."}]},
    {"page_id": "/wiki/Beta", "context": "", "paragraphs": [{"title": "Beta", "text": "Beta is a place. Alpha FC played there in 1950."}]},
]
SPLIT = {"/wiki/Alpha_FC": "tune", "/wiki/Escadron_1/2_Cigognes": "valid", "/wiki/Beta": "test_clean"}


@pytest.fixture()
def corpus_dir(tmp_path):
    pages = tmp_path / "pages.jsonl"
    pages.write_text("\n".join(json.dumps(p) for p in PAGES), encoding="utf-8")
    out = tmp_path / "corpus"
    build_corpus(pages, SPLIT, out)
    return tmp_path, out


@pytest.fixture()
def corpus(corpus_dir):
    return TextCorpus.load(corpus_dir[1])


def test_file_name_and_page_id_roundtrip():
    assert file_name("/wiki/Knox_Cunningham") == "Knox_Cunningham.txt"
    assert file_name("/wiki/Escadron_1/2_Cigognes") == "Escadron_1%2F2_Cigognes.txt"
    assert page_id_of("Escadron_1%2F2_Cigognes") == "/wiki/Escadron_1/2_Cigognes"


def test_build_only_requested_pages_and_index_outside(corpus_dir, tmp_path):
    root, out = corpus_dir
    assert sorted(p.name for p in out.iterdir()) == ["Alpha_FC.txt", "Beta.txt", "Escadron_1%2F2_Cigognes.txt"]
    pages = root / "pages.jsonl"
    out2 = root / "corpus2"
    index = build_corpus(pages, {"/wiki/Beta": "valid"}, out2)
    assert [p.name for p in out2.iterdir()] == ["Beta.txt"] and index == {"/wiki/Beta": {"file": "Beta.txt", "split": "valid"}}


def test_files_hold_only_chunk_text_no_labels(corpus_dir):
    """Tên tập không được lọt vào file; văn bản mỗi đoạn trùng chunk của ingestion."""
    root, out = corpus_dir
    for p in out.iterdir():
        t = p.read_text(encoding="utf-8")
        assert not any(w in t for w in ("tune", "valid", "test_clean", "start_time", "end_time"))
    docs = {d.doc_id: d for d in load_pages(root / "pages.jsonl")}
    corpus = TextCorpus.load(out)
    for pid, d in docs.items():
        got = {p.idx: p.text for p in corpus.pages[page_id_of_name(pid)]}
        assert got == {int(c.chunk_id.rpartition("#")[2]): c.text for c in chunk_document(d)}


def page_id_of_name(page_id):
    return file_name(page_id).removesuffix(".txt")


def test_empty_section_keeps_chunk_index(corpus):
    assert [p.idx for p in corpus.pages["Alpha_FC"]] == [0, 2, 3]
    # đoạn chứa dòng trống bên trong không bị tách làm đôi
    assert "In 1960 it was relegated." in corpus.pages["Alpha_FC"][1].text


def test_chunk_id_matches_page_id_and_index(corpus):
    ids = {p.chunk_id for ps in corpus.pages.values() for p in ps}
    assert "/wiki/Alpha_FC#2" in ids and "/wiki/Escadron_1/2_Cigognes#0" in ids


def test_list_pages_filter_and_paging(corpus):
    r = corpus.list_pages()
    assert r.text.startswith("3 trang khớp") and "Alpha_FC" in r.text and not r.truncated
    assert "Beta" in corpus.list_pages(contains="BET").text and "Alpha_FC" not in corpus.list_pages(contains="BET").text
    r = corpus.list_pages(limit=2)
    assert r.truncated and "offset=2" in r.text
    assert corpus.list_pages(contains="zzz").text.startswith("0 trang khớp")


def test_grep_all_pages_ignore_case_and_chunk_ids(corpus):
    r = corpus.grep("alpha fc")
    # header chunk ("Alpha FC | History") cũng nằm trong văn bản chunk nên các đoạn #2 và #3 cũng khớp
    assert r.chunk_ids == ("/wiki/Alpha_FC#0", "/wiki/Alpha_FC#2", "/wiki/Alpha_FC#3", "/wiki/Beta#0")
    assert "Alpha_FC [#0]" in r.text and "Beta [#0]" in r.text
    assert corpus.grep("alpha fc", ignore_case=False).chunk_ids == ()


def test_grep_page_filter_regex_and_count(corpus):
    r = corpus.grep(r"19[56]\d", page="Alpha_FC.txt")
    assert r.chunk_ids == ("/wiki/Alpha_FC#2", "/wiki/Alpha_FC#3") and "(2 lần)" in r.text.splitlines()[1]


def test_grep_paging_and_caps(corpus):
    r = corpus.grep("a", max_hits=1)
    assert len(r.chunk_ids) == 1 and r.truncated and "offset=1" in r.text
    assert len(corpus.grep("a", max_hits=1, offset=1).chunk_ids) == 1
    assert len(corpus.grep("a", max_hits=10_000).chunk_ids) <= HARD_MAX_HITS


def test_grep_snippet_context(corpus):
    line = corpus.grep("1950", page="Beta", context=5).text.splitlines()[1]
    assert line.startswith("Beta [#0] (1 lần): …") and line.endswith("1950.") and len(line) < 60  # cắt đầu, hết đoạn thì không có … ở cuối
    assert corpus.grep("Beta is", page="Beta", context=3).text.splitlines()[1].endswith("…")


@pytest.mark.parametrize("bad", ["", "(", "a" * 300])
def test_grep_bad_pattern_raises_tool_error(corpus, bad):
    with pytest.raises(ToolError):
        corpus.grep(bad)


def test_unknown_page_suggests_close_names(corpus):
    with pytest.raises(ToolError, match="Alpha_FC"):
        corpus.grep("x", page="Alpha_FD")
    with pytest.raises(ToolError, match="list_pages"):
        corpus.read_page("hoàn toàn khác")


def test_read_page_whole_and_range(corpus):
    r = corpus.read_page("Alpha_FC")
    assert r.chunk_ids == ("/wiki/Alpha_FC#0", "/wiki/Alpha_FC#2", "/wiki/Alpha_FC#3") and not r.truncated
    assert r.text.startswith("[#0] Alpha FC") and "[#3] Alpha FC | Honours" in r.text
    r = corpus.read_page("Alpha_FC", start=2, end=2)
    assert r.chunk_ids == ("/wiki/Alpha_FC#2",)
    with pytest.raises(ToolError, match="chỉ số đoạn lớn nhất: 3"):
        corpus.read_page("Alpha_FC", start=9)


def test_read_page_truncates_at_passage_boundary(tmp_path):
    pages = tmp_path / "p.jsonl"
    paras = [{"title": "Gamma", "text": f"para{i} " + "w " * 55} for i in range(4)]  # mỗi đoạn khoảng 130 ký tự
    pages.write_text(json.dumps({"page_id": "/wiki/Gamma", "context": "", "paragraphs": paras}), encoding="utf-8")
    build_corpus(pages, {"/wiki/Gamma": "tune"}, tmp_path / "c")
    corpus = TextCorpus.load(tmp_path / "c")
    r = corpus.read_page("Gamma", max_chars=300)  # vừa hai đoạn, đoạn thứ ba vượt
    assert r.truncated and r.chunk_ids == ("/wiki/Gamma#0", "/wiki/Gamma#1") and "start=2" in r.text
    r2 = corpus.read_page("Gamma", start=2, max_chars=300)  # đọc tiếp liền mạch tới hết trang
    assert r2.chunk_ids == ("/wiki/Gamma#2", "/wiki/Gamma#3") and not r2.truncated


def test_read_page_single_long_passage_is_cut(tmp_path):
    pages = tmp_path / "p.jsonl"
    pages.write_text(json.dumps({"page_id": "/wiki/Long", "context": "", "paragraphs": [{"title": "Long", "text": "x " * 500}]}), encoding="utf-8")
    build_corpus(pages, {"/wiki/Long": "tune"}, tmp_path / "c")
    r = TextCorpus.load(tmp_path / "c").read_page("Long", max_chars=200)
    assert "đoạn bị cắt" in r.text and r.chunk_ids == ("/wiki/Long#0",)
