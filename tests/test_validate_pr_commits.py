"""Tests for the commit-message half of the PR contract."""

from scripts.validate_pr_commits import (
    editable_message,
    subject_problems,
    validate_commit_messages,
)


class TestSubjectProblems:
    def test_release_please_subject_passes(self) -> None:
        assert subject_problems("chore(main): release 1.2.3") == []

    def test_plain_type_passes(self) -> None:
        assert subject_problems("feat: add walk tool") == []

    def test_double_scope_passes(self) -> None:
        assert subject_problems("chore(deps)(github-actions): bump actions") == []

    def test_non_conventional_fails(self) -> None:
        problems = subject_problems("update stuff")

        assert len(problems) == 1
        assert "not a Conventional Commit subject" in problems[0]

    def test_unsupported_type_names_the_type(self) -> None:
        problems = subject_problems("wip: try something")

        assert problems == [
            (
                "'wip: try something' uses unsupported type 'wip'. Allowed types: "
                "build, chore, ci, docs, feat, fix, perf, refactor, revert, style, test."
            )
        ]


class TestBodyRules:
    def test_column_zero_bullet_rejected(self) -> None:
        from scripts.validate_pr_commits import message_problems

        message = "fix: subject\n\n- bullet at column 0\n"
        problems = message_problems(message)

        assert any("Markdown bullet at column 0" in problem for problem in problems)

    def test_blank_line_after_breaking_change_rejected(self) -> None:
        from scripts.validate_pr_commits import message_problems

        message = "feat!: subject\n\nBREAKING CHANGE:\n\n- dropped thing\n"
        problems = message_problems(message)

        assert any("blank line directly after 'BREAKING CHANGE:'" in problem for problem in problems)

    def test_clean_message_passes(self) -> None:
        from scripts.validate_pr_commits import message_problems

        assert message_problems("fix: subject\n\n  - indented bullet\n\nBREAKING CHANGE: note\n") == []


class TestValidateCommitMessages:
    def test_release_commit_message_full_body(self) -> None:
        message = "chore(main): release 1.2.3\n\n---\n\n### Bug Fixes\n\n  - fix a thing\n"

        ok, reported = validate_commit_messages([message])

        assert ok
        assert reported == ["All 1 commit message(s) are releasable."]

    def test_mixed_messages_report_each_problem(self) -> None:
        ok, reported = validate_commit_messages(["feat: ok", "bad subject"])

        assert not ok
        assert len(reported) == 1

    def test_empty_range_is_ok(self) -> None:
        ok, reported = validate_commit_messages([])

        assert ok
        assert reported == ["No non-merge commits to validate."]


class TestEditableMessage:
    def test_strips_comments_and_scissors(self) -> None:
        raw = (
            "feat: subject\n"
            "\n"
            "# Please enter the commit message\n"
            "# ------------------------ >8 ------------------------\n"
            "# rest ignored\n"
        )

        assert editable_message(raw) == "feat: subject"

    def test_keeps_body(self) -> None:
        assert editable_message("fix: x\n\n  - bullet indented\n") == "fix: x\n\n  - bullet indented"
