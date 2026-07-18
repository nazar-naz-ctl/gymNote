"""
Muscle Coverage Engine (Етап 1: лише оцінка)
═══════════════════════════════════════════════
Відповідає не на питання "чи вправи різні?" (це Exercise Similarity
Engine, вже значною мірою покритий Compatibility Engine + Diversity
Score), а на інше: "чи м'яз отримав УСІ необхідні типи стимулу за
тиждень?".

Приклад: три різні жими на груди (Similarity Engine їх не заб'є —
вони формально різні) все одно можуть залишити програму однобокою,
якщо жодного разу за тиждень не було розтяжки/ізоляції (chest_fly)
чи жиму під іншим кутом.

MUSCLE_FUNCTIONS визначає очікувані "функціональні ролі" (рухові
патерни) для кожної тренованої групи м'язів. Coverage Score = яка
частка цих ролей реально присутня в програмі за весь тиждень.

Етап 1 (цей модуль): лише розрахунок і звіт, без автозаміни вправ.
Автозаміна — це вже Optimization Engine 2.0, окремий, набагато
складніший крок (Coverage знаходить прогалину → потрібно знайти
вправу, яка її закриє → перевірити Compatibility/Fatigue/Volume/
Similarity → не зламати порядок → не погіршити інші метрики).
"""

MUSCLE_FUNCTIONS = {
    "груди": {"horizontal_press", "incline_press", "decline_press", "chest_fly"},
    "спина_ширина": {"vertical_pull", "vertical_pull_explosive"},
    "спина_товщина": {"horizontal_pull", "hip_hinge_deadlift", "shrug"},
    "плечі": {"vertical_press", "front_raise", "lateral_raise"},
    "задні дельти": {"rear_delt_fly"},
    "трапеція": {"shrug", "upright_row"},
    "квадрицепс": {"squat_bilateral", "squat_unilateral", "leg_extension", "lunge_unilateral"},
    "біцепс стегна": {"hip_hinge", "leg_curl"},
    "сідниці": {"hip_thrust", "squat_bilateral"},
    "біцепс": {"bicep_curl", "bicep_curl_isolated"},
    "трицепс": {"tricep_extension", "tricep_dip"},
    "прес": {"core_flexion", "core_rotation", "core_stability"},
    "литки": {"calf_raise"},
}

MIN_COVERAGE_FOR_PENALTY = 0.5


def compute_muscle_coverage(program: dict) -> dict:
    """
    Для кожної тренованої за тиждень групи м'язів — які функціональні
    ролі (патерни) реально присутні, яких бракує, і Coverage Score
    (0.0-1.0).

    Повертає {група: {"covered": {...}, "missing": {...}, "score": 0.0-1.0}}
    Групи, для яких MUSCLE_FUNCTIONS не визначено, пропускаються
    (немає з чим порівнювати).
    """
    patterns_by_group = {}

    for day in program.values():
        for ex in day.get("exercises", []):
            group = ex.get("_group")
            pattern = ex.get("movement_pattern")
            if not group or not pattern:
                continue
            patterns_by_group.setdefault(group, set()).add(pattern)

    coverage = {}
    for group, expected in MUSCLE_FUNCTIONS.items():
        if group not in patterns_by_group:
            continue  # групу взагалі не тренували цього тижня — нема що оцінювати
        actual = patterns_by_group[group]
        covered = actual & expected
        missing = expected - actual
        score = len(covered) / len(expected) if expected else 1.0
        coverage[group] = {
            "covered": covered,
            "missing": missing,
            "score": round(score, 2),
        }

    return coverage