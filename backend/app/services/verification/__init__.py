"""
app/services/verification package.

Lead data-quality verification, confidence scoring, source quality assessment,
and cross-field consistency checking.
"""

from app.services.verification.confidence_scorer import ConfidenceScorer
from app.services.verification.consistency_checker import (
    ConsistencyResult,
    check_consistency,
)
from app.services.verification.field_completeness import (
    CompletenessResult,
    calculate_field_completeness,
)
from app.services.verification.source_quality import (
    FieldSourceInfo,
    SourceQualityResult,
    assess_source_quality,
)
from app.services.verification.verification_rules import (
    COMPLETENESS_WEIGHT,
    CONSISTENCY_WEIGHT,
    DEFAULT_FIELD_WEIGHTS,
    HIGH_THRESHOLD,
    MEDIUM_THRESHOLD,
    SOURCE_WEIGHT,
)
from app.services.verification.verification_service import VerificationService

__all__ = [
    "VerificationService",
    "ConfidenceScorer",
    "calculate_field_completeness",
    "CompletenessResult",
    "assess_source_quality",
    "SourceQualityResult",
    "FieldSourceInfo",
    "check_consistency",
    "ConsistencyResult",
    "HIGH_THRESHOLD",
    "MEDIUM_THRESHOLD",
    "COMPLETENESS_WEIGHT",
    "SOURCE_WEIGHT",
    "CONSISTENCY_WEIGHT",
    "DEFAULT_FIELD_WEIGHTS",
]
