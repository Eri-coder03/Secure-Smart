# SecureSmart

A hackathon prototype for the **Smart World** theme. It simulates connected devices, flags unusual telemetry, raises separate environmental alerts, and lets an operator review cases. No real equipment is connected or controlled.

## Run in VS Code on Windows

Extract the ZIP and open the `SecureSmart_Hackathon` folder. In the terminal:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

If `py` does not work but `python` does, replace `py` with `python`.

## Demo in five steps

1. Open **Command Center** with the default simulation seed 42.
2. Enable **Show both problems together** and click **Next telemetry update** three times. ENV-01 reaches EMERGENCY and CCTV DEV-12 reaches CRITICAL.
3. Command Center now shows separate counters, two alert banners, a pie chart containing both sources, and an environmental sensor bar chart.
4. Open **Problem Center**. Its first heading shows detailed environmental sensor alerts; its second shows the CCTV cybersecurity problem. Command Center displays the environmental bar chart and alert table below the device charts. Open **Incident History** to see both records under their own headings.
5. Open **Incident Cases** to acknowledge or resolve a case with a note. Explain that all readings and operator actions are simulated.

After **Acknowledge case**, the notification banner disappears, while the simulated reading and charts remain elevated. After **Resolve and simulate recovery**, the affected device or sensor returns to a normal simulated reading. The counters, bar chart, pie chart and Problem Center update accordingly. The case stays Resolved in Incident Cases and earlier alerts stay in Incident History. Use **Reset demo** in the sidebar to start again.

This recovery is a software demonstration. No real device is repaired or controlled.

## Which alert takes priority?

The app has **two separate streams**. `ENV-01` is an environmental gas/smoke sensor and `ENV-02` is a water sensor. `DEV-12` is a CCTV camera whose network behavior changes in the cyber demo. For this simulated presentation, an environmental EMERGENCY goes first in Incident Cases because it concerns site safety. A cybersecurity HIGH or CRITICAL alert goes to the device security review. The numeric scores across these streams are not directly comparable. The pie chart counts devices and sensors by category and status; it does not average or compare their scores.

## Code guide

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit pages, controls and charts |
| `simulator.py` | 28 simulated devices and the DEV-12 incident |
| `ml_detector.py` | Isolation Forest trained on 1,200 synthetic normal readings |
| `detector.py` | Rule-based risk score and severity |
| `emergency.py` | Invented gas/smoke and water indices and alert history |
| `history.py` | Cybersecurity alert history |
| `incidents.py` | Case IDs, operator status, notes and timeline |

## Scope and limits

- The ML flag means a reading looks unusual relative to synthetic normal data. It does not prove an attack, and the model has not been evaluated on real incidents.
- Environmental indices run from 0 to 100. WATCH begins at 50 and EMERGENCY at 75 **only for this demo**. They are not calibrated measurements or real safety limits.
- Incident Cases and both alert histories are kept in the current Streamlit session. A refresh or server restart can clear them. Acknowledging or resolving a case changes only the interface; it does not notify anyone or control equipment.
- A real deployment would require authorized device connections, validated detection, secure access, persistent storage, and site-approved response procedures.
