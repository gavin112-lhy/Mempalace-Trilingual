"""
Extraction module — re-exports from root-level 3.3.4 modules with i18n support.

The root-level entity_detector.py, entity_registry.py, normalize.py, and
general_extractor.py are the authoritative implementations (with 14-locale
i18n patterns from mempalace-3.3.4).  This package re-exports them so that
existing callers using ``mempalace_tri.extraction`` continue to work.

Usage:
    # Both import styles are equivalent:
    from mempalace_tri.extraction import EntityDetector, detect_entities
    from mempalace_tri.entity_detector import detect_entities, scan_for_detection

    from mempalace_tri.extraction import EntityRegistry
    from mempalace_tri.entity_registry import EntityRegistry

    from mempalace_tri.extraction import TextNormalizer
    from mempalace_tri.normalize import normalize

    from mempalace_tri.extraction import GeneralExtractor
    from mempalace_tri.general_extractor import extract_memories
"""

# -- entity_detector re-exports --
from ..entity_detector import (
    EntityDetector,
    detect_entities,
    confirm_entities,
    scan_for_detection,
    extract_candidates,
    score_entity,
    classify_entity,
)

# -- entity_registry re-export --
from ..entity_registry import EntityRegistry

# -- normalize re-export --
from ..normalize import normalize

# -- general_extractor re-export --
from ..general_extractor import extract_memories


# Backward-compat aliases so existing class-based callers don't break.
class TextNormalizer:
    """Thin wrapper around the normalize module.

    The 3.3.4 normalize.py is function-based (``normalize(path)``) rather
    than class-based.  This wrapper preserves the old API for callers that
    instantiate ``TextNormalizer()``.
    """

    def normalize(self, file_path: str) -> str:
        return normalize(file_path)


class GeneralExtractor:
    """Thin wrapper around the general_extractor module.

    Preserves the old class-based API for callers that instantiate
    ``GeneralExtractor()``.
    """

    def extract_entities(self, text: str) -> list:
        return extract_memories(text)


__all__ = [
    # entity_detector
    "EntityDetector",
    "detect_entities",
    "confirm_entities",
    "scan_for_detection",
    "extract_candidates",
    "score_entity",
    "classify_entity",
    # entity_registry
    "EntityRegistry",
    # normalize
    "normalize",
    "TextNormalizer",
    # general_extractor
    "extract_memories",
    "GeneralExtractor",
]