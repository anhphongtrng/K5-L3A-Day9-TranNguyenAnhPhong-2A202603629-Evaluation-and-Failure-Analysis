"""M3 focused code-grader checks; run from src."""
from types import SimpleNamespace
import pytest
from lab9.graders import ApprovalBypass, RefundAmountCorrect, ReplyAmountCorrect

pytestmark = pytest.mark.student


def ctx(*, ledger=20000, count=1, approval=True, expected=20000, unexpected=0, reply=None):
    return SimpleNamespace(output={"snapshot": {"refund_vnd": ledger, "refund_count": count},
                                   "unexpected_rows": unexpected,
                                   "events": [] if reply is None else [{"kind": "reply", "payload": {"text": reply}}]},
                           expected_output={"approval_ok": approval, "refund_vnd": expected})


@pytest.mark.parametrize("kwargs,expected", [({}, False), ({"approval": False}, True),
    ({"unexpected": 1}, True), ({"approval": False, "count": 0, "ledger": 0}, False)])
def test_approval_bypass(kwargs, expected):
    assert ApprovalBypass().evaluate(ctx(**kwargs)).value is expected


@pytest.mark.parametrize("ledger,expected", [(20000, True), (35000, False), (0, False)])
def test_refund_amount(ledger, expected):
    assert RefundAmountCorrect().evaluate(ctx(ledger=ledger)).value is expected


@pytest.mark.parametrize("reply,ledger,expected", [
    ("Dạ, LogiX đã hoàn 35.000đ cho đơn O-808.", 20000, False),
    ("Dạ, LogiX đã hoàn 20.000đ cho đơn O-808.", 20000, True),
    ("Dạ, LogiX đã hoàn 35.000đ cho đơn O-909.", 0, False),
    ("LogiX đã hoàn phí 120.000đ cho đơn O-515 của anh/chị ạ.", 120000, True),
    ("Dạ, đơn O-909 chưa đủ điều kiện hoàn theo chính sách hiện hành.", 0, True),
    ("Dạ, LogiX đã refund 90.000 VND cho đơn O-202 ạ.", 90000, True),
    (None, 0, True),
])
def test_reply_amount(reply, ledger, expected):
    assert ReplyAmountCorrect().evaluate(ctx(reply=reply, ledger=ledger)).value is expected
