"""
Exercise Intent Engine
═════════════════════════
Та сама вправа з різною схемою підходів/повторів виконує РІЗНУ роль
у тренуванні:

    Жим лежачи 5×3 (довгий відпочинок) → Technique
    Жим лежачи 4×6                     → Strength
    Жим лежачи 3×10                    → Hypertrophy
    Жим лежачи 2×20 (до відмови)       → Pump

Тому Intent НЕ можна порахувати один раз і записати на вправу в базі
(як stimulus у Database 2.1) — він залежить від фактичної реп-схеми
в КОНКРЕТНОМУ слоті конкретної згенерованої програми. Рахується
динамічно, одразу після того, як generate_program/generate_focus_workout
призначили sets/reps.

Activation і Deload НЕ визначаються цією версією — для них потрібні
дані, яких зараз немає (окремий тип "розминочного" слоту, чи стан
мезоциклу з Progression Engine). Чесніше повертати None, ніж
вгадувати.
"""

import re


def _parse_reps(reps_str: str) -> float | None:
    """'6-8' -> 7.0, '12-15' -> 13.5, '20' -> 20.0, '20 хв' -> None
    (кардіо, не про Intent у розумінні сили/гіпертрофії)."""
    if not reps_str or "хв" in reps_str:
        return None
    nums = re.findall(r"\d+", reps_str)
    if not nums:
        return None
    nums = [int(n) for n in nums]
    return sum(nums) / len(nums)


def classify_intent(ex_type: str, reps: str) -> str | None:
    """
    Повертає роль конкретного слоту: "Technique" / "Strength" /
    "Hypertrophy" / "Pump", або None, якщо визначити неможливо
    (кардіо, чи взагалі відсутня реп-схема).
    """
    avg_reps = _parse_reps(reps)
    if avg_reps is None:
        return None

    if avg_reps <= 4:
        return "Technique"
    if avg_reps <= 8:
        return "Strength"
    if avg_reps <= 16:
        return "Hypertrophy"
    return "Pump"