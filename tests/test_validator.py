from src.validator import run_full_validation


def test_reference_datasets_validate_against_rules():
    scenarios_report, cases_report = run_full_validation()
    assert scenarios_report.matches == scenarios_report.total
    assert cases_report.matches == cases_report.total
