"""
Regression tests: the archived data must keep reproducing the manuscript.

    pytest                 # everything (~2 min; reruns the Stage 2 bootstrap)
    pytest -m "not slow"   # skip Tables 6-8 (~20 s)

The known discrepancies documented in docs/reproducibility_report.md are
pinned as MISMATCH, so a change that silently "fixes" or alters them fails too.
"""

import hashlib

import pytest

from reproduce import results as r
from reproduce import verify

# Check ids that do not equal the manuscript today (see the report, D1-D3).
KNOWN_MISMATCHES = {
    "Ablation workbook E rows",     # workbook E = 90/120; paper's E comes from Stage 2
    "Qwen unparsed outputs",        # 1 of 400 Qwen outputs has no parseable decision
    "Explanation length ratio",     # ~6x measured vs. "approximately five-fold"
}


def _assert_checks(df):
    for c in df.itertuples():
        if c.id in KNOWN_MISMATCHES:
            assert c.status == "MISMATCH", f"{c.id} changed: now {c.status} ({c.observed})"
        else:
            assert c.status in {"MATCH", "RECORD_ONLY", "NOT_VERIFIABLE"}, \
                f"{c.id}: expected {c.expected}, observed {c.observed}"


def test_archived_data_unchanged():
    manifest = r.ROOT / "reproduce" / "data_checksums.sha256"
    for line in manifest.read_text().splitlines():
        digest, path = line.split(maxsplit=1)
        actual = hashlib.sha256((r.ROOT / path).read_bytes()).hexdigest()
        assert actual == digest, f"{path} differs from the archived version"


def test_stage1_record():
    _assert_checks(verify.all_checks().query("ref.str.startswith('Table 4') or ref.str.startswith('Table 5')"))
    t4, _ = r.stage1_record()
    assert len(t4) == 12  # 4 prompt configurations x 3 models, not 18


def test_stage2_descriptive():
    _assert_checks(pd_concat(verify.stage2_descriptive_checks()))


def test_ablation_and_cross_model():
    _assert_checks(pd_concat(verify.ablation_checks()))


def test_speed_offset():
    _assert_checks(pd_concat(verify.speed_offset_checks()))


def test_decision_parsing_matches_stored_codes():
    for s in ("ToT", "CoT"):
        assert r.stage2_integrity(s)["reparse_mismatches"] == 0
    for m in ("gpt", "qwen"):
        assert r.ablation_integrity(m)["reparse_mismatches"] == 0


@pytest.mark.slow
def test_stage2_statistics(tmp_path):
    _assert_checks(pd_concat(verify.stage2_statistics_checks(verify.run_stage2_analysis(tmp_path))))


def pd_concat(checks):
    import pandas as pd
    return pd.DataFrame(checks)
