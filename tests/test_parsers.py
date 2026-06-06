from datetime import date

from apps.normalizer.parsers import (
    _num,
    _to_date,
    _to_inr,
    extract_skills,
    parse_salary_text,
    salary_from_description,
    strip_html,
)


def test_strip_html_removes_tags_and_collapses_ws() -> None:
    assert strip_html("<p>Hello <b>World</b></p>") == "Hello World"


def test_strip_html_unescapes_entities() -> None:
    assert strip_html("Tom &amp; Jerry") == "Tom & Jerry"


def test_strip_html_empty_inputs_return_none() -> None:
    assert strip_html(None) is None
    assert strip_html("") is None
    assert strip_html("   ") is None


def test_num_parses_and_guards() -> None:
    assert _num("12.5") == 12.5
    assert _num(10) == 10.0
    assert _num(None) is None
    assert _num("") is None
    assert _num("abc") is None


def test_to_date_iso_and_z_suffix() -> None:
    assert _to_date("2026-01-15") == date(2026, 1, 15)
    assert _to_date("2026-01-15T10:30:00Z") == date(2026, 1, 15)


def test_to_date_guards() -> None:
    assert _to_date(None) is None
    assert _to_date("") is None
    assert _to_date("not a date") is None


def test_parse_salary_text_single_units() -> None:
    assert parse_salary_text("5 lakh") == (500000.0, 500000.0)
    assert parse_salary_text("80k") == (80000.0, 80000.0)
    assert parse_salary_text("2 cr") == (20000000.0, 20000000.0)


def test_parse_salary_text_guards() -> None:
    assert parse_salary_text(None) == (None, None)
    assert parse_salary_text("") == (None, None)
    assert parse_salary_text("competitive pay") == (None, None)


def test_to_inr_applies_unit_multiplier() -> None:
    assert _to_inr("12", "lpa") == 1200000.0
    assert _to_inr("2", "cr") == 20000000.0
    assert _to_inr("1,200,000", None) == 1200000.0


def test_extract_skills_guards_and_invariants() -> None:
    assert extract_skills(None) is None
    assert extract_skills("") is None
    result = extract_skills("python python sql")
    if result is not None:
        assert result == sorted(result)
        assert len(result) == len(set(result))


def test_salary_from_description_requires_cue() -> None:
    assert salary_from_description(None) == (None, None)
    assert salary_from_description("") == (None, None)
    assert salary_from_description("Great team and free lunch") == (None, None)
