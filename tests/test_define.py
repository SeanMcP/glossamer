import sys

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def get(word):
    return client.get(f"/define/{word}")


def test_exact_match_with_multiple_senses_noun_first():
    body = get("dog").json()
    assert body["words"] == ["dog"]
    assert len(body["senses"]) > 1
    assert body["senses"][0]["pos"] == "noun"
    assert "Canis familiaris" in body["senses"][0]["synonyms"]


def test_suffix_rules_resolve_running_to_run():
    body = get("running").json()
    # "running" is its own lemma too, so both forms are returned, exact first.
    assert body["words"] == ["running", "run"]
    run_senses = [s for s in body["senses"] if s["word"] == "run"]
    assert run_senses and all(s["pos"] == "verb" for s in run_senses)


def test_exceptions_resolve_geese_to_goose():
    body = get("geese").json()
    assert body["words"] == ["goose"]
    assert body["senses"][0]["pos"] == "noun"


def test_multiword_lookup():
    body = get("ice cream").json()
    assert body["words"] == ["ice_cream"]


def test_input_is_normalized():
    response = get("DOG ")
    assert response.status_code == 200
    assert response.json()["words"] == ["dog"]


def test_unknown_word_is_404():
    response = get("asdfqwer")
    assert response.status_code == 404
    assert "asdfqwer" in response.json()["detail"]


def test_blank_input_is_422():
    assert get(" ").status_code == 422


def test_overlong_input_is_422():
    assert get("a" * 101).status_code == 422


def test_runtime_does_not_import_nltk():
    assert "nltk" not in sys.modules
