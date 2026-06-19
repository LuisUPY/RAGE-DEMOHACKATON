from rage_bench.dataset import load_attacks
from rage_bench.models import get_model
from rage_bench.report import build_report
from rage_bench.runner import run_benchmark


def test_vulnerable_model_has_high_asr():
    cases = load_attacks()
    results = run_benchmark(get_model("mock", "vulnerable"), cases)
    report = build_report("mock:vulnerable", results)
    assert report.total_cases == len(cases)
    assert report.asr >= 90.0


def test_hardened_model_has_zero_asr():
    cases = load_attacks()
    results = run_benchmark(get_model("mock", "hardened"), cases)
    report = build_report("mock:hardened", results)
    assert report.total_successes == 0
    assert report.severity_score == 0.0


def test_guarded_model_is_partially_vulnerable():
    cases = load_attacks()
    results = run_benchmark(get_model("mock", "guarded"), cases)
    report = build_report("mock:guarded", results)
    # A guarded model should be neither fully safe nor fully broken.
    assert 0 < report.total_successes < report.total_cases


def test_report_per_category_totals_match():
    cases = load_attacks()
    results = run_benchmark(get_model("mock", "guarded"), cases)
    report = build_report("mock:guarded", results)
    assert sum(s.total for s in report.per_category) == report.total_cases
    assert sum(s.successes for s in report.per_category) == report.total_successes
