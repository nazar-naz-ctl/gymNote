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


def validate_program(program: dict, level: int, equipment: list) -> dict:
    """
    Перевіряє вже згенеровану програму й повертає:
    {"score": 0-100, "issues": [опис проблем], "push_sets": ..., "pull_sets": ...,
     "quad_sets": ..., "ham_sets": ...}
    """
    issues = []
    score = 100

    push_sets = 0
    pull_sets = 0
    quad_sets = 0
    ham_sets = 0
    equip_set = set(equipment)
    max_diff = MAX_DIFFICULTY_BY_LEVEL.get(level, 5)

    for day_num, day in program.items():
        seen_today = set()
        for ex in day.get("exercises", []):
            name = ex["name"]
            pattern = get_pattern(name)
            sets = ex.get("sets", 0)
            group = ex.get("_group")

            if pattern in PUSH_PATTERNS:
                push_sets += sets
            elif pattern in PULL_PATTERNS:
                pull_sets += sets

            if group == "квадрицепс":
                quad_sets += sets
            elif group == "біцепс стегна":
                ham_sets += sets

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

    score = max(0, min(100, score))
    return {
        "score": score,
        "issues": issues,
        "push_sets": push_sets,
        "pull_sets": pull_sets,
        "quad_sets": quad_sets,
        "ham_sets": ham_sets,
    }