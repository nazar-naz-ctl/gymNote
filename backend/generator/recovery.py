"""
Fatigue Engine + Weekly Fatigue Manager
════════════════════════════════════════
Оцінка системної втоми вправ (Fatigue Score) та контроль
накопичення важких осьових навантажень (станова тяга, присідання)
між сусідніми днями тижня.

FATIGUE_BY_PATTERN/AXIAL_PATTERNS переїхали в enrichment.py — там
вони "насіннєві" дані для первинного заповнення бази (fatigue,
spine_load — вже прямо на кожній вправі). get_fatigue_score()/
is_axial() нижче — тонкі обгортки "по імені" для випадків, коли під
рукою немає самого об'єкта вправи; деінде в генераторі (engine.py)
ці значення читаються НАПРЯМУ з об'єкта: ex.get("fatigue"),
ex.get("spine_load", 1) >= 5.
"""

_FATIGUE_BY_NAME_CACHE = None


def get_fatigue_score(name: str) -> int:
    """Fatigue Score (1-5) для конкретної вправи — читає з уже
    збагаченої бази (exercises_db), а не з окремого словника."""
    global _FATIGUE_BY_NAME_CACHE
    if _FATIGUE_BY_NAME_CACHE is None:
        from exercises_db import exercises as _all_exercises
        _FATIGUE_BY_NAME_CACHE = {e["name"]: e.get("fatigue", 3) for e in _all_exercises}
    return _FATIGUE_BY_NAME_CACHE.get(name, 3)


def is_axial(name: str) -> bool:
    """Чи є вправа осьовою (навантажує хребет системно) — за полем
    spine_load з бази (spine_load >= 5 відповідає точно тим самим
    п'яти патернам, що раніше були в AXIAL_PATTERNS)."""
    global _FATIGUE_BY_NAME_CACHE  # той самий кеш можна розширити, але простіше окремо
    from exercises_db import exercises as _all_exercises
    for e in _all_exercises:
        if e["name"] == name:
            return e.get("spine_load", 1) >= 5
    return False


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