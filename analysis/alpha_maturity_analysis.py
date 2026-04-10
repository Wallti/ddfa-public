#!/usr/bin/env python3
"""
Alpha Maturity Stage Analysis
==============================
Analyses the alpha maturity progression (warmup → transition → mature) in DDFA
session data and quantifies alpha drift across stages.

Expected CSV columns:
  - alpha_maturity_stage: "warmup" / "transition" / "mature"
  - alpha1_source: "modeA_120" / "modeB_200" / "dualWindow_blend"
  - vt1_method: VT1 detection method used
  - alpha1_raw: raw alpha before mode blending

Core columns: beat_idx, timestamp_ms, rr_ms, hr_bpm, power_watts,
  alpha1, alpha1_smoothed, alpha1_corrected, vt1_hr_bpm, vt1_power_watts,
  vt1_confidence, vt1_state, zone, fatigue_level, ...

Usage:
    python3 alpha_maturity_analysis.py [--csv path/to/pipeline_results.csv]
    python3 alpha_maturity_analysis.py --check-columns
"""

import csv
import sys
import argparse
import math
from pathlib import Path
from collections import defaultdict

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

CSV_PATH = Path(__file__).parent / "pipeline_results.csv"

# Spalten aus S80 (TASK-559/560/561)
S80_COLUMNS = ["alpha1_source", "vt1_method", "alpha1_raw"]

# Spalte aus S81 (TASK-569)
S81_COLUMNS = ["alpha_maturity_stage"]

MATURITY_ORDER = {"warmup": 0, "transition": 1, "mature": 2}

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def safe_float(val, default=float("nan")):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def load_csv(path: Path) -> tuple[list[str], list[dict]]:
    """Load CSV, return (headers, rows)."""
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []
    return headers, rows


# ──────────────────────────────────────────────────────────────────────────────
# Sanity Check (Sprint-80-Closure Gate)
# ──────────────────────────────────────────────────────────────────────────────

def sanity_check_s80_columns(headers: list[str], rows: list[dict]) -> dict:
    """
    Prüft ob S80-Spalten vorhanden und plausibel befüllt sind.
    Gibt dict mit pass/warn/fail pro Spalte zurück.
    """
    results = {}

    for col in S80_COLUMNS + S81_COLUMNS:
        if col not in headers:
            results[col] = {"status": "MISSING", "detail": "Spalte nicht in CSV"}
            continue

        values = [r[col] for r in rows if r.get(col, "").strip()]
        empty_count = sum(1 for r in rows if not r.get(col, "").strip())
        total = len(rows)

        if len(values) == 0:
            results[col] = {"status": "FAIL", "detail": "Spalte vorhanden aber alle leer"}
            continue

        fill_rate = len(values) / total

        # Column-specific checks
        if col == "alpha1_source":
            valid_vals = {"modeA_120", "modeB_200", "dualWindow_blend"}
            unique = set(values)
            invalid = unique - valid_vals - {"", "nan"}
            if invalid:
                results[col] = {"status": "WARN",
                                "detail": f"Unbekannte Werte: {invalid}. Gültig: {valid_vals}"}
            elif "dualWindow_blend" not in unique:
                results[col] = {"status": "WARN",
                                "detail": f"'dualWindow_blend' nie gesehen. Nur: {unique}"}
            else:
                counts = {v: values.count(v) for v in unique}
                results[col] = {"status": "OK", "detail": f"Verteilung: {counts}"}

        elif col == "alpha1_raw":
            floats = [safe_float(v) for v in values]
            valid = [v for v in floats if not math.isnan(v)]
            if len(valid) == 0:
                results[col] = {"status": "FAIL", "detail": "Keine numerischen Werte"}
            elif min(valid) < -2 or max(valid) > 3:
                results[col] = {"status": "WARN",
                                "detail": f"Verdächtige Range: [{min(valid):.3f}, {max(valid):.3f}]"}
            else:
                mean_v = sum(valid) / len(valid)
                results[col] = {"status": "OK",
                                "detail": f"n={len(valid)}, mean={mean_v:.3f}, "
                                          f"range=[{min(valid):.3f}, {max(valid):.3f}]"}

        elif col == "vt1_method":
            unique = set(values)
            results[col] = {"status": "OK" if len(unique) > 0 else "FAIL",
                            "detail": f"Methoden: {unique}"}

        elif col == "alpha_maturity_stage":
            valid_stages = set(MATURITY_ORDER.keys())
            unique = set(values)
            invalid = unique - valid_stages - {"", "nan"}
            if invalid:
                results[col] = {"status": "WARN",
                                "detail": f"Unbekannte Stages: {invalid}"}
            else:
                counts = {v: values.count(v) for v in unique if v in valid_stages}
                results[col] = {"status": "OK", "detail": f"Stage-Verteilung: {counts}"}

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Maturity Analysis
# ──────────────────────────────────────────────────────────────────────────────

