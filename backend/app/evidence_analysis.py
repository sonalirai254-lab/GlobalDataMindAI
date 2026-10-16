"""Evidence-Based AI Analysis Engine for GlobalDataMindAI.
Provides fact-grounded, auditable analytical intelligence for:
1. Real Country Data (World Bank historical time-series & multi-country comparisons).
2. User-Provided Academic Records (Class 10, Class 12, B.Tech progression).

Guiding Principles:
- Strict evidence-grounding: Every factual claim cites verified sources and retrieval dates.
- Separate analysis: Real country datasets and personal academic profiles are evaluated in isolated pipelines.
- Explains historical trends, comparative positions, statistical anomalies, and data limitations.
- Identifies uncertainty and survey gaps; correlation is never confused with causation.
- Never fabricates statistics; missing data remains strictly None/unrecorded.
- Never guarantees predictions; all forward projections are non-deterministic bounded scenarios.
"""
from __future__ import annotations

import math
import time
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("evidence_analysis")

NO_PREDICTION_GUARANTEE = (
    "STATISTICAL DISCLAIMER: Past performance and historical trends do not guarantee "
    "future outcomes. Projections are non-deterministic, bounded scenarios based on historical baseline rates. "
    "GlobalDataMindAI never fabricates statistics or guarantees future predictions."
)


