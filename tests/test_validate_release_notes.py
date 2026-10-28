import pytest
from scripts.validate_pr_commits import validate_commit_messages
from scripts.validate_release_notes import _split_messages, validate_release_notes

OVERRIDE = """
BEGIN_COMMIT_OVERRIDE
fix(audit): serialize ledger read-modify-write cycles

feat(cli): confirm irreversible project delete
END_COMMIT_OVERRIDE
"""


def test_single_commit_pr_owes_no_override() -> None:
    ok, _ = validate_release_notes("Just a description.", commit_count=1, require_above=1)

    assert ok


def test_multi_commit_pr_without_an_override_is_rejected() -> None:
    ok, messages = validate_release_notes("Just a description.", commit_count=29, require_above=1)

    assert not ok
    assert any("squashes 29 commits" in message for message in messages)


def test_override_block_splits_into_one_entry_per_message() -> None:
    ok, messages = validate_release_notes(OVERRIDE, commit_count=29, require_above=1)

    assert ok
    assert "2 changelog entr" in messages[0]


def test_github_default_squash_body_shape_is_rejected() -> None:
    body = """
BEGIN_COMMIT_OVERRIDE
* fix(audit): serialize ledger read-modify-write cycles
* feat(cli): confirm irreversible project delete
END_COMMIT_OVERRIDE
"""

    block = body.split("BEGIN_COMMIT_OVERRIDE")[1].split("END_COMMIT_OVERRIDE")[0]
    assert len(_split_messages(block)) == 1

    ok, messages = validate_release_notes(body, commit_count=2, require_above=1)

    assert not ok
    assert any("not a Conventional Commit subject" in message for message in messages)


def test_blank_line_after_breaking_change_is_rejected() -> None:
    body = """
BEGIN_COMMIT_OVERRIDE
refactor(cli)!: drop duplicate snapshot commands

BREAKING CHANGE: the operator surface changed.

- `portfolio status` is gone; use `status`.
END_COMMIT_OVERRIDE
"""

    ok, messages = validate_release_notes(body, commit_count=2, require_above=1)

    assert not ok
    assert any("blank line directly after" in message for message in messages)


def test_breaking_change_bullets_on_the_next_line_are_accepted() -> None:
    body = """
BEGIN_COMMIT_OVERRIDE
refactor(cli)!: drop duplicate snapshot commands
BREAKING CHANGE: the operator surface changed.
- `portfolio status` is gone; use `status`.
END_COMMIT_OVERRIDE
"""

    ok, _ = validate_release_notes(body, commit_count=2, require_above=1)

    assert ok


def test_unsupported_type_in_an_override_entry_is_rejected() -> None:
    body = "BEGIN_COMMIT_OVERRIDE\nwip(cli): halfway there\nEND_COMMIT_OVERRIDE"

    ok, messages = validate_release_notes(body, commit_count=2, require_above=1)

    assert not ok
    assert any("unsupported type 'wip'" in message for message in messages)


@pytest.mark.parametrize("second_type", ["fix", "wip"])
def test_breaking_note_and_following_override_entry_are_validated_separately(second_type: str) -> None:
    body = (
        "BEGIN_COMMIT_OVERRIDE\nfeat!: replace the API\n\n"
        "BREAKING CHANGE: migrate calls.\n- Use the new API.\n\n"
        f"{second_type}: maintain the CLI\n\n  - Preserve validation.\nEND_COMMIT_OVERRIDE"
    )

    ok, messages = validate_release_notes(body, commit_count=2, require_above=1)

    assert ok == (second_type == "fix")
    if ok:
        assert "2 changelog entr" in messages[0]
    else:
        assert "unsupported type 'wip'" in messages[0]


def test_commit_subjects_must_be_conventional() -> None:
    ok, messages = validate_commit_messages(["fix(ci): pin the digest", "quick wip fix"])

    assert not ok
    assert any("'quick wip fix' is not a Conventional Commit subject." in message for message in messages)


def test_conventional_commit_subjects_pass() -> None:
    ok, _ = validate_commit_messages(["fix(ci): pin the digest", "docs: explain the gate"])

    assert ok


@pytest.mark.parametrize("indent", ["", "  "])
def test_ordinary_body_bullets_follow_the_same_rule(indent: str) -> None:
    message = f"ci: add validators\n\n{indent}- one thing\n{indent}- another thing"
    body = f"BEGIN_COMMIT_OVERRIDE\n{message}\nEND_COMMIT_OVERRIDE"

    commit_ok, commit_messages = validate_commit_messages([message])
    override_ok, override_messages = validate_release_notes(body, commit_count=2, require_above=1)

    assert commit_ok == override_ok == bool(indent)
    if not indent:
        assert commit_messages == override_messages
        assert "Markdown bullet at column 0" in commit_messages[0]


@pytest.mark.parametrize("gap", ["", "\n"])
def test_breaking_note_bullets_follow_the_same_rule(gap: str) -> None:
    message = f"feat!: replace the API\n\nBREAKING CHANGE: migrate calls.\n{gap}- Use the new API."
    body = f"BEGIN_COMMIT_OVERRIDE\n{message}\nEND_COMMIT_OVERRIDE"

    commit_ok, commit_messages = validate_commit_messages([message])
    override_ok, override_messages = validate_release_notes(body, commit_count=2, require_above=1)

    assert commit_ok == override_ok == (not gap)
    if gap:
        assert commit_messages == override_messages
        assert any("blank line directly after" in problem for problem in commit_messages)


def test_breaking_note_does_not_exempt_later_ordinary_bullets() -> None:
    message = "feat!: replace the API\n\nBREAKING CHANGE: migrate calls.\n- New API.\n\n- Ordinary body."
    body = f"BEGIN_COMMIT_OVERRIDE\n{message}\nEND_COMMIT_OVERRIDE"

    commit_ok, commit_messages = validate_commit_messages([message])
    override_ok, override_messages = validate_release_notes(body, commit_count=2, require_above=1)

    assert not commit_ok
    assert not override_ok
    assert commit_messages == override_messages
    assert "Markdown bullet at column 0" in commit_messages[0]
