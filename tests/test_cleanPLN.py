import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

pytest.importorskip("petta")

import cleanPLN


def test_balance_parentheses_adds_missing_closer():
    fixed, score = cleanPLN.balance_parentheses("(abc")

    assert fixed == "(abc)"
    assert score == pytest.approx(0.6)


def test_balance_parentheses_removes_trailing_excess():
    fixed, score = cleanPLN.balance_parentheses("abc()))")

    assert fixed == "abc()"
    assert score == pytest.approx(0.6)


def test_balance_parentheses_leaves_misaligned_closers():
    expr = "a)b)c"
    fixed, score = cleanPLN.balance_parentheses(expr)

    assert fixed == expr
    assert score == 0.0


def test_balance_parentheses_handles_leading_colon():
    fixed, score = cleanPLN.balance_parentheses(":foo)")

    assert fixed == "(:foo)"
    assert score == pytest.approx(0.6)


def test_run_petta_check_returns_float():
    result = cleanPLN._run_petta_check(":expr", "(: pattern)", 0.1, 0.2)
    assert isinstance(result, float)


def test_checkstmt_matches_stmt_shape():
    result = cleanPLN.checkStmt("(: prf foo (STV 1.0 1.0))")
    assert result == pytest.approx(1.0)


def test_checkstmt_rejects_non_stmt_shape():
    result = cleanPLN.checkStmt("(: $prf (Implication a b) (STV 1.0 1.0))")
    assert result == pytest.approx(0.0)


def test_checkimpl_matches_implication_shape():
    result = cleanPLN.checkImpl("(: prf (Implication a b) (STV 1.0 1.0))")
    assert result == pytest.approx(1.0)


def test_checkimpl_rejects_non_implication_shape():
    result = cleanPLN.checkImpl("(: prf foo (STV 1.0 1.0))")
    assert result == pytest.approx(0.0)


def test_checkquery_accepts_variable_proof_tag():
    result = cleanPLN.checkQuery("(: $prf foo (STV 1.0 1.0))")
    assert result == pytest.approx(1.0)


def test_checkquery_rejects_non_variable_proof_tag():
    result = cleanPLN.checkQuery("(: prf foo (STV 1.0 1.0))")
    assert result == pytest.approx(0.0)
