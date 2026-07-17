"""
Focus Workout Engine
═════════════════════
Тренування на одну або кілька конкретних груп м'язів — доповнення
до повних сплітів (SPLITS/DAY_STRUCTURES). Структура дня будується
динамічно під обрані групи й рівень інтенсивності (1-4: просте →
хардкорне), а не береться з готового шаблону.

Повністю перевикористовує вже наявну інфраструктуру: Exercise
Selection Engine (find_exercises — той самий Compatibility/Score
Engine), Volume Engine (щоб навіть Хардкор не переліз за MRV).
"""

from collections import defaultdict

from .exercise_selector import find_exercises
from .volume import VOLUME_LANDMARKS, get_sets_reps, real_muscle


# Пункти меню, які показуємо користувачу
FOCUS_GROUP_LABELS = {
    "груди": "Груди",
    "спина": "Спина",
    "плечі": "Плечі",
    "біцепс": "Біцепс",
    "трицепс": "Трицепс",
    "квадрицепс": "Квадрицепс",
    "біцепс стегна": "Задня поверхня стегна",
    "сідниці": "Сідниці",
    "прес": "Прес",
    "литки": "Литки",
    "трапеція": "Трапеція",
}

# "Спина" і "Плечі" в меню — це не один реальний ключ м'язової групи
# в базі, а комбінація кількох (для ширшого вибору вправ)
FOCUS_GROUP_EXPANSION = {
    "спина": ["спина_ширина", "спина_товщина"],
    "плечі": ["плечі", "задні дельти"],
}

# 4 рівні інтенсивності: скільки слотів (тип вправи, кількість)
# на КОЖНУ обрану групу м'язів
HARDCORE_TIERS = {
    1: {"label": "🟢 Просте",  "slots": [("base", 2)]},
    2: {"label": "🟡 Середнє", "slots": [("base", 2), ("isolation", 2)]},
    3: {"label": "🟠 Важке",   "slots": [("base", 2), ("assist", 2), ("isolation", 2)]},
    4: {"label": "🔴 Хардкор", "slots": [("base", 2), ("assist", 2), ("isolation", 3)]},
}


def generate_focus_workout(muscle_groups: list, equipment: list, level: int, hardcore: int, goal: str = "маса", priority_pattern: str = None) -> dict:
    """
    muscle_groups — список пунктів меню (ключі FOCUS_GROUP_LABELS),
    напр. ["біцепс", "трицепс"].
    priority_pattern — опційний тонший акцент УСЕРЕДИНІ обраних груп
    (напр. "incline_press" для "верх грудей", коли muscle_groups
    містить "груди"). У Focus Workout сама группа вже й так у
    пріоритеті (це весь сенс фічі) — priority_pattern лише додає
    точності всередині неї.
    Повертає один "день" у тому самому форматі, що й звичайні дні
    generate_program: {"name": ..., "exercises": [...], "note": ""}.
    """
    equipment = list(equipment)
    if "власна вага" not in equipment:
        equipment.append("власна вага")

    tier = HARDCORE_TIERS.get(hardcore, HARDCORE_TIERS[2])

    used_names = set()
    used_patterns = set()
    family_counts = {}
    day_used_names = set()

    exercises = []
    sets_by_real_muscle = defaultdict(int)

    expanded_groups = []
    for mg in muscle_groups:
        expanded_groups.extend(FOCUS_GROUP_EXPANSION.get(mg, [mg]))

    for muscle_group in expanded_groups:
        for ex_type, count in tier["slots"]:
            found = find_exercises(
                muscle_group=muscle_group,
                ex_type=ex_type,
                equipment=equipment,
                level=level,
                goal=goal,
                used_names=used_names,
                count=count,
                used_patterns=used_patterns,
                avoid_today=day_used_names,
                family_counts=family_counts,
                priority_muscle=muscle_group,
                priority_pattern=priority_pattern,
            )
            day_used_names.update(e["name"] for e in found)

            sets, reps = get_sets_reps(ex_type, goal, level)

            for ex in found:
                ex["sets"] = sets
                ex["reps"] = reps
                from .intent import classify_intent
                ex["intent"] = classify_intent(ex_type, reps)
                ex["ex_type"] = ex_type
                ex["_group"] = muscle_group
                sets_by_real_muscle[real_muscle(muscle_group)] += sets

            exercises.extend(found)

    # Навіть на Хардкор рівні не даємо перевищити MRV — підрізаємо
    # пропорційно, якщо накопичилось забагато підходів на одну
    # реальну м'язову групу.
    for group_key, total in sets_by_real_muscle.items():
        landmarks = VOLUME_LANDMARKS.get(group_key)
        if not landmarks or total <= landmarks["MRV"]:
            continue
        factor = landmarks["MRV"] / total
        for ex in exercises:
            if real_muscle(ex["_group"]) == group_key:
                ex["sets"] = max(1, round(ex["sets"] * factor))

    from .order import order_exercises
    from .primary import select_primary_lift
    exercises = order_exercises(exercises)
    # Перша обрана користувачем група — розумний дефолт пріоритету
    # для Primary Lift, коли обрано кілька груп одразу (напр.
    # Біцепс+Трицепс — головною логічно стає вправа на Біцепс,
    # бо його обрали першим)
    select_primary_lift(exercises, priority_muscle=expanded_groups[0] if expanded_groups else None, priority_pattern=priority_pattern)

    if hardcore >= 3:
        from .engine import build_supersets
        exercises = build_supersets(exercises)

    label = tier["label"]
    groups_text = " + ".join(FOCUS_GROUP_LABELS.get(m, m) for m in muscle_groups)

    return {
        "name": f"{label} — {groups_text}",
        "exercises": exercises,
        "note": "",
    }