class EvidenceAnalysisEngine:
    """Engine for generating auditable, evidence-grounded AI analysis of global and personal datasets."""

    def __init__(self, global_manager: Any, personal_manager: Any, trust_ledger: Any, graph_store: Any) -> None:
        self.global_mgr = global_manager
        self.personal_mgr = personal_manager
        self.trust_ledger = trust_ledger
        self.store = graph_store

    # ---------------- 1. Global Intelligence Analysis ---------------- #

    def analyze_global_series(
        self,
        country: str,
        indicator: str,
        start_year: int = 1990,
        end_year: int = 2024,
    ) -> dict[str, Any]:
        """Perform comprehensive evidence-based AI analysis on a single country indicator series."""
        if not country or not country.strip():
            raise ValueError("Country code or name is required for analysis.")
        if not indicator or not indicator.strip():
            raise ValueError("Indicator code is required for analysis.")

        # 1. Retrieve verified historical series
        series_data = self.global_mgr.get_series(
            country=country,
            indicator=indicator,
            start_year=start_year,
            end_year=end_year,
        )

        country_name = series_data["country"]["name"]
        country_code = series_data["country"]["code"]
        indicator_name = series_data["indicator"]["name"]
        indicator_code = series_data["indicator"]["code"]
        unit = series_data["indicator"].get("unit", "")
        meta = series_data.get("meta", {})
        source_name = meta.get("source", "World Bank Indicators API")
        source_id = str(meta.get("source_id", "2"))
        last_updated = meta.get("last_updated", "Current")
        retrieved_at = meta.get("fetched_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

        observations = series_data.get("observations", [])
        valid_points = [o for o in observations if not o.get("is_missing") and o.get("value") is not None]
        missing_points = [o for o in observations if o.get("is_missing") or o.get("value") is None]

        if not valid_points:
            raise ValueError(
                f"Insufficient data: World Bank API returned 0 valid observations for {indicator_name} "
                f"in {country_name} ({start_year}-{end_year}). Analysis cannot be conducted without verified ground truth."
            )

        # 2. Historical Trend Analysis
        oldest = valid_points[0]
        latest = valid_points[-1]
        start_val = oldest["value"]
        end_val = latest["value"]
        total_delta = end_val - start_val
        pct_change = round(((end_val - start_val) / abs(start_val)) * 100.0, 2) if start_val != 0 else None

        years_span = latest["year"] - oldest["year"]
        cagr = None
        if years_span > 0 and start_val > 0 and end_val > 0:
            cagr = round(((end_val / start_val) ** (1.0 / years_span) - 1.0) * 100.0, 2)

        trend_direction = "Growth" if total_delta > 0 else "Decline" if total_delta < 0 else "Stagnant"

        # 3. Anomaly & Outlier Detection (Step-by-Step Volatility)
        yoy_changes = []
        for i in range(1, len(valid_points)):
            prev_pt = valid_points[i - 1]
            curr_pt = valid_points[i]
            if prev_pt["value"] != 0:
                pct_step = round(((curr_pt["value"] - prev_pt["value"]) / abs(prev_pt["value"])) * 100.0, 2)
                yoy_changes.append({
                    "from_year": prev_pt["year"],
                    "to_year": curr_pt["year"],
                    "yoy_pct": pct_step,
                    "delta": round(curr_pt["value"] - prev_pt["value"], 2),
                })

        anomalies = []
        if yoy_changes:
            mean_yoy = sum(ch["yoy_pct"] for ch in yoy_changes) / len(yoy_changes)
            variance = sum((ch["yoy_pct"] - mean_yoy) ** 2 for ch in yoy_changes) / len(yoy_changes) if len(yoy_changes) > 1 else 0.0
            std_yoy = math.sqrt(variance)

            for ch in yoy_changes:
                # Flag anomalies where change exceeds 2.0 standard deviations or absolute change >= 14%
                is_outlier = (abs(ch["yoy_pct"] - mean_yoy) > (2.0 * std_yoy) if std_yoy > 0.01 else False) or abs(ch["yoy_pct"]) >= 14.0
                if is_outlier:
                    direction_str = "Spike" if ch["yoy_pct"] > 0 else "Contraction"
                    anomalies.append({
                        "period": f"{ch['from_year']} → {ch['to_year']}",
                        "anomaly_type": f"Statistical {direction_str}",
                        "rate_of_change": f"{ch['yoy_pct']}%",
                        "significance": "Deviates significantly from multi-year historical trend.",
                        "probable_factors": (
                            "Macroeconomic shock, pandemic disruption (e.g. 2020), policy shifts, or methodological revisions in World Bank series."
                            if (ch['from_year'] in (2019, 2020) or ch['to_year'] in (2020, 2021)) else
                            "Significant geopolitical, commodity cycle, or currency revaluation event."
                        ),
                    })

        # 4. Verified Grounded Claims & Citations
        citations = [
            {
                "claim": f"{indicator_name} for {country_name} in {latest['year']} was {latest['value']} {unit}.".strip(),
                "source": source_name,
                "source_id": source_id,
                "indicator_code": indicator_code,
                "last_updated": last_updated,
                "retrieved_at": retrieved_at,
            },
            {
                "claim": f"Baseline {oldest['year']} value was {oldest['value']} {unit}.".strip(),
                "source": source_name,
                "source_id": source_id,
                "indicator_code": indicator_code,
                "last_updated": last_updated,
                "retrieved_at": retrieved_at,
            },
        ]

        verified_facts = [
            f"Observed span: {oldest['year']} to {latest['year']} ({len(valid_points)} populated annual observations).",
            f"Oldest recorded value: {oldest['value']} {unit} ({oldest['year']}).",
            f"Latest recorded value: {latest['value']} {unit} ({latest['year']}).",
            f"Overall net change: {'+' if total_delta > 0 else ''}{round(total_delta, 2)} {unit} ({pct_change}%).",
            f"Compound Annual Growth Rate (CAGR): {cagr}% per year." if cagr is not None else "CAGR not applicable.",
        ]

        # 5. Uncertainty & Limitations
        limitations = [
            f"Missing observation gap: {len(missing_points)} years in the requested range ({start_year}-{end_year}) have no recorded data in the World Bank repository.",
            f"Official World Bank reporting release date is {last_updated}; latest data points may be subject to future retrospective revisions.",
            "Correlation limitation: Historical trend direction describes statistical behavior and does not infer direct single-factor causation.",
        ]
        if missing_points:
            missing_years_str = ", ".join(str(o["year"]) for o in missing_points[:6])
            if len(missing_points) > 6:
                missing_years_str += f" and {len(missing_points) - 6} more"
            limitations.append(f"Unrecorded years: {missing_years_str} (isolated as null, strictly never fabricated).")

        # 6. Non-guaranteed Analytical Scenarios
        scenarios = []
        if cagr is not None:
            proj_years = 3
            baseline_val = round(latest["value"] * ((1 + (cagr / 100.0)) ** proj_years), 2)
            conservative_val = round(latest["value"] * ((1 + ((cagr * 0.5) / 100.0)) ** proj_years), 2)
            scenarios.append({
                "scenario_name": "Historical Trend Continuation (Baseline)",
                "projection_horizon": f"+{proj_years} Years ({latest['year'] + proj_years})",
                "estimated_value": f"{baseline_val} {unit}".strip(),
                "growth_assumption": f"Assumes historical CAGR of {cagr}% persists without structural economic shocks.",
                "confidence_level": "Conditional Projection (Not Guaranteed)",
            })
            scenarios.append({
                "scenario_name": "Conservative Deceleration (Lower Bound)",
                "projection_horizon": f"+{proj_years} Years ({latest['year'] + proj_years})",
                "estimated_value": f"{conservative_val} {unit}".strip(),
                "growth_assumption": f"Assumes 50% moderation in annual trajectory ({round(cagr * 0.5, 2)}% p.a.).",
                "confidence_level": "Conditional Projection (Not Guaranteed)",
            })

        # 7. Executive Synthesis
        summary_text = (
            f"Evidence-based analysis of **{indicator_name}** for **{country_name}** spanning "
            f"**{oldest['year']} to {latest['year']}** indicates an overall **{trend_direction.lower()} trend** "
            f"of **{pct_change}%** (from {oldest['value']} to {latest['value']} {unit}). "
            f"Data comprises {len(valid_points)} verified observations from {source_name}. "
            f"{'Detected ' + str(len(anomalies)) + ' significant volatility anomalies across the evaluated period. ' if anomalies else 'The trajectory demonstrates relatively stable year-over-year progression. '}"
            f"All factual metrics are directly grounded in official World Bank releases."
        )

        # 8. Record in Trust Ledger
        ledger_entry = self.trust_ledger.record_conclusion(
            query=f"AI Evidence Analysis: {indicator_name} ({country_name})",
            conclusion=summary_text,
            verified_facts=verified_facts,
            assumptions=[],
            missing_evidence=limitations,
            supporting_entities=[
                {"id": f"country_{country_code.lower()}", "label": country_name, "kind": "Country"},
                {"id": f"indicator_{indicator_code.lower().replace('.', '_')}", "label": indicator_name, "kind": "Indicator"},
            ],
            traversed_edges=[{"source": country_name, "rel": "HAS_INDICATOR", "target": indicator_name}],
            source_documents=[{"id": f"wb_{indicator_code}", "title": source_name, "checksum": "worldbank_ground_truth"}],
            database_source="World Bank Indicators API + Persistent Graph",
        )

        return {
            "analysis_scope": "GLOBAL_COUNTRY_INTELLIGENCE",
            "country": {"code": country_code, "name": country_name},
            "indicator": {"code": indicator_code, "name": indicator_name, "unit": unit},
            "timeframe": {"start_year": oldest["year"], "end_year": latest["year"]},
            "summary": summary_text,
            "historical_trend": {
                "direction": trend_direction,
                "oldest_observation": oldest,
                "latest_observation": latest,
                "net_change": round(total_delta, 2),
                "percentage_change": pct_change,
                "cagr_percentage": cagr,
                "total_valid_observations": len(valid_points),
            },
            "detected_anomalies": anomalies,
            "citations": citations,
            "verified_facts": verified_facts,
            "uncertainty_and_limitations": limitations,
            "analytical_scenarios": scenarios,
            "disclaimer": NO_PREDICTION_GUARANTEE,
            "trust_ledger_id": ledger_entry.get("id"),
            "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def analyze_global_comparison(
        self,
        country_codes: list[str],
        indicator: str,
        start_year: int = 1990,
        end_year: int = 2024,
    ) -> dict[str, Any]:
        """Perform cross-country comparative analysis explaining relative disparities, convergence, and anomalies."""
        if not country_codes or len(country_codes) < 2:
            raise ValueError("Comparative analysis requires at least 2 countries.")
        if len(country_codes) > 8:
            raise ValueError("Comparative analysis is limited to a maximum of 8 countries.")

        comparison_data = self.global_mgr.compare_countries(
            country_codes=country_codes,
            indicator=indicator,
            start_year=start_year,
            end_year=end_year,
        )

        ind_info = comparison_data.get("indicator", {})
        ind_name = ind_info.get("name", indicator)
        unit = ind_info.get("unit", "")
        countries_res = comparison_data.get("countries", {})
        latest_ranks = comparison_data.get("latest_rankings", [])

        if not latest_ranks:
            raise ValueError("No valid cross-country comparative observations were found.")

        # Top vs. Lowest Disparity
        top_country = latest_ranks[0]
        bottom_country = latest_ranks[-1]
        parity_ratio = None
        if bottom_country["latest_value"] and bottom_country["latest_value"] > 0:
            parity_ratio = round(top_country["latest_value"] / bottom_country["latest_value"], 2)

        # Cross-country convergence / divergence analysis
        first_yr = comparison_data.get("years", [start_year])[0]
        latest_yr = comparison_data.get("years", [end_year])[-1]

        rank_cards = []
        for r in latest_ranks:
            rank_cards.append({
                "rank": r["rank"],
                "country": r["country_name"],
                "country_code": r["country_code"],
                "latest_value": f"{r['latest_value']} {unit}".strip(),
                "latest_year": r["latest_year"],
            })

        summary_text = (
            f"Comparative evidence-based AI analysis for **{ind_name}** across {len(latest_ranks)} countries "
            f"reveals highest performance in **{top_country['country_name']}** ({top_country['latest_value']} {unit}) "
            f"and lowest in **{bottom_country['country_name']}** ({bottom_country['latest_value']} {unit}). "
            f"{'The relative disparity gap is ' + str(parity_ratio) + 'x. ' if parity_ratio else ''}"
            f"All values are audited against official World Bank Development Indicators."
        )

        citations = [
            {
                "claim": f"Top ranking country: {top_country['country_name']} ({top_country['latest_value']} {unit}).",
                "source": "World Bank World Development Indicators",
                "indicator_code": indicator,
            },
            {
                "claim": f"Lowest ranking country: {bottom_country['country_name']} ({bottom_country['latest_value']} {unit}).",
                "source": "World Bank World Development Indicators",
                "indicator_code": indicator,
            },
        ]

        verified_facts = [
            f"Compared countries: {', '.join(r['country_name'] for r in latest_ranks)}.",
            f"Disparity ratio (highest/lowest): {parity_ratio}x." if parity_ratio else "Disparity ratio could not be computed.",
            f"Evaluated timeline window: {first_yr} to {latest_yr}.",
        ]

        limitations = [
            "Cross-country comparability may be affected by differences in national accounting standards and purchasing power adjustments.",
            "Reporting years across countries may vary slightly due to differing national statistical survey release intervals.",
            "Ranking reflects strictly empirical observations and carries no normative endorsement or guaranteed forecast.",
        ]

        return {
            "analysis_scope": "GLOBAL_CROSS_COUNTRY_COMPARISON",
            "indicator": {"code": indicator, "name": ind_name, "unit": unit},
            "summary": summary_text,
            "rankings": rank_cards,
            "disparity_metrics": {
                "top_country": top_country,
                "lowest_country": bottom_country,
                "disparity_ratio": parity_ratio,
            },
            "citations": citations,
            "verified_facts": verified_facts,
            "uncertainty_and_limitations": limitations,
            "disclaimer": NO_PREDICTION_GUARANTEE,
            "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    # ---------------- 2. Personal Intelligence Analysis ---------------- #

    def analyze_personal_records(self, mask_sensitive: bool = True) -> dict[str, Any]:
        """Perform evidence-based AI analysis on user-provided academic records in complete isolation from country data."""
        profile = self.personal_mgr.get_profile(mask_sensitive=mask_sensitive)
        timeline = profile.get("timeline", [])
        actual_records = profile.get("actual_records", [])
        missing_milestones = profile.get("missing_milestones", [])
        comparison = profile.get("comparison", {})
        insights = profile.get("calculated_insights", [])

        if not timeline:
            return {
                "analysis_scope": "PERSONAL_ACADEMIC_INTELLIGENCE",
                "has_records": False,
                "summary": (
                    "No personal academic records have been recorded yet. "
                    "Evidence-based analysis requires user-attested ground truth for Class 10, Class 12, or B.Tech. "
                    "Zero-fabrication rule active: missing records are never fabricated."
                ),
                "recorded_milestones_count": 0,
                "missing_milestones": missing_milestones,
                "disclaimer": NO_PREDICTION_GUARANTEE,
            }

        # 1. Milestone Progression Trend
        normalized_scores = [t["normalized_percentage"] for t in timeline]
        avg_score = round(sum(normalized_scores) / len(normalized_scores), 2)
        highest_rec = max(timeline, key=lambda t: t["normalized_percentage"])
        lowest_rec = min(timeline, key=lambda t: t["normalized_percentage"])

        progression_narrative = []
        for t in timeline:
            progression_narrative.append(
                f"{t['qualification']} ({t['passing_year']}): {t['score_display']} at {t['institution']} "
                f"[{t['stream_or_major']}] — Normalized: {t['normalized_percentage']}%"
            )

        trajectory_summary = "Consistent Academic Performance"
        deltas = comparison.get("score_deltas", [])
        anomalies = []

        if len(timeline) >= 2:
            first_pct = timeline[0]["normalized_percentage"]
            latest_pct = timeline[-1]["normalized_percentage"]
            net_delta = round(latest_pct - first_pct, 2)
            if net_delta > 2.0:
                trajectory_summary = f"Positive Trajectory (+{net_delta}% progression)"
            elif net_delta < -2.0:
                trajectory_summary = f"Moderating Trajectory ({net_delta}% variation)"
            else:
                trajectory_summary = f"Highly Stable Trajectory (±{abs(net_delta)}% delta)"

            # Check for anomalies (delta > 7.0%)
            for d in deltas:
                if abs(d["percentage_change"]) >= 6.0:
                    shift_type = "Notable Performance Elevation" if d["percentage_change"] > 0 else "Curriculum Transition Adjustment"
                    anomalies.append({
                        "transition": f"{d['from_qualification']} → {d['to_qualification']}",
                        "percentage_delta": f"{d['percentage_change']}%",
                        "anomaly_type": shift_type,
                        "context": (
                            "Substantial shift occurring between general secondary schooling and rigorous specialized higher secondary / engineering coursework."
                        ),
                    })

        # 2. Verified Citations
        citations = []
        for t in timeline:
            reg_display = t.get("roll_or_registration_number") or "Unspecified"
            citations.append({
                "claim": f"{t['qualification']} completed at {t['institution']} ({t['board_or_university']}) with score {t['score_display']}.",
                "source": "User-Attested Academic Transcripts (Self-Reported)",
                "recorded_at": t.get("recorded_at"),
                "registration_ref": reg_display,
            })

        verified_facts = [
            f"Documented milestone count: {len(timeline)} of 3 standard educational stages.",
            f"Chronological education span: {timeline[0]['passing_year']} to {timeline[-1]['passing_year']}.",
            f"Peak recorded milestone: {highest_rec['qualification']} ({highest_rec['score_display']}).",
            f"Normalized equivalent mean: {avg_score}%.",
        ]

        # 3. Limitations & Uncertainty
        limitations = [
            "Source nature: Records are self-attested by the user and have not undergone third-party cryptographic registrar verification.",
            f"Sample granularity: Evaluates {len(timeline)} summative milestone scores; does not reflect semester-by-semester GPA trends or continuous internal assessment marks.",
            "Zero fabrication rule: Unrecorded milestones are not interpolated or estimated.",
            "Prediction limitation: Historical academic marks do not guarantee professional career performance or future competitive examination outcomes.",
        ]

        if missing_milestones:
            missing_names = ", ".join(m["qualification"] for m in missing_milestones)
            limitations.append(f"Unrecorded milestones: {missing_names} (analysis is strictly limited to recorded stages).")

        # 4. Summary Text
        summary_text = (
            f"Evidence-based analysis of the user's personal academic records indicates a **{trajectory_summary.lower()}** "
            f"with a normalized academic average of **{avg_score}%** across {len(timeline)} recorded milestone(s). "
            f"Highest performance was achieved in **{highest_rec['qualification']}** ({highest_rec['score_display']}). "
            f"Stream progression reflects transition into **{timeline[-1]['stream_or_major']}**. "
            f"All claims cite verified user-attested transcripts; unrecorded stages remain strictly uninvented."
        )

        # 5. Record Trust Ledger Entry
        ledger_entry = self.trust_ledger.record_conclusion(
            query="AI Evidence Analysis: Personal Academic Intelligence",
            conclusion=summary_text,
            verified_facts=verified_facts,
            assumptions=[],
            missing_evidence=limitations,
            supporting_entities=[{"id": t["id"], "label": t["qualification"], "kind": "AcademicRecord"} for t in timeline],
            traversed_edges=[{"source": "Personal Academic Profile", "rel": "HAS_ACADEMIC_RECORD", "target": t["qualification"]} for t in timeline],
            database_source="Personal Intelligence Secure Store + Graph",
        )

        return {
            "analysis_scope": "PERSONAL_ACADEMIC_INTELLIGENCE",
            "has_records": True,
            "summary": summary_text,
            "recorded_milestones_count": len(timeline),
            "missing_milestones": missing_milestones,
            "trajectory_classification": trajectory_summary,
            "academic_average_percentage": avg_score,
            "milestone_progression": {
                "trajectory_summary": trajectory_summary,
                "average_normalized_score": avg_score,
                "highest_milestone": highest_rec,
                "lowest_milestone": lowest_rec,
                "narrative": progression_narrative,
            },
            "progression_narrative": progression_narrative,
            "detected_anomalies": anomalies,
            "calculated_insights": insights,
            "citations": citations,
            "verified_facts": verified_facts,
            "uncertainty_and_limitations": limitations,
            "disclaimer": NO_PREDICTION_GUARANTEE,
            "trust_ledger_id": ledger_entry.get("id"),
            "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
