"""
Muscle Coverage Engine (Етап 1: лише оцінка, версія 1.1 — з вагою обсягу)
═══════════════════════════════════════════════════════════════════════════
Відповідає не на питання "чи вправи різні?" (це Exercise Similarity
Engine, вже значною мірою покритий Compatibility Engine + Diversity
Score), а на інше: "чи м'яз отримав УСІ необхідні типи стимулу за
тиждень, і в достатньому ОБСЯЗІ?".

Приклад: три різні жими на груди (Similarity Engine їх не заб'є —
вони формально різні) все одно можуть залишити програму однобокою,
якщо жодного разу за тиждень не було розтяжки/ізоляції (chest_fly)
чи жиму під іншим кутом.

v1.1 (обсяг): версія 1.0 рахувала лише БІНАРНУ присутність патерну
(є/нема), незалежно від кількості сетів. Це давало хибно високий
Coverage Score у випадках типу "верх грудей 18 сетів, низ 3 сети,
розводка 0" — усі три патерни могли формально числитись "покритими",
хоча реальний розподіл стимулу вкрай нерівномірний. Тепер кожен
очікуваний патерн отримує оцінку 0.0-1.0 залежно від його частки в
загальному обсязі групи, порівняно з "ідеальною" рівномірною часткою
(1 / кількість очікуваних патернів groupи). Патерн з часткою на рівні
або вище ідеальної отримує повний бал (1.0) — не карається за
перевиконання, лише за недобір.

MUSCLE_FUNCTIONS визначає очікувані "функціональні ролі" (рухові
патерни) для кожної тренованої групи м'язів.

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
    ролі (патерни) реально присутні, скільки сетів припадає на кожну,
    яких бракує, і зважений Coverage Score (0.0-1.0).

    Повертає {група: {"covered": {...}, "missing": {...},
                       "pattern_scores": {патерн: 0.0-1.0},
                       "score": 0.0-1.0}}
    Групи, для яких MUSCLE_FUNCTIONS не визначено, або які взагалі
    не тренувались цього тижня, пропускаються.
    """
    sets_by_group_pattern = {}

    for day in program.values():
        for ex in day.get("exercises", []):
            group = ex.get("_group")
            pattern = ex.get("movement_pattern")
            if not group or not pattern:
                continue
            sets = ex.get("sets", 0)
            sets_by_group_pattern.setdefault(group, {})
            sets_by_group_pattern[group][pattern] = sets_by_group_pattern[group].get(pattern, 0) + sets

    coverage = {}
    for group, expected in MUSCLE_FUNCTIONS.items():
        pattern_sets = sets_by_group_pattern.get(group)
        if not pattern_sets:
            continue  # групу взагалі не тренували цього тижня — нема що оцінювати

        # Рахуємо загальний обсяг ЛИШЕ по очікуваних патернах цієї
        # групи (сети на патерни поза MUSCLE_FUNCTIONS не впливають
        # на пропорцію — вони вже не про "функціональну роль")
        total_sets = sum(pattern_sets.get(p, 0) for p in expected)
        if total_sets == 0:
            continue

        ideal_share = 1.0 / len(expected)
        pattern_scores = {}
        covered = set()
        missing = set()

        for pattern in expected:
            actual_sets = pattern_sets.get(pattern, 0)
            if actual_sets == 0:
                pattern_scores[pattern] = 0.0
                missing.add(pattern)
                continue
            actual_share = actual_sets / total_sets
            # Не карається за перевиконання — лише капується на 1.0
            pattern_score = min(1.0, actual_share / ideal_share)
            pattern_scores[pattern] = round(pattern_score, 2)
            covered.add(pattern)

        score = sum(pattern_scores.values()) / len(expected)
        coverage[group] = {
            "covered": covered,
            "missing": missing,
            "pattern_scores": pattern_scores,
            "score": round(score, 2),
        }

    return coverage