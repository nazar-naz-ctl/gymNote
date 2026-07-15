"""
Fatigue Engine + Weekly Fatigue Manager
════════════════════════════════════════
Оцінка системної втоми вправ (Fatigue Score) на основі рухового
патерну, та контроль накопичення важких осьових навантажень
(станова тяга, присідання) між сусідніми днями тижня.
"""

from .exercise_selector import get_pattern

FATIGUE_BY_PATTERN = {
    "hip_hinge_deadlift": 5,
    "squat_bilateral": 5,
    "olympic_pull": 5,
    "olympic_press": 5,
    "vertical_pull_explosive": 5,

    "squat_machine": 4,
    "squat_explosive": 4,
    "squat_unilateral": 4,
    "lunge_unilateral": 4,
    "horizontal_press": 4,
    "vertical_press": 4,
    "horizontal_pull": 4,
    "vertical_pull": 4,
    "hip_thrust": 4,
    "carry": 4,

    "incline_press": 3,
    "decline_press": 3,
    "hip_hinge": 3,
    "leg_curl": 3,
    "leg_extension": 3,
    "hip_thrust_unilateral": 3,
    "upright_row": 3,
    "shrug": 3,
    "chest_fly": 3,
    "pullover": 3,
    "lat_pullover": 3,
    "core_stability": 3,
    "conditioning": 3,

    "lateral_raise": 2,
    "front_raise": 2,
    "rear_delt_fly": 2,
    "bicep_curl": 2,
    "bicep_curl_isolated": 2,
    "tricep_extension": 2,
    "tricep_dip": 2,
    "core_flexion": 2,
    "core_rotation": 2,
    "hip_abduction": 2,
    "hip_adduction": 2,
    "rotation": 2,
    "forearm": 2,

    "calf_raise": 1,
    "neck": 1,
    "mobility": 1,
}

DEFAULT_FATIGUE = 3

AXIAL_PATTERNS = {
    "hip_hinge_deadlift",
    "squat_bilateral",
    "squat_machine",
    "olympic_pull",
    "olympic_press",
}


def get_fatigue_score(name: str) -> int:
    """Fatigue Score (1-5) для конкретної вправи, за її патерном."""
    pattern = get_pattern(name)
    return FATIGUE_BY_PATTERN.get(pattern, DEFAULT_FATIGUE)


def is_axial(name: str) -> bool:
    """Чи є вправа осьовою (навантажує хребет системно)."""
    return get_pattern(name) in AXIAL_PATTERNS


AXIAL_MUSCLE_GROUPS = {"квадрицепс", "спина_товщина", "сідниці", "біцепс стегна"}


def calculate_daily_axial_load(day_keys: list, goal: str, level: int) -> list:
    """Для кожного дня тижня — наближена оцінка сумарного осьового
    навантаження (підходи в base-слотах типово осьових груп)."""
    from .split import DAY_STRUCTURES
    from .volume import get_sets_reps

    loads = []
    for day_key in day_keys:
        template = DAY_STRUCTURES.get(day_key)
        if not template:
            loads.append(0)
            continue
        total = 0
        for muscle_group, ex_type, count in template["structure"]:
            if muscle_group in AXIAL_MUSCLE_GROUPS and ex_type == "base":
                sets, _ = get_sets_reps(ex_type, goal, level)
                total += count * sets
        loads.append(total)
    return loads


def calculate_axial_dampening(day_keys: list, goal: str, level: int, threshold: int = 8) -> list:
    """
    Якщо день з високим осьовим навантаженням йде одразу після
    іншого дня з високим осьовим навантаженням — повертає
    коефіцієнт зменшення (0-1) для підходів ОСЬОВИХ вправ саме
    цього дня, щоб дати ЦНС/хребту трохи більше часу на
    відновлення. Список float у тому ж порядку, що day_keys.
    """
    loads = calculate_daily_axial_load(day_keys, goal, level)
    factors = []
    prev_high = False
    for load in loads:
        is_high = load >= threshold
        factors.append(0.85 if (is_high and prev_high) else 1.0)
        prev_high = is_high
    return factors


# ══════════════════════════════════════════════════════
# COMPATIBILITY ENGINE
# ══════════════════════════════════════════════════════
# Деякі патерни різні за назвою, але біомеханічно однотипні —
# складання їх забагато за один день дає надлишкове повторюване
# навантаження на ту саму ланку (найчастіше поперек), навіть якщо
# формально це "різні" вправи. На відміну від used_patterns (точний
# збіг), тут групуємо схожі патерни в "родину" й обмежуємо разом.
#
# Присідання свідомо НЕ згруповані — кілька варіацій присідань за
# день (штанга/жим ногами/Смітт) — нормальний, навмисний дизайн дня
# ніг, а не надлишок.

PATTERN_FAMILIES = {
    "hip_hinge_deadlift": "hip_hinge_family",
    "hip_hinge": "hip_hinge_family",
}

FAMILY_CAP = {
    "hip_hinge_family": 2,
}


def get_family(pattern: str) -> str | None:
    return PATTERN_FAMILIES.get(pattern)


def family_cap_reached(pattern: str, family_counts: dict) -> bool:
    """Чи вже досягнуто ліміт цієї родини патернів на сьогодні."""
    family = get_family(pattern)
    if not family:
        return False
    return family_counts.get(family, 0) >= FAMILY_CAP.get(family, 999)


def register_family_pick(pattern: str, family_counts: dict) -> None:
    family = get_family(pattern)
    if family:
        family_counts[family] = family_counts.get(family, 0) + 1
