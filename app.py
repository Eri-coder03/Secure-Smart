import streamlit as st
import pandas as pd
import plotly.express as px
from simulator import generate_tick
from detector import analyze, recommendation
from ml_detector import fit_baseline, detect
from history import update_history, get_history
from emergency import simulate_emergencies, update_emergency_history, get_emergency_history
from incidents import sync_incidents, get_cases, latest_case, is_new_case, change_case, cases_table, recover_devices, recover_environment

st.set_page_config(page_title="SecureSmart", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.3rem;}
div[data-testid="stMetric"] {border:1px solid #2b3448; padding:14px; border-radius:14px;}
.hero {padding:18px 22px;border-radius:18px;background:linear-gradient(90deg,#111827,#172554);margin-bottom:16px;}
.hero h1 {color:#f8fafc !important; margin:0 0 12px 0;}
.hero .small {color:#cbd5e1 !important;font-size:.92rem}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🛡️ SecureSmart</h1><div class="small">AI-inspired Smart World Security & Emergency Monitoring Prototype</div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Demo Controls")
    seed = st.number_input("Simulation seed", min_value=1, max_value=9999, value=42)
    st.markdown("**Cybersecurity scenario**")
    incident = st.toggle("Simulate suspicious CCTV activity", value=False)
    st.markdown("**Environmental scenario**")
    emergency_scenario = st.selectbox("Simulated sensor event", ["None", "Gas / smoke", "Water leak"])
    combined_demo = st.toggle("Show both problems together", value=False)
    if combined_demo:
        st.caption("At update 3 or later, the gas/smoke sensor and CCTV both reach a critical alert.")
    st.caption("The prototype uses simulated IoT telemetry. No real devices are attacked or controlled.")
    if "tick" not in st.session_state:
        st.session_state.tick = 0
    if st.button("Next telemetry update", use_container_width=True):
        st.session_state.tick += 1
    if st.button("Reset demo", use_container_width=True):
        for key in ("cases", "seen_alerts", "incident_history", "last_recorded_tick",
                    "emergency_history", "last_emergency_key"):
            st.session_state.pop(key, None)
        st.session_state.tick = 0
        st.rerun()
    st.caption(f"Simulation update: {st.session_state.tick}. Click to advance the demo.")
    page = st.radio("Navigate", ["Command Center", "Devices", "Problem Center", "Incident History", "Incident Cases", "About"])

@st.cache_resource
def baseline(seed):
    return fit_baseline(seed)

df = recover_devices(generate_tick(28, int(seed), st.session_state.tick, incident or combined_demo))
df = analyze(detect(df, baseline(int(seed))))
update_history(df, st.session_state.tick)
selected_environment = "Gas / smoke" if combined_demo else emergency_scenario
emergencies = recover_environment(simulate_emergencies(st.session_state.tick, selected_environment))
update_emergency_history(emergencies, st.session_state.tick, selected_environment)
sync_incidents(get_history(), get_emergency_history())

def case_label(source, target):
    case = latest_case(source, target)
    return f'{case["id"]}: {case["status"]}' if case else "No case"

df["case_status"] = df["device_id"].map(lambda target: case_label("Device", target))
emergencies["case_status"] = emergencies["sensor_id"].map(lambda target: case_label("Environment", target))
df["notify"] = df["device_id"].map(lambda target: is_new_case("Device", target))
emergencies["notify"] = emergencies["sensor_id"].map(lambda target: is_new_case("Environment", target))
open_cases = sum(case["status"] != "Resolved" for case in get_cases())
resolved_cases = sum(case["status"] == "Resolved" for case in get_cases())

if page == "Command Center":
    online = int(df["online"].sum())
    threats = int((df["risk_score"] >= 45).sum())
    avg = int(df["risk_score"].mean())

    environmental_count = int((emergencies["level"] != "NORMAL").sum())
    a,b,c,d,e = st.columns(5)
    a.metric("Connected Devices", len(df))
    b.metric("Online", online)
    c.metric("Environmental alerts", environmental_count)
    d.metric("Cybersecurity alerts", threats)
    e.metric("Average device risk", f"{avg}/100")
    active_emergencies = emergencies[(emergencies["level"] == "EMERGENCY") & emergencies["notify"]]
    if not active_emergencies.empty:
        for _, row in active_emergencies.iterrows():
            st.error(f'PRIORITY 1 · Simulated environmental emergency at {row["location"]}. Case {row["case_status"]}. Reading remains {row["reading_index"]}/100.')
    elif not emergencies[(emergencies["level"] == "WATCH") & emergencies["notify"]].empty:
        st.warning("Environmental sensor demo: WATCH level. Open Problem Center.")
    critical_devices = df[(df["severity"] == "CRITICAL") & df["notify"]]
    if not critical_devices.empty:
        for _, row in critical_devices.iterrows():
            st.error(f'PRIORITY 2 · Critical cybersecurity alert on {row["device_id"]}. Case {row["case_status"]}. Risk remains {row["risk_score"]}/100.')
    else:
        new_high = df[(df["severity"] == "HIGH") & df["notify"]]
        if not new_high.empty:
            st.warning(f"Cybersecurity: {len(new_high)} new HIGH alert(s). Open Problem Center.")
    st.caption("Two separate streams: environmental sensor alerts concern site safety; CCTV telemetry concerns device cybersecurity.")
    st.caption(f"Case workflow: {open_cases} open · {resolved_cases} resolved. Resolve applies a simulated recovery to that device or sensor.")

    left, right = st.columns([1.5,1])
    with left:
        st.subheader("Device Risk Overview")
        chart = df.sort_values("risk_score", ascending=False).head(12)
        fig = px.bar(chart, x="device_id", y="risk_score", hover_data=["device_type","location","severity"])
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Current Status: Devices and Sensors")
        device_status = pd.DataFrame({"status": "Cybersecurity · " + df["severity"], "count": 1})
        sensor_status = pd.DataFrame({"status": "Environment · " + emergencies["level"], "count": 1})
        counts = pd.concat([device_status, sensor_status], ignore_index=True).groupby("status", as_index=False)["count"].sum()
        st.plotly_chart(px.pie(counts, names="status", values="count", hole=.55), use_container_width=True)
        st.caption("Pie slices count 28 devices and 2 sensors by current status. Their numeric scores are not compared.")

    st.subheader("Environmental Sensor Readings")
    sensor_chart = px.bar(emergencies, x="sensor_id", y="reading_index", color="level",
                          color_discrete_map={"NORMAL": "#22c55e", "WATCH": "#f59e0b", "EMERGENCY": "#ef4444"},
                          hover_data=["signal", "location"], text="reading_index", range_y=[0, 100],
                          labels={"sensor_id": "Sensor", "reading_index": "Invented reading index (0–100)"})
    st.plotly_chart(sensor_chart, use_container_width=True)
    st.caption("Environmental readings are invented for this demo, not calibrated safety measurements.")

    st.subheader("Device Cybersecurity Alerts")
    alerts = df[df["risk_score"] >= 25].sort_values("risk_score", ascending=False)
    if alerts.empty:
        st.success("No elevated-risk devices in the current simulation.")
    else:
        st.dataframe(alerts[["device_id","device_type","location","risk_score","severity","case_status"]], use_container_width=True, hide_index=True)

    st.subheader("Environmental Alerts")
    environmental_alerts = emergencies[emergencies["level"] != "NORMAL"]
    if environmental_alerts.empty:
        st.success("No environmental sensor alerts in the current simulation.")
    else:
        st.dataframe(environmental_alerts[["sensor_id", "signal", "location", "reading_index", "level", "case_status"]],
                     use_container_width=True, hide_index=True)

elif page == "Devices":
    st.subheader("Smart World Device Inventory")
    st.dataframe(df[["device_id","device_type","location","online","network_requests","failed_logins","cpu_usage","temperature","packet_rate","ml_anomaly","risk_score","severity"]], use_container_width=True, hide_index=True)

elif page == "Problem Center":
    st.title("Problem Center")
    st.caption(f"Case workflow: {open_cases} open · {resolved_cases} resolved. Resolved targets return to normal in this demo.")
    st.subheader("1. Environmental sensor problems")
    st.write("ENV-01: gas/smoke index in the Lab Wing. ENV-02: water level index in Parking.")
    st.caption("All readings are invented indices from 0 to 100. WATCH and EMERGENCY thresholds are for this demo only.")
    active = emergencies[(emergencies["level"] == "EMERGENCY") & emergencies["notify"]]
    watching = emergencies[(emergencies["level"] == "WATCH") & emergencies["notify"]]
    if not active.empty:
        for _, row in active.iterrows():
            st.error(f'{row["level"]}: {row["signal"]} at {row["location"]} (index {row["reading_index"]}/100).')
        st.write("**Demo response:** Notify the responsible site team and follow its established emergency procedures.")
    elif not watching.empty:
        st.warning("Simulated sensor readings are elevated. Continue checking the readings.")
    elif (emergencies["level"] == "NORMAL").all():
        st.success("No environmental alerts in the current simulated reading.")
    st.subheader("Environmental Sensor Details")
    for _, row in emergencies.iterrows():
        with st.expander(f'{row["sensor_id"]} · {row["signal"]} · {row["level"]}', expanded=row["level"] != "NORMAL"):
            st.write(f'**Location:** {row["location"]}')
            st.write(f'**Simulated reading:** {row["reading_index"]}/100  |  **Status:** {row["level"]}')
            st.write(f'**Case:** {row["case_status"]}')
            if row["level"] == "EMERGENCY":
                st.write("**Demo response:** Notify the responsible site team and follow its established procedures.")
            elif row["level"] == "WATCH":
                st.write("**Demo response:** Review the sensor reading and continue monitoring.")
            else:
                st.write("**Demo response:** No alert for this sensor.")

    st.subheader("2. Device cybersecurity problems")
    st.caption("CCTV and other device telemetry is reviewed separately from the environmental sensors above.")
    alerts = df[df["risk_score"] >= 25].sort_values("risk_score", ascending=False)
    if alerts.empty:
        st.info("No device cybersecurity alerts. Enable 'Simulate suspicious CCTV activity' or 'Show both problems together'.")
    elif not alerts[(alerts["severity"] == "CRITICAL") & alerts["notify"]].empty:
        critical_ids = ", ".join(alerts.loc[(alerts["severity"] == "CRITICAL") & alerts["notify"], "device_id"])
        st.error(f"PRIORITY 2 · Critical cybersecurity alert on {critical_ids}. Inspect the affected device below.")
    elif not alerts[(alerts["severity"] == "HIGH") & alerts["notify"]].empty:
        st.warning("Cybersecurity alert: a device needs review.")
    for _, row in alerts.iterrows():
        with st.expander(f'{row["severity"]} • {row["device_id"]} • Risk {row["risk_score"]}/100', expanded=row["severity"]=="CRITICAL"):
            st.write(f'**Device:** {row["device_type"]}  |  **Location:** {row["location"]}')
            st.write(f'**Case:** {row["case_status"]}')
            st.write(f'Network requests: {row["network_requests"]} • Failed logins: {row["failed_logins"]} • CPU: {row["cpu_usage"]:.0f}% • Packet rate: {row["packet_rate"]}')
            st.write(f'**ML baseline flagged anomaly:** {"Yes" if row["ml_anomaly"] else "No"}')
            st.write("**Recommended response:** " + recommendation(row))

elif page == "Incident Cases":
    st.subheader("Incident Cases")
    st.info("Demo triage order: an environmental EMERGENCY is reviewed first; cybersecurity alerts follow. These categories have separate sources and response teams.")
    st.caption("Demo workflow only. Resolve simulates recovery in the charts; it does not control any device or send a notification.")
    cases = get_cases()
    if not cases:
        st.info("Create a simulated alert first. Then return here to acknowledge and review it.")
    else:
        st.dataframe(cases_table().sort_values("priority"), use_container_width=True, hide_index=True)
        case_id = st.selectbox("Select case", [case["id"] for case in cases][::-1])
        selected = next(case for case in cases if case["id"] == case_id)
        st.write(f'**{selected["id"]}**  |  {selected["source"]}  |  {selected["target"]}  |  {selected["status"]}')
        note = st.text_input("Operator note (optional, up to 300 characters)", max_chars=300, key=f"note_{case_id}")
        if selected["status"] == "New":
            if st.button("Acknowledge case"):
                change_case(case_id, "Acknowledge", note)
                st.rerun()
        elif selected["status"] == "Investigating":
            if st.button("Resolve and simulate recovery"):
                change_case(case_id, "Resolve", note)
                st.rerun()
        else:
            st.success("Case marked resolved.")
        st.subheader("Case Timeline")
        st.dataframe(pd.DataFrame(selected["timeline"]), use_container_width=True, hide_index=True)
        if selected["note"]:
            st.write("**Last operator note:** " + selected["note"])

elif page == "Incident History":
    st.subheader("Incident History")
    st.caption("Both histories are kept for this browser session.")
    st.markdown("### 1. Environmental sensor alerts")
    emergency_history = get_emergency_history()
    if emergency_history.empty:
        st.info("No environmental alerts recorded yet.")
    else:
        st.dataframe(emergency_history.iloc[::-1], use_container_width=True, hide_index=True)
        st.download_button("Download environmental alerts (CSV)", emergency_history.to_csv(index=False).encode("utf-8"),
                           file_name="securesmart_environmental_alerts.csv", mime="text/csv")
    st.markdown("### 2. Device cybersecurity alerts")
    history = get_history()
    if history.empty:
        st.info("No device cybersecurity alerts recorded yet.")
    else:
        st.dataframe(history.iloc[::-1], use_container_width=True, hide_index=True)
        st.download_button("Download cybersecurity alerts (CSV)", history.to_csv(index=False).encode("utf-8"),
                           file_name="securesmart_incidents.csv", mime="text/csv")

elif page == "About":
    st.subheader("Why SecureSmart?")
    st.write("""
Smart environments depend on connected devices. SecureSmart demonstrates how a unified monitoring layer can
collect device telemetry, detect abnormal behavior, prioritize risk, and give operators clear response guidance.
This hackathon prototype intentionally uses simulated telemetry so it can be demonstrated safely without attacking
or controlling real infrastructure.
""")
    st.markdown("**Prototype flow:** Devices → Telemetry → ML Baseline + Rule Scoring → Alert Prioritization → Operator Response")
    st.caption("The ML model is trained on synthetic normal data. Environmental indices and thresholds are illustrative, not calibrated safety measurements.")