def analyze_maturity(rows: list[dict], session_id: str = "session_1") -> dict:
    """
    Analysiert alpha_maturity_stage-Verlauf einer Session.
    Gibt dict mit Metriken zurück.
    """
    result = {"session_id": session_id}

    has_maturity = any(r.get("alpha_maturity_stage", "").strip() for r in rows)
    if not has_maturity:
        result["status"] = "MISSING_COLUMN"
        result["note"] = "alpha_maturity_stage nicht in Daten — warte auf TASK-569"
        return result

    # Zeit-bis-mature
    first_mature_ts = None
    first_transition_ts = None
    session_start_ts = None

    for r in rows:
        ts = safe_float(r.get("timestamp_ms", ""))
        stage = r.get("alpha_maturity_stage", "").strip()
        if math.isnan(ts):
            continue
        if session_start_ts is None:
            session_start_ts = ts
        if stage == "transition" and first_transition_ts is None:
            first_transition_ts = ts
        if stage == "mature" and first_mature_ts is None:
            first_mature_ts = ts

    if session_start_ts and first_mature_ts:
        result["time_to_mature_s"] = (first_mature_ts - session_start_ts) / 1000.0
        result["time_to_mature_min"] = result["time_to_mature_s"] / 60.0
    else:
        result["time_to_mature_s"] = None
        result["note_mature"] = "Keine 'mature' Stage erreicht in dieser Session"

    if session_start_ts and first_transition_ts:
        result["time_to_transition_s"] = (first_transition_ts - session_start_ts) / 1000.0

    # α-Wert-Verschiebung pro Stage
    alpha_by_stage = defaultdict(list)
    alpha_raw_by_stage = defaultdict(list)

    for r in rows:
        stage = r.get("alpha_maturity_stage", "").strip()
        if stage not in MATURITY_ORDER:
            continue
        a1 = safe_float(r.get("alpha1", ""))
        if not math.isnan(a1):
            alpha_by_stage[stage].append(a1)
        a_raw = safe_float(r.get("alpha1_raw", ""))
        if not math.isnan(a_raw):
            alpha_raw_by_stage[stage].append(a_raw)

    stage_stats = {}
    for stage in ["warmup", "transition", "mature"]:
        vals = alpha_by_stage[stage]
        if vals:
            stage_stats[stage] = {
                "n": len(vals),
                "mean_alpha1": sum(vals) / len(vals),
                "min": min(vals),
                "max": max(vals),
            }
        else:
            stage_stats[stage] = {"n": 0}

    result["alpha_by_stage"] = stage_stats

    # α-Drift: Δ(warmup → mature)
    if stage_stats.get("warmup", {}).get("n", 0) > 0 and \
       stage_stats.get("mature", {}).get("n", 0) > 0:
        result["alpha_drift_warmup_to_mature"] = (
            stage_stats["mature"]["mean_alpha1"]
            - stage_stats["warmup"]["mean_alpha1"]
        )

    # VT1-Detection-Stabilität: vt1_method-Wechsel pro Stage
    if any(r.get("vt1_method", "").strip() for r in rows):
        vt1_changes_by_stage = defaultdict(int)
        prev_method = None
        prev_stage = None
        for r in rows:
            stage = r.get("alpha_maturity_stage", "").strip()
            method = r.get("vt1_method", "").strip()
            if stage not in MATURITY_ORDER:
                continue
            if prev_method and method and method != prev_method:
                vt1_changes_by_stage[stage] += 1
            prev_method = method or prev_method
            prev_stage = stage
        result["vt1_method_changes_by_stage"] = dict(vt1_changes_by_stage)

    result["status"] = "OK"
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="TASK-572: alphaMaturityStage Analyse")
    parser.add_argument("--csv", default=str(CSV_PATH), help="Pfad zur pipeline_results.csv")
    parser.add_argument("--check-columns", action="store_true",
                        help="Nur S80-Spalten-Sanity-Check (kein Maturity-Plot)")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"FEHLER: CSV nicht gefunden: {csv_path}")
        sys.exit(1)

    print(f"Lade: {csv_path}")
    headers, rows = load_csv(csv_path)
    print(f"  → {len(rows)} Zeilen, {len(headers)} Spalten")

    # ── Sanity Check S80-Spalten ──────────────────────────────────────────────
    print("\n=== Sanity-Check S80/S81-Spalten ===")
    sanity = sanity_check_s80_columns(headers, rows)

    has_failure = False
    for col, res in sanity.items():
        status = res["status"]
        marker = "✅" if status == "OK" else ("⚠️ " if status == "WARN" else "❌")
        print(f"  {marker} {col}: {res['detail']}")
        if status in ("FAIL", "MISSING"):
            has_failure = True

    if has_failure:
        print("\n⚠️  SANITY-CHECK FAIL — S80-Commit evtl. ausstehend oder Fehler in Pipeline.")
        print("   Sprint-80-Closure-Gate: Bitte an Orchestrator melden.")
    else:
        print("\n✅ Alle vorhandenen S80-Spalten plausibel.")

    if args.check_columns:
        return

    # ── Maturity-Analyse ─────────────────────────────────────────────────────
    print("\n=== alphaMaturityStage-Analyse ===")
    metrics = analyze_maturity(rows, session_id=csv_path.stem)

    if metrics.get("status") == "MISSING_COLUMN":
        print(f"  ⏳ {metrics['note']}")
        print("     Script-Skeleton bereit — erneut ausführen nach TASK-569-Commit.")
        return

    print(f"  Session: {metrics['session_id']}")

    if metrics.get("time_to_mature_min"):
        print(f"  Zeit bis 'mature': {metrics['time_to_mature_min']:.1f} min "
              f"({metrics['time_to_mature_s']:.0f}s)")
    if metrics.get("time_to_transition_s"):
        print(f"  Zeit bis 'transition': {metrics['time_to_transition_s']/60:.1f} min")
    if metrics.get("note_mature"):
        print(f"  ⚠️  {metrics['note_mature']}")

    print("\n  α₁ pro Stage (mean):")
    for stage in ["warmup", "transition", "mature"]:
        s = metrics["alpha_by_stage"].get(stage, {})
        if s.get("n", 0) > 0:
            print(f"    {stage:12s}: n={s['n']:5d}, mean={s['mean_alpha1']:.4f}, "
                  f"range=[{s['min']:.3f}, {s['max']:.3f}]")
        else:
            print(f"    {stage:12s}: — (keine Daten)")

    if "alpha_drift_warmup_to_mature" in metrics:
        drift = metrics["alpha_drift_warmup_to_mature"]
        print(f"\n  α-Drift warmup→mature: {drift:+.4f} "
              f"({'↑ Zunahme' if drift > 0 else '↓ Abnahme'})")

    if "vt1_method_changes_by_stage" in metrics:
        print("\n  VT1-Methoden-Wechsel pro Stage:")
        for stage, cnt in metrics["vt1_method_changes_by_stage"].items():
            print(f"    {stage:12s}: {cnt} Wechsel")

    print("\nDone.")


if __name__ == "__main__":
    main()
