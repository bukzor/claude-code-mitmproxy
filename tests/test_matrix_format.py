"""The match matrix survives a trip through its own text form.

`diff_matrices.py` compares a matrix collected now against one captured
before the change, which exists only as the text `check_dark_patches.py`
printed. That comparison is only as good as `parse` being `render`'s
inverse, and nothing else would notice if it stopped being one: a mangled
label or a swallowed column reads as an ordinary diff line.
"""

from __future__ import annotations

from claude_mitmproxy import check_dark_patches
from claude_mitmproxy import diff_matrices

MATRIX = check_dark_patches.PatchMatrix(
    stems=("v2.1.226", "v2.1.227-fable"),
    rows=(
        check_dark_patches.PatchRow(
            "strip-git-status", False, {"v2.1.226": "HIT", "v2.1.227-fable": "HIT"}
        ),
        # Longest label, so `table` pads it to nothing -- the case where a
        # naive split on whitespace would run label and first cell together.
        check_dark_patches.PatchRow(
            "strip-tool-preference", True, {"v2.1.226": "-", "v2.1.227-fable": "SUBSUMED"}
        ),
    ),
)


def test_round_trip():
    assert check_dark_patches.parse(check_dark_patches.render(MATRIX)) == MATRIX


def test_logging_lines_are_not_table_rows():
    """A matrix is captured with `> before.txt 2>&1`, so a patch-miss warning
    lands in the middle of it."""
    text = check_dark_patches.render(MATRIX)
    lines = text.splitlines()
    contaminated = "\n".join(
        lines[:2] + ["WARNING:root:patch strip-git-status: no match"] + lines[2:]
    )
    assert check_dark_patches.parse(contaminated) == MATRIX


def test_diff_of_a_matrix_with_itself_is_empty():
    result = diff_matrices.diff(MATRIX, MATRIX)
    assert result.cells == ()
    assert result.sunset == ()
    assert result.unshared_patches == ()
    assert result.unshared_stems == ()


def test_diff_reports_the_cell_that_moved():
    moved = MATRIX._replace(
        rows=(
            MATRIX.rows[0]._replace(cells={"v2.1.226": "-", "v2.1.227-fable": "HIT"}),
            MATRIX.rows[1],
        )
    )
    result = diff_matrices.diff(MATRIX, moved)
    assert result.cells == (
        diff_matrices.CellChange("strip-git-status", "v2.1.226", "HIT", "-"),
    )
    assert result.shared_patches == 2
    assert result.shared_stems == 2


def test_diff_leaves_unshared_rows_and_columns_alone():
    """A promoted fixture adds a column and a retired patch drops a row; both
    are reported as unshared rather than diffed."""
    other = check_dark_patches.PatchMatrix(
        stems=("v2.1.226", "v2.1.228"),
        rows=(MATRIX.rows[0], ),
    )
    result = diff_matrices.diff(MATRIX, other)
    assert result.cells == ()
    assert result.shared_patches == 1
    assert result.shared_stems == 1
    assert result.unshared_patches == ("strip-tool-preference",)
    assert result.unshared_stems == ("v2.1.227-fable", "v2.1.228")
