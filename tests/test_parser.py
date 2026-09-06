from pathlib import Path

from dealbrief.parser import parse_notes, MISSING_PLACEHOLDER

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_all_labeled_fields_from_well_formed_notes():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)

    assert notes.get("company") == "Acme Robotics"
    assert notes.get("sector") == "Industrial automation"
    assert notes.get("stage") == "Seed"
    assert notes.get("ask") == "$2M at $10M post"
    assert "manual sorting" in notes.get("problem")
    assert "vision-guided picking arm" in notes.get("solution")
    assert "$180k ARR" in notes.get("traction")
    assert "Zoox" in notes.get("team")
    assert "Taiwan" in notes.get("risks")
    assert "cohort-level retention" in notes.get("notes")


def test_multiline_field_values_are_joined_up_to_the_next_label():
    raw = (FIXTURES / "sample_notes.txt").read_text()
    notes = parse_notes(raw)
    # "Problem:" spans three lines in the fixture; make sure none were dropped.
    problem = notes.get("problem")
    assert "20% of labor hours" in problem
    assert "design partners raised in discovery" in problem


def test_missing_fields_are_explicit_not_silently_absent():
    raw = (FIXTURES / "sparse_notes.txt").read_text()
    notes = parse_notes(raw)

    assert notes.get("company") == "Widgetco"
    assert notes.get("stage") == "pre-seed"
    # Never captured in this fixture at all.
    assert notes.get("ask") == MISSING_PLACEHOLDER
    assert notes.get("traction") == MISSING_PLACEHOLDER
    assert "ask" in notes.missing_fields()
    assert "traction" in notes.missing_fields()


def test_label_matching_is_case_insensitive_and_alias_tolerant():
    raw = "COMPANY: Foo Inc\nValuation: $5M post\nRaise: on a SAFE\n"
    notes = parse_notes(raw)
    assert notes.get("company") == "Foo Inc"
    # "Valuation" and "Raise" are both aliases of the same canonical "ask"
    # field, so the second labeled line appends onto the same field instead
    # of silently overwriting the first.
    ask = notes.get("ask")
    assert "$5M post" in ask
    assert "on a SAFE" in ask


def test_stray_preamble_before_first_label_is_dropped_not_raised():
    raw = "Just some free-form chatter before anyone used a label.\nCompany: Foo\n"
    notes = parse_notes(raw)
    assert notes.get("company") == "Foo"


def test_empty_notes_produce_all_missing_fields_without_crashing():
    notes = parse_notes("")
    assert notes.missing_fields() == [
        "company",
        "sector",
        "stage",
        "ask",
        "problem",
        "solution",
        "traction",
        "team",
    ]
