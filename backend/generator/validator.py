"""
Program Validator
══════════════════
Фінальна перевірка вже згенерованої програми — не втручається в
процес генерації, лише оцінює результат і дає список зауважень.
Призначено для ВНУТРІШНЬОГО тестування/логів — не показується
кінцевому користувачеві в боті.

Використання (наприклад, з debug-скрипта під час тестування):

    from backend.generator import generate_program
    from backend.generator.validator import validate_program

    program = generate_program('зал', ['штанга','гантелі'], 'маса', 3, 5)
    report = validate_program(program, level=3, equipment=['штанга','гантелі'])
    print(report['score'], report['issues'])
"""

from .exercise_selector import get_pattern
from .volume import MAX_DIFFICULTY_BY_LEVEL
from .coverage import compute_muscle_coverage, MIN_COVERAGE_FOR_PENALTY, MUSCLE_FUNCTIONS
from .intelligence import compute_intelligence_score

# Патерни, що вважаються "штовхаючими" (push) і "тягнучими" (pull)
# рухами — для перевірки балансу навантаження за тиждень.
PUSH_PATTERNS = {
    "horizontal_press", "incline_press", "decline_press", "vertical_press",
    "tricep_extension", "tricep_dip",
}
PULL_PATTERNS = {
    "horizontal_pull", "vertical_pull", "vertical_pull_explosive", "upright_row",
    "rear_delt_fly", "bicep_curl", "bicep_curl_isolated", "shrug",
    "pullover", "lat_pullover",
}

# Validator 2.0 — Joint Balance: який тип суглоба переважно
# навантажує кожен патерн (для перевірки, чи не перевантажені одні
# й ті ж суглоби весь тиждень поспіль)
JOINT_TYPE_BY_PATTERN = {
    "squat_bilateral": "коліна", "squat_unilateral": "коліна", "squat_machine": "коліна",
    "lunge_unilateral": "коліна", "leg_extension": "коліна", "squat_explosive": "коліна",
    "leg_curl": "коліна",
    "vertical_press": "плечі", "horizontal_press": "плечі", "incline_press": "плечі",
    "decline_press": "плечі", "lateral_raise": "плечі", "front_raise": "плечі",
    "tricep_extension": "лікті", "bicep_curl": "лікті",
    "hip_hinge_deadlift": "хребет/таз", "hip_hinge": "хребет/таз", "hip_thrust": "хребет/таз",
}

# Validator 2.0 — Compound/Isolation: цільове співвідношення
# (компаунд-сети / усі сети) залежно від цілі користувача
TARGET_COMPOUND_RATIO = {
    "сила": 0.65,
    "маса": 0.55,
    "рельєф": 0.45,
    "схуднення": 0.40,
    "витривалість": 0.35,
}
COMPOUND_RATIO_TOLERANCE = 0.25


