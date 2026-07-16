"""
Exercise Database 2.0
══════════════════════
Збагачує кожен запис вправи (з exercises_db.py) вісьмома новими
полями метаданих, похідними від уже наявних даних (руховий патерн,
складність, обладнання, ціль):

    movement_pattern — руховий патерн (той самий, що вже давно
                       використовується через get_pattern(), тепер
                       записаний прямо на вправі)
    fatigue          — Fatigue Score 1-5 (той самий, що вже є в
                       recovery.py, тепер прямо на вправі)
    compound         — чи багатосуглобовий рух (True/False)
    unilateral       — чи однобічна вправа (True/False)
    spine_load       — навантаження на хребет, 1-5
    stability        — вимога до стабілізації/балансу, 1-5
    skill            — технічна складність виконання, 1-5
    stimulus         — основний тренувальний стимул: "гіпертрофія" /
                       "сила" / "потужність" / "витривалість"

ВАЖЛИВО: це перший крок (Etap 1 з roadmap). Сам генератор (Score
Engine тощо) поки й далі рахує ці ж речі по-своєму через окремі
словники в exercise_selector.py/recovery.py — це свідомо, щоб не
чіпати вже протестований робочий код. Другий крок (Score Engine 2.0)
перепише генератор так, щоб він читав саме ці нові поля з бази,
а не рахував їх окремо — тоді дублювання зникне.
"""

COMPOUND_PATTERNS = {
    "hip_hinge_deadlift", "hip_hinge", "squat_bilateral", "squat_unilateral",
    "squat_machine", "squat_explosive", "lunge_unilateral",
    "horizontal_press", "incline_press", "decline_press", "vertical_press",
    "horizontal_pull", "vertical_pull", "vertical_pull_explosive",
    "hip_thrust", "hip_thrust_unilateral", "olympic_pull", "olympic_press", "carry",
}

SPINE_LOAD_BY_PATTERN = {
    "hip_hinge_deadlift": 5, "squat_bilateral": 5, "squat_machine": 5,
    "olympic_pull": 5, "olympic_press": 5,
    "hip_hinge": 4, "squat_unilateral": 4, "squat_explosive": 4,
    "lunge_unilateral": 4, "carry": 4,
    "horizontal_press": 3, "vertical_press": 3, "horizontal_pull": 3,
    "vertical_pull": 3, "hip_thrust": 3, "upright_row": 3,
    "incline_press": 2, "decline_press": 2, "hip_thrust_unilateral": 2,
    "chest_fly": 2, "shrug": 2,
}
DEFAULT_SPINE_LOAD = 1

HIGH_SKILL_PATTERNS = {"olympic_pull", "olympic_press", "vertical_pull_explosive"}
POWER_PATTERNS = {"olympic_pull", "olympic_press", "squat_explosive", "vertical_pull_explosive"}

STABLE_EQUIPMENT = {"тренажер", "блок", "тренажер Сміта"}
UNSTABLE_EQUIPMENT = {"TRX", "кільця"}


def compute_compound(pattern: str) -> bool:
    return pattern in COMPOUND_PATTERNS


def compute_unilateral(pattern: str) -> bool:
    return bool(pattern) and "unilateral" in pattern


def compute_spine_load(pattern: str) -> int:
    return SPINE_LOAD_BY_PATTERN.get(pattern, DEFAULT_SPINE_LOAD)


def compute_stability(ex: dict, pattern: str) -> int:
    equipment = set(ex.get("equipment", []))
    is_uni = compute_unilateral(pattern)

    if is_uni:
        return 5
    if equipment & UNSTABLE_EQUIPMENT:
        return 4
    if equipment & STABLE_EQUIPMENT:
        return 1
    return 3


def compute_skill(ex: dict, pattern: str) -> int:
    base = ex.get("difficulty", 3)
    if pattern in HIGH_SKILL_PATTERNS:
        base += 1
    return max(1, min(5, base))


def compute_stimulus(ex: dict, pattern: str) -> str:
    goal = ex.get("goal", [])
    if pattern in POWER_PATTERNS:
        return "потужність"
    if "сила" in goal and ex.get("difficulty", 3) >= 3:
        return "сила"
    if "витривалість" in goal or "схуднення" in goal or ex.get("type") == "кардіо":
        return "витривалість"
    return "гіпертрофія"


def enrich_exercise(ex: dict, get_pattern_fn, get_fatigue_fn) -> dict:
    """Мутує вправу на місці, додаючи 8 нових полів. Повертає той самий dict."""
    pattern = get_pattern_fn(ex["name"])

    ex["movement_pattern"] = pattern
    ex["fatigue"] = get_fatigue_fn(ex["name"])
    ex["compound"] = compute_compound(pattern)
    ex["unilateral"] = compute_unilateral(pattern)
    ex["spine_load"] = compute_spine_load(pattern)
    ex["stability"] = compute_stability(ex, pattern)
    ex["skill"] = compute_skill(ex, pattern)
    ex["stimulus"] = compute_stimulus(ex, pattern)
    return ex


def enrich_all(exercises_list: list, get_pattern_fn, get_fatigue_fn) -> None:
    """Збагачує весь список вправ на місці (мутація, без копіювання списку)."""
    for ex in exercises_list:
        enrich_exercise(ex, get_pattern_fn, get_fatigue_fn)