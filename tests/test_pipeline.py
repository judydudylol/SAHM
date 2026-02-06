"""
Pipeline integration tests for current SAHM modules.
"""

from src.dispatch_engine import dispatch
from src.medic_matcher import assign_medic
from src.triage_engine import triage


def _to_matcher_mode(response_mode: str) -> str:
    mode_map = {
        "DOCTOR_DRONE": "aerial_only",
        "AMBULANCE": "ground_only",
        "BOTH": "combined",
    }
    return mode_map.get(response_mode, "ground_only")


def test_pipeline_critical_case_assigns_medic():
    triage_result = triage(
        symptoms=["chest_pain_crushing", "shortness_of_breath"],
        free_text="Severe crushing chest pain and breathing distress",
        duration_minutes=8,
        voice_stress_score=0.9,
    )
    assert triage_result["severity_level"] == 3

    dispatch_result = dispatch(
        weather_risk_pct=10.0,
        harm_threshold_min=4.0,
        ground_eta_min=22.0,
        air_eta_min=3.6,
    )
    assert dispatch_result.response_mode in {"DOCTOR_DRONE", "BOTH"}

    assignment = assign_medic(
        decision_output={"response_mode": _to_matcher_mode(dispatch_result.response_mode)},
        triage_output={
            "severity_level": triage_result["severity_level"],
            "category": triage_result["category"],
        },
        scenario_seed=11,
    )
    assert assignment["status"] == "success"
    assert assignment["assigned_medic"] is not None
    assert assignment["match_time_seconds"] < 3.0


def test_pipeline_ambulance_only_skips_aerial_assignment():
    triage_result = triage(
        symptoms=["headache", "mild_pain"],
        free_text="Mild headache, speaking clearly",
        duration_minutes=90,
        voice_stress_score=0.2,
    )
    assert triage_result["severity_level"] <= 1

    dispatch_result = dispatch(
        weather_risk_pct=80.0,
        harm_threshold_min=20.0,
        ground_eta_min=18.0,
        air_eta_min=3.6,
    )
    assert dispatch_result.response_mode == "AMBULANCE"

    assignment = assign_medic(
        decision_output={"response_mode": _to_matcher_mode(dispatch_result.response_mode)},
        triage_output={
            "severity_level": triage_result["severity_level"],
            "category": triage_result["category"],
        },
        scenario_seed=5,
    )
    assert assignment["assigned_medic"] is None
    assert "Ground ambulance only" in assignment["reasoning"]
