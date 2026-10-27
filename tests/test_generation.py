from tam.generation.answerer import AnswerBatch, AnswerItem, is_refusal, valid_batch
from tam.generation.scoring import contains, exact_match, f1_score, normalize


def test_normalize_and_em():
    assert normalize("The  Köln!") == "koln"
    assert exact_match("Markus Anfang", ["markus anfang"]) == 1.0
    assert exact_match(None, ["x"]) == 0.0


def test_f1_and_contains():
    assert round(f1_score("Markus Anfang was the coach", ["Markus Anfang"]), 3) == 0.667
    assert contains("It was Markus Anfang", ["Markus Anfang"]) == 1.0
    assert contains("Markus", ["Markus Anfang"]) == 0.0


def test_refusal_and_batch_validity():
    assert is_refusal(None) and is_refusal("Null.") and not is_refusal("Oslo")
    ok = AnswerBatch(answers=[AnswerItem(n=2, answer="a", evidence=[1]), AnswerItem(n=1, answer=None)])
    assert valid_batch(ok, 2)
    assert not valid_batch(AnswerBatch(answers=[AnswerItem(n=1), AnswerItem(n=1)]), 2)
    assert not valid_batch(AnswerBatch(answers=[AnswerItem(n=1)]), 2)
