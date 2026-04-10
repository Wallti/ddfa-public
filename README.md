# DDFA — Real-Time Threshold Detection for Endurance Athletes

**DFA is the science. DDFA is what makes it usable.**

DDFA is an iOS app that detects both ventilatory thresholds (VT1 and VT2) in real time using DFA alpha1 from a standard chest strap. No lab visit, no lactate strips, no guessing.

## What it does

- **Live VT1 and VT2 detection** from beat-to-beat RR intervals during exercise
- **Dual-engine DFA**: fast engine (sf=1, 200-beat buffer) for responsive VT1 detection + deep engine (sf=5, up to 1280 beats) for stable autonomic tracking
- **Per-session threshold recalibration** — no fixed 0.75/0.50 constants; your threshold is measured fresh every workout
- **TriGate validation** — VT1 fires only when power, HR, and alpha1 all converge within 10%
- **IntensityGauge** — 4-zone colour gauge (green/yellow/orange/red) with 10s EMA smoothing
- **Fatigue tracking** — adaptive drift detection (cardiac/muscular/combined), interval carryover analysis
- **Cross-session learning** — 3D bin history (power x HR x alpha1), Kalman-filtered VT2, personalised baseline
- **Garmin Connect IQ** integration — phone computes, watch displays
- **Full export** — beat-by-beat CSV, FIT files (with native RR intervals), PDF summaries

## Architecture Overview

```
Chest Strap (BLE)
    │
    ▼
RR Preprocessing ──→ Ectopic detection, artefact rejection, interpolation
    │
    ├──→ α₁ Engine (sf=1, scales 4-16, 200 beats) ──→ VT1 Detection
    │
    ├──→ α₂ Engine (sf=5, scales 5-64, 1280 beats) ──→ Stable autonomic tracking
    │                                                     Median-over-scales stabilisation
    │
    ├──→ RMSSD Quality Gate ──→ Plausibility check (holds last good value on artefact)
    │
    ├──→ AlphaMaturityTracker ──→ warmup (<400) → transition (400-1279) → mature (≥1280)
    │
    ├──→ TriGateDetector ──→ Power ±10% AND HR ±10% AND α₁ ±10% → VT1 lock
    │
    ├──→ AdaptiveDriftDetector ──→ Cardiac / Muscular / Combined drift classification
    │
    ├──→ Cross-Session Kalman ──→ VT2 smoothing across workouts
    │
    └──→ IntensityGaugeScore ──→ 0.5·power + 0.3·HR + 0.2·α₁ → 4-zone gauge
```

## What's in this repo

This is the public-facing companion to the closed-source iOS app. It contains:

- **[docs/dfa_alpha1_explained.md](docs/dfa_alpha1_explained.md)** — Full technical article explaining the science behind DFA alpha1 and how DDFA extends it into a real-time product
- **[analysis/alpha_maturity_analysis.py](analysis/alpha_maturity_analysis.py)** — Python script analysing alpha maturity stages (warmup/transition/mature) and alpha drift across a session
- **[examples/sample_session.csv](examples/sample_session.csv)** — Anonymised beat-by-beat data from a real workout session (timestamps zeroed, power/HR offset)
- **[docs/references.md](docs/references.md)** — Key papers behind the DFA alpha1 methodology

## CSV Schema (28 columns)

| Column | Description |
|--------|-------------|
| `beat_idx` | Sequential beat index |
| `timestamp_ms` | Milliseconds since session start |
| `rr_ms` | RR interval in milliseconds |
| `hr_bpm` | Instantaneous heart rate |
| `power_watts` | Current power output |
| `alpha1` | DFA alpha1 (blended dual-engine) |
| `alpha1_smoothed` | EMA-smoothed alpha1 |
| `alpha1_corrected` | Drift-corrected alpha1 |
| `vt1_hr_bpm` / `vt1_power_watts` | Detected VT1 in HR and power |
| `vt1_confidence` | VT1 detection confidence (0-1) |
| `vt1_state` | Detection state (initializing/detecting/confirmed) |
| `vt2_hr_bpm` / `vt2_power_watts` | Detected VT2 in HR and power |
| `vt2_confidence` / `vt2_detected` | VT2 confidence and detection flag |
| `zone` | Current intensity zone |
| `fatigue_level` | Accumulated fatigue estimate |
| `decoupling_pct` | Cardiac decoupling percentage |
| `alpha_tilde` | Detrended alpha estimate |
| `baseline_phase` | Baseline calibration phase |
| `probe_active` / `probe_alpha1` / `probe_r2` | Steady-state probe metrics |
| `probe_vt1_hr` / `probe_dominant` | Probe VT1 detection |

## The science

DFA alpha1 measures the fractal complexity of beat-to-beat heart rate variation. At rest and low intensity, your autonomic nervous system produces complex, fractal-like RR patterns (alpha > 0.75). Cross the aerobic threshold and that complexity collapses — alpha drops below 0.75. Push past the anaerobic threshold and alpha drops below 0.50.

This has been validated against gas exchange (ventilatory thresholds), not lactate — the correlation between HRVT and VT1 is r ~0.95 across multiple studies.

DDFA's contribution is making this work in real time on a phone: noise handling, dual-engine stabilisation, personalised thresholds, TriGate validation, and cross-session learning.

## Key references

- Gronwald, T., Rogers, B., Hoos, O. (2020) — *Fractal correlation properties of HRV as biomarker for intensity distribution*. Frontiers in Physiology.
- Rogers, B. et al. (2021) — Multiple papers validating HRVT (~0.75) against ventilatory and lactate thresholds.
- Kanniainen, M. et al. (2023) — *Estimation of exercise thresholds based on dynamical correlation properties of HRV.*
- Molkkari, M. et al. (2020) — *Dynamical heart beat correlations during running.*
- Plews, D. J. et al. (2013) — *Training adaptation and HRV in elite endurance athletes.*

## Tech stack

- Swift / SwiftUI, on-device only (no cloud)
- 75+ modules, 1200+ automated tests
- BLE RR interval acquisition from any ANT+/BLE chest strap
- DFA computation optimised from O(n^2) to O(n) for real-time processing
- Garmin Connect IQ data field companion

## Status

Active development. Currently in Sprint 87.

---

**Walter Vath** — endurance athlete, developer. DDFA is available for iOS.

## License

MIT License. See [LICENSE](LICENSE).
