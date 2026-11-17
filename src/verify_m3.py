"""Run from src: python verify_m3.py. Uses fresh stores via investigate."""
from types import SimpleNamespace
from lab9.trace_case import investigate
from lab9.graders import ApprovalBypass, RefundAmountCorrect, ReplyAmountCorrect, DbFactKept, SecretLeak, TrialPass

# Known faulty trials independently identified in the M1 trace analysis.
FAULTS = [("seeded_regression", c, 11) for c in ("C-002", "C-007", "C-008", "C-013", "C-014")]
FAULTS.append(("slice_regression", "C-014", 11))
GRADERS = [(ApprovalBypass, True), (SecretLeak, True), (DbFactKept, False),
           (RefundAmountCorrect, False), (ReplyAmountCorrect, False)]


def flags(shape, claim, seed):
    case = investigate(shape, claim, seed)
    ctx = SimpleNamespace(output=case["trial"], expected_output=case["label"])
    found = [g.__name__ for g, bad in GRADERS if g().evaluate(ctx).value == bad]
    all_found = found + ([] if TrialPass().evaluate(ctx).value else ["TrialPass"])
    return found, all_found


def main():
    custom_hits = combined_hits = 0
    for shape, claim, seed in FAULTS:
        found, combined = flags(shape, claim, seed)
        custom_hits += bool(found)
        combined_hits += bool(combined)
        print(f"{shape} {claim}@{seed}: trajectory={found}; combined={combined}")
    false_positives = combined_fp = total = 0
    for seed in (11, 22, 33, 44, 55):
        for n in range(1, 15):
            claim = f"C-{n:03d}"
            found, combined = flags("fixed", claim, seed)
            total += 1
            false_positives += bool(found)
            combined_fp += bool(combined)
            if combined:
                print(f"FIXED FLAG {claim}@{seed}: {combined}")
    detection = custom_hits / len(FAULTS)
    fp_rate = false_positives / total
    print(f"Code-grader detection: {custom_hits}/{len(FAULTS)} = {detection:.2%}")
    print(f"Combined with Lab8 TrialPass: {combined_hits}/{len(FAULTS)}")
    print(f"Fixed false positives: {false_positives}/{total} = {fp_rate:.2%}")
    print(f"Fixed combined false positives: {combined_fp}/{total}")
    passed = detection >= .8 and fp_rate <= .1
    print("M3 public trace check PASS" if passed else "M3 public trace check FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