def validate_program(program: dict, level: int, equipment: list, goal: str = None) -> dict:
    """
    Перевіряє вже згенеровану програму й повертає:
    {"score": 0-100, "issues": [опис проблем], "push_sets": ..., "pull_sets": ...,
     "quad_sets": ..., "ham_sets": ..., "diversity_by_day": {...},
     "joint_totals": {...}, "compound_ratio": ...}
    """
    issues = []
    score = 100

    push_sets = 0
    pull_sets = 0
    quad_sets = 0
    ham_sets = 0
    compound_sets = 0
    isolation_sets = 0
    joint_totals = {}
    diversity_by_day = {}
    equip_set = set(equipment)
    max_diff = MAX_DIFFICULTY_BY_LEVEL.get(level, 5)

    for day_num, day in program.items():
        seen_today = set()
        day_patterns = set()
        day_exercise_count = 0

        for ex in day.get("exercises", []):
            name = ex["name"]
            pattern = ex.get("movement_pattern") or get_pattern(name)
            sets = ex.get("sets", 0)
            group = ex.get("_group")
            day_exercise_count += 1
            if pattern:
                day_patterns.add(pattern)

            if pattern in PUSH_PATTERNS:
                push_sets += sets
            elif pattern in PULL_PATTERNS:
                pull_sets += sets

            if group == "квадрицепс":
                quad_sets += sets
            elif group == "біцепс стегна":
                ham_sets += sets

            # Compound/Isolation (Validator 2.0)
            if ex.get("compound"):
                compound_sets += sets
            else:
                isolation_sets += sets

            # Joint Balance (Validator 2.0) — сумуємо joint_fatigue
            # за типом суглоба за весь тиждень
            joint_type = JOINT_TYPE_BY_PATTERN.get(pattern)
            if joint_type:
                joint_totals[joint_type] = joint_totals.get(joint_type, 0) + ex.get("joint_fatigue", 1) * sets

            # Обладнання — вправа має підходити хоч під один з наявних предметів
            ex_equipment = set(ex.get("equipment", []))
            if ex_equipment and not (ex_equipment & equip_set):
                issues.append(f"День {day_num}: «{name}» не відповідає обладнанню користувача")
                score -= 5

            # Складність не має перевищувати межу для рівня
            if ex.get("difficulty", 3) > max_diff:
                issues.append(f"День {day_num}: «{name}» занадто складна для рівня {level}")
                score -= 5

            # Дублікат у межах одного дня (має бути неможливим після Фази 2,
            # але валідатор перевіряє незалежно, як остання лінія захисту)
            if name in seen_today:
                issues.append(f"День {day_num}: «{name}» повторюється в межах одного дня")
                score -= 10
            seen_today.add(name)

        # Diversity Score (Validator 2.0) — скільки РІЗНИХ рухових
        # патернів у дні відносно кількості вправ. Низький показник
        # означає, що багато вправ дня діють на тіло дуже подібно
        # (навіть якщо формально різні назви).
        if day_exercise_count > 0:
            diversity_ratio = len(day_patterns) / day_exercise_count
            diversity_by_day[day_num] = round(diversity_ratio, 2)
            if diversity_ratio < 0.5:
                issues.append(
                    f"День {day_num}: низька різноманітність рухів "
                    f"({len(day_patterns)} унікальних патернів на {day_exercise_count} вправ)"
                )
                score -= 5

    if push_sets or pull_sets:
        total = push_sets + pull_sets
        ratio = push_sets / total
        if ratio > 0.65 or ratio < 0.35:
            issues.append(
                f"Дисбаланс Push/Pull за тиждень: {push_sets} push проти {pull_sets} pull підходів"
            )
            score -= 10

    if quad_sets or ham_sets:
        total = quad_sets + ham_sets
        ratio = quad_sets / total
        if ratio > 0.7 or ratio < 0.3:
            issues.append(
                f"Дисбаланс Квадрицепс/Задня поверхня стегна: {quad_sets} проти {ham_sets} підходів"
            )
            score -= 10

    # Joint Balance — чи не перевантажений один тип суглоба явно
    # більше за інші за весь тиждень
    compound_ratio = None
    if joint_totals and len(joint_totals) > 1:
        max_joint = max(joint_totals, key=joint_totals.get)
        max_value = joint_totals[max_joint]
        others_avg = sum(v for k, v in joint_totals.items() if k != max_joint) / (len(joint_totals) - 1)
        if others_avg > 0 and max_value > others_avg * 2.5:
            issues.append(
                f"Дисбаланс навантаження на суглоби за тиждень: «{max_joint}» "
                f"навантажені значно більше за решту ({joint_totals})"
            )
            score -= 5

    # Compound/Isolation — чи відповідає цілі користувача
    if goal and (compound_sets or isolation_sets):
        total = compound_sets + isolation_sets
        compound_ratio = round(compound_sets / total, 2)
        target = TARGET_COMPOUND_RATIO.get(goal)
        if target is not None and abs(compound_ratio - target) > COMPOUND_RATIO_TOLERANCE:
            issues.append(
                f"Compound/Isolation не відповідає цілі «{goal}»: "
                f"{int(compound_ratio*100)}% compound (орієнтир ~{int(target*100)}%)"
            )
            score -= 5

    # Muscle Coverage Engine — чи покриті всі функціональні ролі
    # кожної тренованої групи м'язів за весь тиждень
    coverage = compute_muscle_coverage(program)
    for group, data in coverage.items():
        if data["score"] < MIN_COVERAGE_FOR_PENALTY:
            missing_labels = ", ".join(sorted(data["missing"]))
            issues.append(
                f"Недостатнє покриття функціональних ролей «{group}» "
                f"({int(data['score']*100)}%) — бракує: {missing_labels}"
            )
            score -= 5

    score = max(0, min(100, score))
    result = {
        "score": score,
        "issues": issues,
        "push_sets": push_sets,
        "pull_sets": pull_sets,
        "quad_sets": quad_sets,
        "ham_sets": ham_sets,
        "diversity_by_day": diversity_by_day,
        "joint_totals": joint_totals,
        "compound_ratio": compound_ratio,
        "muscle_coverage": coverage,
    }

    # Workout Intelligence Engine — об'єднує всі показники вище в
    # один зважений Intelligence Score (окремо від штрафного "score")
    intelligence = compute_intelligence_score(result, program)
    result["intelligence_score"] = intelligence["intelligence_score"]
    result["intelligence_breakdown"] = intelligence["breakdown"]

    return result
