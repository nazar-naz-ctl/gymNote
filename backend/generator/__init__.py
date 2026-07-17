"""
Generator Engine — генератор програм тренувань GymNote.

Повністю відокремлений від Telegram. Публічний інтерфейс,
яким користується handlers/generator.py:

    from backend.generator import generate_program, format_program
    from backend.generator import program_to_storable, program_from_storable

Внутрішня структура (по Engine, згідно з roadmap):
    split.py              — Split Engine (шаблони днів, спліти)
    volume.py              — Volume Engine (MEV/MAV/MRV, підходи/повтори)
    exercise_selector.py   — Exercise Selection Engine (підбір вправ, патерни)
    engine.py               — оркестратор + суперсети + форматування
    recovery.py             — Fatigue/Weekly Fatigue/Recovery Engine (заглушка)
    validator.py            — Program Validator (заглушка)
    progression.py          — Progression/Session Integration/Adaptive (заглушка)
"""

from .engine import (
    generate_program,
    generate_optimized_program,
    format_program,
    program_to_storable,
    program_from_storable,
    build_supersets,
    SUPERSET_PAIRS,
    GROUP_LABELS,
    MIN_ACCEPTABLE_SCORE,
    MAX_REGENERATION_ATTEMPTS,
)
from .exercise_selector import find_exercises, get_pattern, get_exercise_score
from .volume import filter_by_difficulty, get_sets_reps, MAX_DIFFICULTY_BY_LEVEL
from .recovery import get_fatigue_score, is_axial
from .validator import validate_program
from .focus import generate_focus_workout, format_focus_workout, FOCUS_GROUP_LABELS, HARDCORE_TIERS
from .order import order_exercises
from .primary import select_primary_lift
from .intent import classify_intent
from .priority import boost_volume_factors, priority_score_bonus

all = [
    "generate_program",
    "generate_optimized_program",
    "format_program",
    "program_to_storable",
    "program_from_storable",
    "build_supersets",
    "SUPERSET_PAIRS",
    "GROUP_LABELS",
    "MIN_ACCEPTABLE_SCORE",
    "MAX_REGENERATION_ATTEMPTS",
    "find_exercises",
    "get_pattern",
    "get_exercise_score",
    "filter_by_difficulty",
    "get_sets_reps",
    "MAX_DIFFICULTY_BY_LEVEL",
    "get_fatigue_score",
    "is_axial",
    "validate_program",
    "generate_focus_workout",
    "format_focus_workout",
    "FOCUS_GROUP_LABELS",
    "HARDCORE_TIERS",
    "order_exercises",
    "select_primary_lift",
    "classify_intent",
    "boost_volume_factors",
    "priority_score_bonus",
]


# ══════════════════════════════════════════════════════
# EXERCISE DATABASE 2.0 — збагачення бази метаданими
# ══════════════════════════════════════════════════════
# Виконується ОДИН РАЗ, тут, у самому кінці файлу — до цього моменту
# exercise_selector.py і recovery.py вже повністю завантажені
# (тому get_pattern/get_fatigue_score точно доступні), а exercises_db.py
# теж вже завантажений раніше (його імпортував exercise_selector.py
# на самому початку). Імпорт тут, а не на початку exercises_db.py,
# свідомо — щоб уникнути циклічного імпорту.
try:
    from exercises_db import exercises as _all_exercises
    from .enrichment import enrich_all

    enrich_all(_all_exercises)
except Exception as _enrich_error:  # noqa: BLE001
    # Збагачення бази — не критична для роботи генератора функція
    # (генератор і так рахує ці речі сам, окремо). Якщо тут щось
    # піде не так — краще змовчати і не блокувати старт бота, ніж
    # впасти через непринципову деталь.
    import logging
    logging.getLogger(__name__).warning(f"Не вдалося збагатити базу вправ метаданими: {_enrich_error}")