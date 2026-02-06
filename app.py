


MEDIC_TOOLS = {
  'Cardiac Arrest': ['AED', 'Cardiac Medications', 'Portable ECG', 'Advanced Airway Kit'],
  'Severe Trauma': ['Tourniquet', 'Hemostatic Gauze', 'IV Fluids', 'Splint Kit', 'Pressure Dressings'],
  'Burn': ['Burn Gel', 'Sterile Dressings', 'IV Fluids', 'Pain Relief'],
  'Respiratory Distress': ['Portable Oxygen', 'Nebulizer', 'Bronchodilators', 'Intubation Kit'],
  'Anaphylaxis': ['EpiPen', 'Antihistamines', 'Oxygen', 'IV Steroids'],
  'Stroke': ['Stroke Assessment Kit', 'Neuroprotective Meds', 'Oxygen', 'Glucose Monitor'],
  'General': ['ALS Kit', 'Vital Signs Monitor', 'First Aid Trauma Bag', 'IV Access Kit'],
}


import hashlib
import html
import textwrap
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from src.data_loader import (
    load_scenarios,
    load_cases,
    load_categorizer,
)
from src.dispatch_engine import dispatch, DispatchResult
from src.validator import validate_scenarios, validate_cases
from src.triage_engine import triage, SYMPTOM_POINTS, RED_FLAGS
from src.medic_matcher import assign_medic
from src.gemini_engine import (
    analyze_audio_call,
    is_gemini_available,
    get_availability_message,
)
from src.map_utils import render_mission_map






