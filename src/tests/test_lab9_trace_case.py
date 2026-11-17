"""M1 regression: C-002 must use DB facts rather than ticket assertions."""
import unittest

from lab9.trace_case import investigate


def assert_c002_contract(case):
    trial, label = case['trial'], case['label']
    assert label['refund_vnd'] == 0
    assert label['refund_count'] == 0
    assert label['status'] == 'denied'
    for key in ('refund_vnd', 'refund_count'):
        assert trial['snapshot'][key] == label[key], key
    assert trial['result']['status'] == label['status']
    assert not any(e.get('kind') == 'model_override' for e in trial['events'])
    assert trial['unexpected_rows'] == 0
    assert trial['lab8_pass'], trial['lab8_reason']


class TestTraceCase(unittest.TestCase):
    def test_c002_ticket_trust(self):
        assert_c002_contract(investigate('fixed', 'C-002', 11))

    def test_c002_seeded_regression_detected(self):
        case = investigate('seeded_regression', 'C-002', 11)
        trial = case['trial']
        self.assertFalse(trial['lab8_pass'])
        self.assertTrue(any(e.get('kind') == 'model_override' for e in trial['events']))
        self.assertNotEqual(trial['snapshot']['refund_vnd'], case['label']['refund_vnd'])
        with self.assertRaises(AssertionError):
            assert_c002_contract(case)
