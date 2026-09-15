"""
app/services/verification/confidence_scorer.py

Calculates deterministic data confidence score and maps to confidence tiers.
"""

from __future__ import annotations

import uuid

from app.schemas.verification import (
    FieldVerification,
    VerificationResult,
    VerificationStatus,
)
from app.services.verification.consistency_checker import ConsistencyResult
from app.services.verification.field_completeness import CompletenessResult
from app.services.verification.source_quality import SourceQualityResult
from app.services.verification.verification_rules import (
    COMPLETENESS_WEIGHT,
    CONSISTENCY_WEIGHT,
    HIGH_THRESHOLD,
    MEDIUM_THRESHOLD,
    SOURCE_WEIGHT,
)


class ConfidenceScorer:
    """Combines completeness, source quality, and consistency into a final data confidence score."""

    @classmethod
    def compute(
        cls,
        *,
        task_id: str,
        organization_id: uuid.UUID,
        lead_id: uuid.UUID | None = None,
        completeness: CompletenessResult,
        source_quality: SourceQualityResult,
        consistency: ConsistencyResult,
    ) -> VerificationResult:
        """Compute the weighted data confidence score and return structured VerificationResult.

        Formula:
            Score = (Completeness * 50%) + (Source Quality * 30%) + (Consistency * 20%)
        """
        raw_score = (
            (completeness.weighted_score * COMPLETENESS_WEIGHT)
            + (source_quality.score * SOURCE_WEIGHT)
            + (consistency.score * CONSISTENCY_WEIGHT)
        )
        final_score = int(round(min(100.0, max(0.0, raw_score))))

        # Map to Confidence Tier
        if final_score >= HIGH_THRESHOLD:
            status: VerificationStatus = "HIGH"
        elif final_score >= MEDIUM_THRESHOLD:
            status = "MEDIUM"
        else:
            status = "LOW"

        # Construct structured reasons
        comp_reason = (
            f"{completeness.fields_found} of {completeness.total_fields} "
            f"requested fields available ({completeness.percentage:.0f}%)"
        )

        if source_quality.details.official_website_fields > 0:
            source_reason = "Information primarily sourced from official website pages"
        elif source_quality.details.directory_fields > 0:
            source_reason = "Information sourced from public business directories"
        elif source_quality.details.fields_with_source > 0:
            source_reason = "Public discovery sources available with provenance"
        else:
            source_reason = "Basic discovery data with limited provenance metadata"

        if "POSSIBLE_CONFLICT" in consistency.flags:
            cons_reason = f"Potential field conflicts flagged: {'; '.join(consistency.conflicts)}"
        elif "EMAIL_DOMAIN_MATCH" in consistency.flags:
            cons_reason = "Website and institutional email domain are fully consistent"
        elif "WEAK_CONSISTENCY_SIGNAL" in consistency.flags:
            cons_reason = "Contact and web presence verified with generic provider email"
        else:
            cons_reason = "Cross-field syntax and structure verified without conflicts"

        reasons = {
            "completeness": comp_reason,
            "sources": source_reason,
            "consistency": cons_reason,
        }

        # Build field-level verification map
        field_verifications: dict[str, FieldVerification] = {}
        for fname, is_available in completeness.field_availability.items():
            s_info = source_quality.field_sources.get(fname)
            fv = FieldVerification(
                field_name=fname,
                available=is_available,
                source_present=s_info.source_present if s_info else False,
                source_type=s_info.source_type if s_info else None,
                source_page_type=s_info.source_page_type if s_info else None,
                source_url=s_info.source_url if s_info else None,
                consistency=consistency.field_consistency.get(fname, "NEUTRAL"),
            )
            field_verifications[fname] = fv

        return VerificationResult(
            task_id=task_id,
            organization_id=organization_id,
            lead_id=lead_id,
            status=status,
            score=final_score,
            fields_found=completeness.fields_found,
            total_fields=completeness.total_fields,
            completeness_percentage=completeness.percentage,
            source_quality_score=source_quality.score,
            consistency_score=consistency.score,
            reasons=reasons,
            flags=consistency.flags,
            field_verifications=field_verifications,
            source_quality_details=source_quality.details,
        )