st.set_page_config(
    page_title="SAHM Emergency Command",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()


def ensure_ui_defaults() -> None:
    """Initialize persistent UI state."""
    if "view_mode" not in st.session_state:
        st.session_state["view_mode"] = "AI Triage"
    if "ui_theme" not in st.session_state:
        base_theme = str(st.get_option("theme.base") or "light").strip().lower()
        st.session_state["ui_theme"] = "Dark" if base_theme == "dark" else "Light"


def apply_theme_overrides() -> None:
    """Apply runtime theme tokens after base stylesheet loads."""
    if st.session_state.get("ui_theme", "Light") != "Dark":
        return

    st.markdown(
        """
<style>
:root {
    --bg-page: #071116;
    --bg-page-alt: #0c1820;
    --bg-surface: #0f1d26;
    --bg-surface-soft: #13242e;
    --bg-ink: #08131a;
    --bg-ink-soft: #102633;
    --page-glow-a: rgba(16, 54, 63, 0.42);
    --page-glow-b: rgba(72, 52, 22, 0.34);

    --text-primary: #e6f0f5;
    --text-secondary: #bfd1d9;
    --text-muted: #95aab4;

    --accent: #28b3a5;
    --accent-strong: #3bcab9;
    --accent-soft: #153737;
    --warning: #d79d35;
    --warning-soft: #372a14;
    --danger: #ff7d76;
    --danger-soft: #3b1b1b;
    --info: #67b9df;
    --info-soft: #163140;
    --on-accent: #f3fffd;

    --border: #29434f;
    --border-strong: #365967;
    --focus-ring: 0 0 0 3px rgba(40, 179, 165, 0.28);
    --selection-inset: inset 0 0 0 1px rgba(63, 209, 192, 0.24);

    --surface-glass: rgba(17, 31, 40, 0.82);
    --surface-glass-strong: rgba(19, 35, 46, 0.9);
    --surface-glass-soft: rgba(19, 35, 46, 0.82);
    --sidebar-bg: rgba(9, 20, 27, 0.88);
    --sidebar-panel-bg: #12212b;

    --hero-border: rgba(94, 133, 150, 0.32);
    --hero-eyebrow: #c8dbe2;
    --hero-title: #f2fbff;
    --hero-subtitle: #d6e7ee;
    --hero-chip-bg: rgba(15, 42, 52, 0.72);
    --hero-chip-border: rgba(118, 170, 188, 0.55);
    --hero-chip-text: #def4fb;
    --hero-chip-live-bg: rgba(27, 131, 117, 0.52);
    --hero-chip-live-border: rgba(109, 228, 206, 0.78);

    --alert-text: #e7f2f7;
    --alert-info-border: #3d6f86;
    --alert-warning-border: #7b6130;
    --alert-error-border: #8c4948;
    --alert-success-border: #3b7f74;

    --button-bg: #15252f;
    --input-bg: #12222d;
    --input-bg-soft: #11222b;
    --audio-hover-bg: #17323f;

    --decision-drone-start: #113833;
    --decision-drone-end: #165049;
    --decision-drone-border: #2f8879;
    --decision-drone-text: #c9f6ee;
    --decision-ambulance-start: #3d2e13;
    --decision-ambulance-end: #523916;
    --decision-ambulance-border: #8d6330;
    --decision-ambulance-text: #ffe5bf;
    --decision-both-start: #132f40;
    --decision-both-end: #1c4055;
    --decision-both-border: #3a6f90;
    --decision-both-text: #d5ecfb;

    --badge-high-bg: #4a3515;
    --badge-high-border: #8b6332;
    --badge-high-text: #ffd99f;
    --badge-success-bg: #123833;
    --badge-success-border: #2f8477;
    --badge-success-text: #b8f3e9;

    --medic-header-bg: #132630;
    --medic-specialty-border: #2f7b71;
    --medic-mini-bg: #132733;
    --medic-rating: #f3bf59;
    --medic-neutral-strong: #deedf4;
    --medic-neutral-soft: #b4c8d2;

    --bar-track: #27414c;
    --time-panel-bg: #12222d;
    --time-track-bg: #29434e;
    --time-fill-text: #f4fbff;
    --time-drone-start: #27af9f;
    --time-drone-end: #179688;
    --time-ambulance-start: #e4a332;
    --time-ambulance-end: #c27a12;
    --time-saved-bg: #143730;
    --time-saved-border: #2b7e71;
    --time-saved-text: #bef4e9;
}

[data-testid="stToolbar"] button,
[data-testid="stToolbar"] button svg {
    color: var(--text-secondary) !important;
    fill: var(--text-secondary) !important;
}
</style>
""",
        unsafe_allow_html=True,
    )






@st.cache_data(show_spinner=False)
def load_all_data() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        data = {
            "scenarios": load_scenarios(),
            "cases": load_cases(),
            "categorizer": load_categorizer(),
        }
        return data, None
    except FileNotFoundError as e:
        return None, str(e)
    except Exception as e:
        return None, f"Unexpected error: {e}"







def to_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

def to_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def stable_int_seed(*parts: Any, modulus: int = 10000) -> int:
    """Deterministic integer seed across Python process restarts."""
    payload = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % modulus


def esc_html(value: Any) -> str:
    """Escape text before interpolating into unsafe_allow_html blocks."""
    return html.escape(str(value), quote=True)


def get_voice_stress_level(score: float) -> str:
    """Convert stress score (0.0-1.0) into LOW/MEDIUM/HIGH buckets."""
    if score >= 0.8:
        return "HIGH"
    if score >= 0.5:
        return "MEDIUM"
    return "LOW"


def render_voice_stress_metric(score: float, label: str = "Voice Stress", show_level: bool = True) -> None:
    """Render stress score with compact in-card severity indicator."""
    stress_level = get_voice_stress_level(score)
    dot = {
        "HIGH": "🔴",
        "MEDIUM": "🟠",
        "LOW": "🟢",
    }[stress_level]

    if show_level:
        st.metric(label, f"{score:.0%}", delta=f"{dot} {stress_level}", delta_color="off")
    else:
        st.metric(f"{label} {dot}", f"{score:.0%}")


def classify_reason_tone(reason: str, result: DispatchResult) -> str:
    """
    Classify reasoning line into a UI tone based on known dispatch message patterns.
    Returns one of: error, warning, success, info.
    """
    text = str(reason).strip().lower()

    if text.startswith("critical:") or "exceeds harm threshold" in text:
        return "error"
    if "unsafe" in text or "exceeds safety threshold" in text:
        return "warning"
    if (
        text.startswith("drone saves")
        or text.startswith("drone arrival:")
        or "dispatching drone for immediate aid" in text
    ):
        return "success"
    if (
        "ground ambulance is safe and sufficient" in text
        or "weather risk acceptable" in text
        or "within harm threshold" in text
        or "below efficiency threshold" in text
    ):
        return "info"

    # Structured fallback based on dispatch outcome flags.
    if result.exceeds_harm:
        return "error"
    if result.exceeds_weather:
        return "warning"
    if result.exceeds_efficiency:
        return "success"
    return "info"


def render_reasoning_lines(result: DispatchResult) -> None:
    """Render decision reasoning with deterministic severity styling."""
    tone_to_renderer = {
        "error": st.error,
        "warning": st.warning,
        "success": st.success,
        "info": st.info,
    }
    for reason in result.reasons:
        reason_text = str(reason).strip()
        if reason_text.lower().startswith("drone arrival:"):
            continue
        tone = classify_reason_tone(reason, result)
        tone_to_renderer[tone](reason_text)






def render_header():
    """Render top product hero."""
    st.markdown(
        f"""
    <section class="app-hero">
      <div class="app-hero__eyebrow">Emergency Command Platform</div>
      <h1>SAHM Dispatch Console</h1>
      <p>Triage, dispatch, and medic orchestration in one operational surface.</p>
      <div class="app-hero__chips">
        <span class="hero-chip hero-chip--live">Live System</span>
      </div>
    </section>
    """,
        unsafe_allow_html=True,
    )

def render_navigation():
    """Render workspace + theme controls."""

    views = [
        "AI Triage",
        "Live Command Center",
        "Scenarios",
        "Test Cases",
        "Data Explorer",
    ]
    nav_col, theme_col = st.columns([5.2, 1.35], gap="small")
    with nav_col:
        st.markdown('<div class="workspace-switcher-label">Workspace</div>', unsafe_allow_html=True)
        nav_buttons = st.columns(len(views), gap="small")
        for idx, view in enumerate(views):
            is_active = st.session_state.get("view_mode") == view
            with nav_buttons[idx]:
                if st.button(
                    view,
                    key=f"workspace_nav_{idx}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["view_mode"] = view
                    st.rerun()
    with theme_col:
        st.markdown('<div class="workspace-switcher-label">Theme</div>', unsafe_allow_html=True)
        theme_buttons = st.columns(2, gap="small")
        for idx, theme in enumerate(["Light", "Dark"]):
            is_active = st.session_state.get("ui_theme") == theme
            with theme_buttons[idx]:
                if st.button(
                    theme,
                    key=f"theme_toggle_{theme.lower()}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state["ui_theme"] = theme
                    st.rerun()

def render_time_comparison(result):
    """Render a visual comparison of drone vs ambulance ETA."""
    drone_eta = result.air_eta_min
    ambulance_eta = result.ground_eta_min
    time_saved = result.time_delta_min
    
    
    if drone_eta <= 0 or ambulance_eta <= 0:
        return
    
    
    max_eta = max(drone_eta, ambulance_eta)
    drone_pct = (drone_eta / max_eta) * 100
    ambulance_pct = (ambulance_eta / max_eta) * 100
    
    st.markdown(f"""
<div class="time-comparison">
    <div class="time-comparison-header">⏱ Response Time Comparison</div>
    <div class="time-comparison-bars">
        <div class="time-bar-row">
            <div class="time-bar-label">🚁 Drone</div>
            <div class="time-bar-container">
                <div class="time-bar-fill drone" style="width: {drone_pct}%;">{drone_eta:.1f} min</div>
            </div>
        </div>
        <div class="time-bar-row">
            <div class="time-bar-label">🚑 Ambulance</div>
            <div class="time-bar-container">
                <div class="time-bar-fill ambulance" style="width: {ambulance_pct}%;">{ambulance_eta:.1f} min</div>
            </div>
        </div>
    </div>
    <div class="time-saved-badge">
        <span class="icon">⚡</span>
        <span>Drone saves {time_saved:.1f} minutes</span>
    </div>
</div>
""", unsafe_allow_html=True)


def render_payload_tools(tools: List[str]) -> None:
    """Render payload tools without raw HTML blocks."""
    st.markdown("#### 📦 Drone Payload")
    cols = st.columns(2)
    for idx, tool in enumerate(tools):
        with cols[idx % 2]:
            st.write(f"⚡ {tool}")


def render_decision_support(
    result: DispatchResult,
    clinical_category: Optional[str] = None,
    include_payload: bool = True,
    include_time: bool = True,
) -> None:
    """Render supporting visual context for dispatch decisions."""
    case_name = getattr(result, 'case_name', None) or getattr(result, 'emergency_case', None) or ''
    category_tool_map = {
        "cardiac": "Cardiac Arrest",
        "trauma_bleeding": "Severe Trauma",
        "respiratory": "Respiratory Distress",
        "allergic": "Anaphylaxis",
        "neuro": "Stroke",
    }
    fallback_key = category_tool_map.get(str(clinical_category or "").lower(), "General")
    tools = MEDIC_TOOLS.get(case_name, MEDIC_TOOLS.get(fallback_key, MEDIC_TOOLS.get('General')))
    if include_payload and result.response_mode in {"DOCTOR_DRONE", "BOTH"}:
        render_payload_tools(tools)
    if include_time:
        render_time_comparison(result)


def render_decision_banner(result):
    if result.response_mode == "BOTH":
        st.markdown(
            f"""
<div class="decision-banner both">
  <h1>SIMULTANEOUS RESPONSE</h1>
  <p>CRITICAL: Drone (Immediate Aid) + Ambulance (Transport)</p>
  <div style="margin-top: 10px;">
    <span class="badge badge-success">{result.rule_triggered}</span>
    <span class="badge badge-success" style="margin-left: 8px;">Confidence: {result.confidence*100:.0f}%</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    elif result.response_mode == "DOCTOR_DRONE":
        st.markdown(
            f"""
<div class="decision-banner drone">
  <h1>DOCTOR DRONE AUTHORIZED</h1>
  <p>Aerial Medical Unit | Immediate Takeoff Cleared</p>
  <div style="margin-top: 10px;">
    <span class="badge badge-success">{result.rule_triggered}</span>
    <span class="badge badge-success" style="margin-left: 8px;">Confidence: {result.confidence*100:.0f}%</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    else:  
        st.markdown(
            f"""
<div class="decision-banner ambulance">
  <h1>GROUND AMBULANCE DISPATCH</h1>
  <p>Standard Emergency Response Protocol</p>
  <div style="margin-top: 10px;">
    <span class="badge badge-high">{result.rule_triggered}</span>
    <span class="badge badge-high" style="margin-left: 8px;">Confidence: {result.confidence*100:.0f}%</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

def render_medic_assignment(assignment: Dict[str, Any]):
    """Render matched medic assignment with horizontal progress bars"""
    
    if assignment.get("status") != "success" or not assignment.get("assigned_medic"):
        if assignment.get("reasoning"):
            st.info(f"Medic Assignment: {assignment['reasoning']}")
        return
    
    medic = assignment["assigned_medic"]
    breakdown = assignment.get("match_breakdown", {})
    
    
    distance_score = breakdown.get('distance_score', 0)
    specialty_score = breakdown.get('specialty_score', 0)
    workload_score = breakdown.get('workload_score', 0)
    rating_score = breakdown.get('rating_score', 0)
    
    
    status = medic.get("status", "Available")
    status_color = "#10b981" if status == "En Route" else "#3b82f6" if status == "Available" else "#f59e0b"
    medic_status = esc_html(status.upper())
    medic_id = esc_html(medic.get("id", "N/A"))
    medic_name = esc_html(medic.get("name", "Unknown Medic"))
    medic_specialty = esc_html(str(medic.get("specialty", "general")).replace("_", " ").title())
    medic_cert = esc_html(str(medic.get("certification", "unknown")).replace("_", " ").title())
    medic_languages = esc_html(", ".join([str(l).upper() for l in medic.get("languages", ["AR"])]))
    
    medic_card_html = f"""
    <div class="medic-card-container">
        <div class="medic-card-header">
            <span class="badge" style="background: {status_color}22; color: {status_color}; border: 1px solid {status_color};">{medic_status}</span>
            <span class="medic-id-tag">ID: {medic_id}</span>
        </div>
        <div class="medic-card-body">
            <div class="medic-info-box">
                <div class="medic-profile-group">
                    <div>
                        <div class="medic-name-large">{medic_name}</div>
                        <div class="medic-specialty-badge">{medic_specialty}</div>
                        <div style="margin-top: 6px; font-size: 0.85rem; color: var(--medic-rating);">⭐ {medic['rating']}/5.0</div>
                    </div>
                </div>
                <div class="medic-stats-row">
                    <div class="medic-mini-stat">
                        <div class="stat-label-small">ETA</div>
                        <div class="stat-value-large" style="color: var(--accent-strong);">{medic['eta_minutes']:.1f} min</div>
                    </div>
                    <div class="medic-mini-stat">
                        <div class="stat-label-small">Distance</div>
                        <div class="stat-value-large">{medic['distance_km']:.1f} km</div>
                    </div>
                    <div class="medic-mini-stat">
                        <div class="stat-label-small">Missions</div>
                        <div class="stat-value-large" style="color: var(--medic-neutral-soft);">{medic['missions_completed']}</div>
                    </div>
                </div>
                 <div class="muted" style="margin-top: 16px; font-size: 0.8rem;">
                    Languages: <span style="color: var(--medic-neutral-strong); font-weight: 600;">{medic_languages}</span><br/>
                    <div style="margin-top: 4px;">Cert: <span style="color: var(--medic-neutral-strong); font-weight: 600;">{medic_cert}</span></div>
                </div>
            </div>
            <div class="medic-score-panel">
                <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--medic-neutral-soft); margin-bottom: 12px; font-weight: 600;">Match Confidence: <span style="color: var(--accent-strong);">{assignment.get("match_score", 0):.2f}</span></div>
                <div class="compact-score-item">
                    <div class="compact-score-header"><span>Distance Proximity</span><span>{distance_score:.0%}</span></div>
                    <div class="compact-bar-bg"><div class="compact-bar-fill" style="width: {distance_score*100}%;"></div></div>
                </div>
                <div class="compact-score-item">
                    <div class="compact-score-header"><span>Specialty Alignment</span><span>{specialty_score:.0%}</span></div>
                    <div class="compact-bar-bg"><div class="compact-bar-fill" style="width: {specialty_score*100}%; background: #3b82f6;"></div></div>
                </div>
                <div class="compact-score-item">
                    <div class="compact-score-header"><span>Workload Capacity</span><span>{workload_score:.0%}</span></div>
                    <div class="compact-bar-bg"><div class="compact-bar-fill" style="width: {workload_score*100}%; background: #a855f7;"></div></div>
                </div>
                <div class="compact-score-item">
                    <div class="compact-score-header"><span>Performance Rating</span><span>{rating_score:.0%}</span></div>
                    <div class="compact-bar-bg"><div class="compact-bar-fill" style="width: {rating_score*100}%; background: #f59e0b;"></div></div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(textwrap.dedent(medic_card_html), unsafe_allow_html=True)


def resolve_ops_location(patient_location: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """Resolve patient coordinates for operational mapping."""
    patient_location = patient_location or {}
    return {
        "latitude": to_float(patient_location.get("latitude"), 24.7136),
        "longitude": to_float(patient_location.get("longitude"), 46.6753),
    }

def render_live_command(data: Dict[str, Any]):
    """Main live demo view with clear step-based flow."""
    st.subheader("Live Command Center")
    scenario: Optional[Dict[str, Any]] = None

    with st.container(border=True):
        st.markdown("#### 1. Incident")
        scenario_options = {
            f"#{s['scenario_id']}: {s['emergency_case']}": s
            for s in data["scenarios"]
        }
        selected_name = st.selectbox("Scenario", options=list(scenario_options.keys()))
        scenario = scenario_options[selected_name]

        overview_left, overview_right = st.columns([2, 1], gap="large")
        with overview_left:
            st.write(f"**{scenario['emergency_case']}**")
            st.write(f"{scenario['location']} • {scenario['time_of_day']}")
        with overview_right:
            render_voice_stress_metric(float(scenario.get("voice_stress_score", 0.0)), "Voice Stress")

        weather_risk_pct = float(scenario["weather_risk_pct"])
        harm_threshold_min = float(scenario["harm_threshold_min"])
        ground_eta_min = float(scenario["ground_eta_min"])
        air_eta_min = float(scenario["air_eta_min"])

    with st.container(border=True):
        st.markdown("#### 2. Dispatch Inputs")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            weather_risk_pct = st.number_input("Weather Risk (%)", 0.0, 100.0, weather_risk_pct, 1.0)
        with col2:
            harm_threshold_min = st.number_input("Harm Threshold (min)", 1.0, 120.0, harm_threshold_min, 1.0)
        with col3:
            ground_eta_min = st.number_input("Ground ETA (min)", 0.5, 240.0, ground_eta_min, 0.5)
        with col4:
            air_eta_min = st.number_input("Air ETA (min)", 0.5, 60.0, air_eta_min, 0.1)

    result = dispatch(weather_risk_pct, harm_threshold_min, ground_eta_min, air_eta_min)

    with st.container(border=True):
        st.markdown("#### 3. Dispatch Decision")
        render_decision_banner(result)
        render_decision_support(result)
        render_reasoning_lines(result)

    if result.response_mode in {"DOCTOR_DRONE", "BOTH"}:
        decision_output = {
            "response_mode": "combined" if result.response_mode == "BOTH" else "aerial_only",
        }
        category = "cardiac"
        if scenario and "emergency_case" in scenario:
            case_lower = scenario["emergency_case"].lower()
            if "cardiac" in case_lower or "heart" in case_lower or "chest pain" in case_lower:
                category = "cardiac"
            elif "trauma" in case_lower or "bleed" in case_lower:
                category = "trauma_bleeding"
            elif "respiratory" in case_lower or "breath" in case_lower:
                category = "respiratory"
            elif "stroke" in case_lower or "neuro" in case_lower:
                category = "neuro"

        triage_output = {
            "severity_level": 3,
            "category": category,
        }
        scenario_id = scenario.get("scenario_id", 1) if scenario else 999
        assignment = assign_medic(decision_output, triage_output, scenario_seed=scenario_id)
        ops_location = resolve_ops_location(assignment.get("patient_location"))
        all_medics = assignment.get("all_medics", [])

        with st.container(border=True):
            st.markdown("#### 4. Operational Assets")
            render_mission_map(
                patient_location=ops_location,
                medics=all_medics,
                selected_medic=assignment.get("assigned_medic"),
                height=420,
            )

        st.markdown("#### Assigned Medical Specialist")
        render_medic_assignment(assignment)
    else:
        st.info("Ground dispatch selected. No aerial medic deployment required.")


def render_scenarios_tab(data: Dict[str, Any]):
    """Scenario lab workspace."""
    st.subheader("Scenarios")

    with st.container(border=True):
        scenario_options = {f"#{s['scenario_id']}: {s['emergency_case']}": s for s in data["scenarios"]}
        selected = st.selectbox("Scenario", options=list(scenario_options.keys()))
        scenario = scenario_options[selected]

        st.write(f"**{scenario['emergency_case']}**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            w = st.number_input("Weather (%)", 0.0, 100.0, float(scenario["weather_risk_pct"]), 1.0)
        with col2:
            h = st.number_input("Harm (min)", 1.0, 120.0, float(scenario["harm_threshold_min"]), 1.0)
        with col3:
            g = st.number_input("Ground (min)", 0.5, 240.0, float(scenario["ground_eta_min"]), 0.5)
        with col4:
            a = st.number_input("Air (min)", 0.5, 60.0, float(scenario["air_eta_min"]), 0.1)

    result = dispatch(w, h, g, a)
    with st.container(border=True):
        render_decision_banner(result)
        st.markdown("#### Reasoning")
        render_reasoning_lines(result)

    with st.expander("All Scenarios", expanded=False):
        df = pd.DataFrame(
            [
                {
                    "ID": s["scenario_id"],
                    "Case": s["emergency_case"],
                    "Severity": s["severity"],
                    "Weather": f"{s['weather_risk_pct']}%",
                    "Ground": f"{s['ground_eta_min']} min",
                    "Air": f"{s['air_eta_min']} min",
                    "Expected": s["expected_decision"],
                }
                for s in data["scenarios"]
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_test_cases_tab(data: Dict[str, Any]):
    """Test case validation workspace."""
    st.subheader("Test Cases")

    with st.container(border=True):
        case_options = {f"#{c['case_id']}: {c['case_name']}": c for c in data["cases"]}
        selected = st.selectbox("Test Case", options=list(case_options.keys()))
        case = case_options[selected]

        c1, c2 = st.columns([2, 1])
        with c1:
            st.write(f"**{case['case_name']}**")
        with c2:
            render_voice_stress_metric(float(case.get("voice_stress_score", 0.0)), "Voice Stress")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            w = st.number_input("Weather (%)", 0.0, 100.0, float(case["weather_risk_pct"]), 1.0, key="case_w")
        with col2:
            h = st.number_input("Harm (min)", 1.0, 120.0, float(case["harm_threshold_min"]), 1.0, key="case_h")
        with col3:
            g = st.number_input("Ground (min)", 0.5, 240.0, float(case["ground_eta_min"]), 0.5, key="case_g")
        with col4:
            a = st.number_input("Air (min)", 0.5, 60.0, float(case["air_eta_min"]), 0.1, key="case_a")

    with st.container(border=True):
        result = dispatch(w, h, g, a)
        render_decision_banner(result)


def render_triage_tab(data: Dict[str, Any]):
    """AI triage workspace with two-stage flow: intake then operations."""
    if 'ai_symptoms' not in st.session_state:
        st.session_state.ai_symptoms = []
    if 'ai_transcription' not in st.session_state:
        st.session_state.ai_transcription = ""
    if 'ai_stress' not in st.session_state:
        st.session_state.ai_stress = 0.5
    if 'ai_medical_summary' not in st.session_state:
        st.session_state.ai_medical_summary = ""
    if 'ai_duration' not in st.session_state:
        st.session_state.ai_duration = 10

    def reset_current_call() -> None:
        keys_to_clear = [
            "ai_transcription",
            "ai_symptoms",
            "ai_stress",
            "ai_medical_summary",
            "ai_duration",
            "last_processed_audio_id",
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    triage_ready = bool(str(st.session_state.ai_medical_summary).strip())
    st.subheader("AI Triage + Dispatch")

    with st.expander("1. Environment", expanded=not triage_ready):
        weather = st.slider("Weather Risk (%)", 0.0, 100.0, st.session_state.get('env_weather', 15.0), 1.0)
        c1, c2 = st.columns(2)
        with c1:
            ground = st.slider("Ground ETA (min)", 1.0, 60.0, st.session_state.get('env_ground', 20.0), 0.5)
        with c2:
            air = st.slider("Air ETA (min)", 1.0, 15.0, st.session_state.get('env_air', 3.6), 0.1)

        st.session_state.env_weather = weather
        st.session_state.env_ground = ground
        st.session_state.env_air = air

    with st.expander("2. Voice Intake", expanded=not triage_ready):
        gemini_available = is_gemini_available()

        if st.session_state.ai_transcription:
            intake_info_col, intake_action_col = st.columns([8.6, 1.4], gap="small")
            with intake_info_col:
                st.caption("Latest call is loaded. Use New Call to replace it.")
            with intake_action_col:
                if st.button(
                    "New Call",
                    key="triage_restart_voice",
                    help="Clear the current intake and start a fresh call.",
                    type="secondary",
                    use_container_width=True,
                ):
                    reset_current_call()
        else:
            audio_recorder_value = None
            file_uploader_value = None

            if gemini_available:
                audio_recorder_value = st.audio_input("Record Emergency Call", key="triage_audio")
                file_uploader_value = st.file_uploader(
                    "Or upload an audio file (.wav, .mp3)",
                    type=["wav", "mp3"],
                    key="triage_audio_upload",
                )
            else:
                st.warning(f"{get_availability_message()}")

            audio_bytes = None
            mime_type = None
            audio_hash = None

            if audio_recorder_value:
                try:
                    audio_bytes = audio_recorder_value.read()
                    mime_type = "audio/wav"
                    audio_hash = hashlib.md5(audio_bytes).hexdigest()
                except Exception as e:
                    st.error(f"Audio recording error: {e}")
            elif file_uploader_value:
                try:
                    audio_bytes = file_uploader_value.read()
                    mime_type = file_uploader_value.type or "audio/wav"
                    audio_hash = hashlib.md5(audio_bytes).hexdigest()
                except Exception as e:
                    st.error(f"File upload error: {e}")

            if audio_bytes and gemini_available:
                try:
                    last_hash = st.session_state.get("last_processed_audio_id")
                    if audio_hash != last_hash:
                        with st.spinner("AI Engine Analyzing Voice Biomarkers & Symptoms..."):
                            ai_result = analyze_audio_call(
                                audio_bytes,
                                mime_type,
                                env_context={"weather": weather, "ground_eta": ground, "air_eta": air},
                            )

                        if ai_result and ai_result.get("success", True):
                            st.session_state.ai_transcription = ai_result.get("transcription", "")
                            st.session_state.ai_symptoms = ai_result.get("symptoms", [])
                            st.session_state.ai_stress = float(ai_result.get("voiceStressScore", 0.5))
                            st.session_state.ai_medical_summary = ai_result.get("medicalSummary", "")
                            st.session_state.ai_duration = int(ai_result.get("symptomDurationMinutes", 10))
                            st.session_state.last_processed_audio_id = audio_hash
                            st.success("AI analysis complete.")
                            st.rerun()
                        else:
                            if isinstance(ai_result, dict) and ai_result.get("error"):
                                st.error(ai_result["error"])
                            else:
                                st.error("AI analysis failed. Please try again.")
                except Exception as e:
                    st.error(f"Audio processing error: {e}")

        if st.session_state.ai_transcription:
            st.info(f"\"{st.session_state.ai_transcription}\"")

    if not st.session_state.ai_medical_summary:
        st.info("Run voice analysis to unlock dispatch outputs.")
        return

    symptoms = st.session_state.ai_symptoms
    free_text = st.session_state.ai_medical_summary
    duration = st.session_state.ai_duration
    voice_stress = st.session_state.ai_stress
    triage_result = triage(symptoms, free_text, duration, voice_stress)
    sev = to_int(triage_result.get("severity_level"), 0)
    cat = str(triage_result.get("category", "other_unclear"))
    confidence = float(triage_result.get("confidence", 0.0))

    category_harm_map = {
        "cardiac": 5, "respiratory": 5, "neuro": 10,
        "trauma_bleeding": 5, "allergic": 3, "infection_fever": 30,
        "gi_dehydration": 30, "mental_health": 60, "other_unclear": 15,
    }
    harm = category_harm_map.get(cat, 15)
    if sev == 3:
        harm = min(harm, 5)
    elif sev == 2:
        harm = min(harm, 10)

    result = dispatch(
        st.session_state.env_weather,
        harm,
        st.session_state.env_ground,
        st.session_state.env_air,
    )

    assignment = None
    ops_location = None
    all_medics = []
    if result.response_mode in ["DOCTOR_DRONE", "BOTH"]:
        mode_map = {"DOCTOR_DRONE": "aerial_only", "AMBULANCE": "ground_only", "BOTH": "combined"}
        matcher_mode = mode_map.get(str(result.response_mode), "aerial_only")
        decision_output = {"response_mode": matcher_mode}
        triage_output = {"severity_level": sev, "category": cat}
        triage_seed = stable_int_seed(cat, sev, duration, ",".join(sorted(symptoms)))
        assignment = assign_medic(decision_output, triage_output, scenario_seed=triage_seed)
        ops_location = resolve_ops_location(assignment.get("patient_location"))
        all_medics = assignment.get("all_medics", [])

    with st.container(border=True):
        st.markdown("#### Triage Summary")
        m1, m2, m3, m4 = st.columns(4, gap="small")
        with m1:
            st.metric("Category", cat.replace("_", " ").title())
        with m2:
            st.metric("Severity Level", str(sev))
        with m3:
            st.metric("Confidence", f"{confidence*100:.0f}%")
        with m4:
            render_voice_stress_metric(float(voice_stress), "Voice Stress", show_level=False)

        st.markdown("#### Symptoms")
        if symptoms:
            for symptom in symptoms:
                st.write(f"• {symptom.replace('_', ' ').title()} ({SYMPTOM_POINTS.get(symptom, 0)} pts)")
        else:
            st.info("No symptoms detected")

        rf = set(symptoms) & RED_FLAGS
        if rf:
            st.error(f"RED FLAGS: {', '.join([s.replace('_', ' ').title() for s in rf])}")

        st.markdown("#### Medical Summary")
        st.info(st.session_state.ai_medical_summary)

    with st.container(border=True):
        st.markdown("#### Dispatch Decision")
        render_decision_banner(result)
        reasoning_col, support_col = st.columns(2, gap="large")
        with reasoning_col:
            st.markdown("##### Why This Decision")
            render_reasoning_lines(result)
        with support_col:
            st.markdown("##### Response Advantage")
            if result.response_mode in {"DOCTOR_DRONE", "BOTH"}:
                render_decision_support(
                    result,
                    clinical_category=cat,
                    include_payload=True,
                    include_time=False,
                )
            else:
                st.info("No drone payload required for ground dispatch.")

        st.markdown("##### ⏱ Response Time Comparison")
        render_time_comparison(result)

    if assignment:
        with st.container(border=True):
            st.markdown("#### Assigned Medical Specialist")
            render_medic_assignment(assignment)

    with st.container(border=True):
        st.markdown("#### Deployment")
        if assignment and ops_location is not None:
            st.markdown("##### Live Operations Map")
            render_mission_map(
                patient_location=ops_location,
                medics=all_medics,
                selected_medic=assignment.get("assigned_medic"),
                height=420,
            )
        else:
            st.info("Ground dispatch selected. No aerial medic deployment required.")


def render_data_explorer(data: Dict[str, Any]):
    """Data explorer view"""
    
    st.subheader("Data Explorer")
    with st.container(border=True):
        if isinstance(data["categorizer"], list):
            df = pd.DataFrame(data["categorizer"])
            st.dataframe(df, use_container_width=True, hide_index=True)






def main():
    ensure_ui_defaults()
    apply_theme_overrides()
    render_header()
    render_navigation()

    data, error = load_all_data()
    if error:
      st.error(f"Data Loading Error: {error}")
      st.info("Ensure these files exist in /Files directory")
      st.stop()

    with st.sidebar:
      st.markdown("### Validation")
      with st.expander("Validation Suite", expanded=False):
        if st.button("Run Validation", use_container_width=True):
          with st.spinner("Validating..."):
            s_rep = validate_scenarios()
            c_rep = validate_cases()
            total = s_rep.total + c_rep.total
            matches = s_rep.matches + c_rep.matches
            accuracy = (matches / total * 100) if total > 0 else 0
            st.success(f"Scenarios: {s_rep.matches}/{s_rep.total}")
            st.success(f"Cases: {c_rep.matches}/{c_rep.total}")
            st.metric("Accuracy", f"{accuracy:.1f}%")

    
    if st.session_state['view_mode'] == "Live Command Center":
      render_live_command(data)
    elif st.session_state['view_mode'] == "Scenarios":
      render_scenarios_tab(data)
    elif st.session_state['view_mode'] == "Test Cases":
      render_test_cases_tab(data)
    elif st.session_state['view_mode'] == "AI Triage":
      render_triage_tab(data)
    elif st.session_state['view_mode'] == "Data Explorer":
      render_data_explorer(data)


if __name__ == "__main__":
    main()
