"""Công cụ graph (`tam.tools.graph_tools`) trên kho giả. Không cần Neo4j, LLM hay embedding."""
import pytest

from tam.tools.base import ToolError
from tam.tools.graph_tools import GraphTools, page_name


def ev(date, track, text, cids, tier=1, phase="point", kind="change"):
    return {"node_id": f"{date}{track}", "date": date, "phase": phase, "track": track, "kind": kind, "subject": "self", "tier": tier, "text": text, "quote": "", "cids": cids}


class FakeGraph:
    def __init__(self, pages):
        self.pages = pages  # tên trang -> danh sách sự kiện đã sắp theo ngày

    def cell_events(self, page, tracks=None, date_from=None, date_to=None, max_tier=2):
        out = []
        for e in self.pages.get(page, []):
            if e["tier"] > max_tier or (tracks is not None and e["track"] not in tracks):
                continue
            if (date_from is not None and e["date"][:4] < date_from) or (date_to is not None and e["date"][:4] > date_to):
                continue
            out.append(e)
        return out

    def events_of_chunks(self, chunk_ids):
        return [{"node_id": e["node_id"], "page": p, "track": e["track"]} for p, evs in self.pages.items() for e in evs if set(e["cids"]) & set(chunk_ids)]


@pytest.fixture()
def tools():
    g = FakeGraph({"Acme": [ev("1990", "role", "Ann became CEO.", ["/wiki/Acme#0"]), ev("1995", "location", "HQ moved to Paris.", ["/wiki/Acme#1"]),
                            ev("2001", "role", "Bob became CEO.", ["/wiki/Acme#2"]), ev("2003", "other", "Minor note.", ["/wiki/Acme#2"], tier=2)]})
    return GraphTools(g)


def test_timeline_lists_events_in_order_with_chunks(tools):
    r = tools.timeline("Acme")
    lines = r.text.split("\n")
    assert lines[0].startswith("4 events on Acme") and "tracks: location, other, role" in lines[0]
    assert [l.split()[1] for l in lines[1:]] == ["1990", "1995", "2001", "2003"]
    assert "1990 [point] role/change (tier 1) Ann became CEO. </wiki/Acme#0>" in r.text
    assert r.chunk_ids == ("/wiki/Acme#0", "/wiki/Acme#1", "/wiki/Acme#2")


def test_page_name_accepts_wiki_prefix_and_chunk_page(tools):
    assert page_name("/wiki/Acme") == "Acme" and page_name("Acme") == "Acme"
    assert tools.timeline("/wiki/Acme").text.startswith("4 events")


def test_filters_by_track_and_years(tools):
    r = tools.timeline("Acme", track=["role"], from_year=1995, to_year=2002)
    assert r.text.startswith("1 events on Acme") and "Bob became CEO" in r.text and "Ann" not in r.text


def test_paging_and_cap(tools):
    p1 = tools.timeline("Acme", max_events=2)
    assert p1.truncated and "offset=2" in p1.text and "1990" in p1.text and "2001" not in p1.text
    p2 = tools.timeline("Acme", max_events=2, offset=2)
    assert not p2.truncated and "2001" in p2.text and "1990" not in p2.text
    assert len(GraphTools(tools._store, events_cap=1).timeline("Acme", max_events=10).text.split("\n")) == 2  # tiêu đề + 1 sự kiện
    with pytest.raises(ToolError):
        tools.timeline("Acme", offset=10)


def test_errors_are_tool_errors(tools):
    for kw in ({"page": "Nope"}, {"page": "Acme", "from_year": 2000, "to_year": 1990}, {"page": "Acme", "track": ["nosuchtrack"]}):
        with pytest.raises(ToolError):
            tools.timeline(**kw)


def test_events_of_chunk(tools):
    r = tools.events_of_chunk(["/wiki/Acme#2", "/wiki/Acme#9"])
    assert "/wiki/Acme#2: 2 events; page Acme; tracks other, role" in r.text and "/wiki/Acme#9: no events in the graph" in r.text


def test_tool_definitions_and_validation(tools):
    t = {x.name: x for x in tools.tools()}
    assert set(t) == {"timeline", "events_of_chunk"}
    assert "page" in t["timeline"].schema()["function"]["parameters"]["properties"]
    with pytest.raises(ToolError):
        t["timeline"].call({"page": "Acme", "max_events": 0})
    assert t["timeline"].call({"page": "Acme", "to_year": 1990}).text.startswith("1 events")


def test_page_name_normalize_matches_graph_naming():
    assert page_name("/wiki/Karlsøy", normalize=True) == "Karls_y"
    assert page_name("David Young (Iowa politician)", normalize=True) == "David_Young_Iowa_politician"
    assert page_name("Department_of_Computing,_Imperial_College_London", normalize=True) == "Department_of_Computing_Imperial_College_London"
    assert page_name("Stefan_Heße", normalize=True) == "Stefan_He_e"
    assert page_name("Karls_y", normalize=False) == "Karls_y"


def test_timeline_normalizes_names_only_when_asked():
    g = FakeGraph({"Acme_Corp": [ev("1990", "role", "Ann became CEO.", ["/wiki/Acme_Corp#0"])]})
    with pytest.raises(ToolError):
        GraphTools(g).timeline("Acme (Corp)")
    assert "Ann became CEO." in GraphTools(g, normalize_names=True).timeline("Acme (Corp)").text


def test_compact_timeline_drops_metadata_and_shortens_chunk_ids():
    g = FakeGraph({"Acme": [ev("1990", "role", "Ann became CEO.", ["/wiki/Acme#0", "/wiki/Acme#1"])]})
    full = GraphTools(g).timeline("Acme").text
    compact = GraphTools(g, compact=True).timeline("Acme")
    assert compact.text.split("\n")[1] == "1. 1990 Ann became CEO. <#0, #1>"
    assert "/wiki/Acme#n" in compact.text.split("\n")[0]
    assert len(compact.text) < len(full)
    assert compact.chunk_ids == ("/wiki/Acme#0", "/wiki/Acme#1")  # id đầy đủ vẫn có trong kết quả có cấu trúc


def test_timeline_accepts_chunk_id_when_normalizing():
    g = FakeGraph({"Sergey_Sirotkin_racing_driver": [ev("2018", "role", "Joined Williams.", ["/wiki/Sergey_Sirotkin_(racing_driver)#13"])]})
    t = GraphTools(g, normalize_names=True)
    assert "Joined Williams." in t.timeline("/wiki/Sergey_Sirotkin_(racing_driver)#13").text
    assert page_name("/wiki/Karlsøy#2", normalize=True) == "Karls_y"
    with pytest.raises(ToolError):
        GraphTools(g).timeline("/wiki/Sergey_Sirotkin_(racing_driver)#13")


def test_track_hint_counts_and_description(tools):
    t = GraphTools(tools._store, track_hint=True)
    assert "tracks: location (1), other (1), role (2)" in t.timeline("Acme").text
    assert "tracks: location, other, role" in tools.timeline("Acme").text  # mặc định không đổi
    assert "narrowed to the relevant track" in t.tools()[0].description
    assert "narrowed" not in tools.tools()[0].description


def test_source_hint_description(tools):
    d = GraphTools(tools._store, source_hint=True).tools()[0].description
    assert "read_chunk shows that chunk's full text" in d
    assert "read_chunk" not in tools.tools()[0].description
