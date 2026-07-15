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
]