def format_focus_workout(day: dict, muscle_groups: list, hardcore: int, equipment: list) -> str:
    """Форматує фокус-тренування в текст. Не переплутати з format_program —
    тут навмисно інша шапка (без \"Днів\", це не багатоденна програма)."""
    from .engine import GROUP_LABELS

    tier = HARDCORE_TIERS.get(hardcore, HARDCORE_TIERS[2])
    groups_text = ", ".join(FOCUS_GROUP_LABELS.get(m, m) for m in muscle_groups)

    header = (
        f"🎯 <b>Фокус-тренування</b>\n\n"
        f"💪 Групи: {groups_text}\n"
        f"⚡ Інтенсивність: {tier['label']}\n"
        f"🏋️ Обладнання: {', '.join(equipment)}\n"
        f"━━━━━━━━━━━━━━━━\n"
    )

    text = header
    prev_group = None
    exs = day["exercises"]
    i = 0
    while i < len(exs):
        ex = exs[i]
        group = ex.get("_group")
        if group != prev_group:
            label = GROUP_LABELS.get(group, group)
            if label:
                text += f"\n<i>— {label} —</i>\n"
        prev_group = group

        sid = ex.get("superset_id")
        if sid is not None and i + 1 < len(exs) and exs[i + 1].get("superset_id") == sid:
            partner = exs[i + 1]
            partner_group = partner.get("_group")
            if partner_group and partner_group != group:
                g1 = GROUP_LABELS.get(group, group)
                g2 = GROUP_LABELS.get(partner_group, partner_group)
                text += (
                    f"🔗 <b>Суперсет</b> ({g1} + {g2}, без відпочинку):\n"
                    f"   1) {ex['name']} — {ex['sets']}×{ex['reps']}\n"
                    f"   2) {partner['name']} — {partner['sets']}×{partner['reps']}\n"
                )
            else:
                text += (
                    "🔗 <b>Суперсет</b> (без відпочинку між вправами):\n"
                    f"   1) {ex['name']} — {ex['sets']}×{ex['reps']}\n"
                    f"   2) {partner['name']} — {partner['sets']}×{partner['reps']}\n"
                )
            i += 2
            continue

        marker = "🎯 " if ex.get("is_primary") else "• "
        text += f"{marker}{ex['name']} — {ex['sets']}×{ex['reps']}\n"
        i += 1

    if not exs:
        text += "\n❌ Не вдалося знайти вправи для цього поєднання. Спробуй додати обладнання.\n"

    return text
