from src.medic_matcher import Medic, MedicMatcher


def test_distance_priority():
    """
    A closer medic should be selected even if farther medic has a better specialty.
    """
    matcher = MedicMatcher()
    matcher.db.medics = []

    patient_loc = (0.0, 0.0)

    medic_near = Medic(
        id="MED-A",
        name="Medic Near",
        specialty="general",
        certification_level="paramedic",
        gps_location=(0.045, 0.0),
        status="available",
        current_load=0,
        missions_completed=10,
        rating=5.0,
        languages=["en"],
    )

    medic_far = Medic(
        id="MED-B",
        name="Medic Far",
        specialty="cardiac",
        certification_level="critical_care",
        gps_location=(0.135, 0.0),
        status="available",
        current_load=0,
        missions_completed=100,
        rating=5.0,
        languages=["en"],
    )

    matcher.db.medics = [medic_near, medic_far]

    decision = {"response_mode": "aerial_only"}
    triage = {"severity_level": 3, "category": "cardiac"}

    result = matcher.find_best_match(decision, triage, patient_location=patient_loc)
    assert result["assigned_medic"]["id"] == "MED-A"
