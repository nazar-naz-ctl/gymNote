"""
Generator Engine
════════════════
Оркестратор: з'єднує Split Engine, Volume Engine та
Exercise Selection Engine в один pipeline і формує готову
програму тренувань. Також відповідає за суперсети та
фінальне форматування тексту програми.

Повністю відокремлений від Telegram — не знає нічого про
aiogram, callback_data чи стан діалогу. Викликається з
handlers/generator.py.
"""

from .split import SPLITS, DAY_STRUCTURES
from .volume import get_sets_reps, calculate_weekly_volume, calculate_scale_factors, apply_scale_to_sets
from .exercise_selector import find_exercises
from .recovery import is_axial, calculate_axial_dampening
from .validator import validate_program


# ══════════════════════════════════════════════════════
# СУПЕРСЕТИ
# ══════════════════════════════════════════════════════

SUPERSET_PAIRS = {
    frozenset({"груди", "трицепс"}),
    frozenset({"груди", "біцепс"}),
    frozenset({"спина_ширина", "біцепс"}),
    frozenset({"спина_товщина", "біцепс"}),
    frozenset({"плечі", "трицепс"}),
    frozenset({"плечі", "задні дельти"}),
    frozenset({"квадрицепс", "біцепс стегна"}),
}


def build_supersets(day_exercises: list) -> list:
    """Для рівнів 3-4 об'єднує ізоляційні вправи в суперсети,
    зберігаючи їх на початковій позиції в списку (а не в кінці)."""
    n = len(day_exercises)
    iso_idx = [i for i, e in enumerate(day_exercises) if e.get("ex_type") == "isolation"]

    by_group = {}
    for i in iso_idx:
        g = day_exercises[i].get("_group", "")
        by_group.setdefault(g, []).append(i)

    pairs = []
    groups = list(by_group.keys())
    for gi in range(len(groups)):
        for gj in range(gi + 1, len(groups)):
            g1, g2 = groups[gi], groups[gj]
            if frozenset({g1, g2}) in SUPERSET_PAIRS:
                while by_group[g1] and by_group[g2]:
                    pairs.append((by_group[g1].pop(0), by_group[g2].pop(0)))

    for items in by_group.values():
        while len(items) >= 2:
            pairs.append((items.pop(0), items.pop(0)))

    skip = set()
    anchor_pair = {}
    sid = 1
    for a, b in pairs:
        anchor = min(a, b)
        partner = max(a, b)
        anchor_pair[anchor] = partner
        skip.add(partner)
        day_exercises[a]["superset_id"] = sid
        day_exercises[b]["superset_id"] = sid
        sid += 1

    result = []
    for i in range(n):
        if i in skip:
            continue
        result.append(day_exercises[i])
        if i in anchor_pair:
            result.append(day_exercises[anchor_pair[i]])
    return result


# ══════════════════════════════════════════════════════
# СЕРІАЛІЗАЦІЯ ПРОГРАМИ (для збереження в FSM-стан)
# ══════════════════════════════════════════════════════

def program_to_storable(program: dict) -> list:
    return [{"day_num": k, **v} for k, v in program.items()]


def program_from_storable(data: list) -> dict:
    return {int(item["day_num"]): {kk: vv for kk, vv in item.items() if kk != "day_num"} for item in data}


# ══════════════════════════════════════════════════════
# ГОЛОВНИЙ ОРКЕСТРАТОР
# ══════════════════════════════════════════════════════

def generate_program(location: str, equipment: list, goal: str, level: int, days: int) -> dict:
    # Власна вага завжди доступна незалежно від локації/обладнання —
    # можна додати вправи "на добивання"/памп навіть у залі чи на
    # вулиці з інвентарем. Це робить програми гнучкішими і рятує
    # дні від "порожніх" груп м'язів при мінімальному обладнанні.
    equipment = list(equipment)
    if "власна вага" not in equipment:
        equipment.append("власна вага")

    split_key = SPLITS.get(location, SPLITS["зал"])
    level_splits = split_key.get(level, split_key[1])
    day_keys = level_splits.get(days, level_splits[min(days, max(level_splits.keys()))])

    # Рахуємо тижневий обсяг ОДИН РАЗ, до генерації днів (Volume Engine)
    weekly_volume = calculate_weekly_volume(day_keys, goal, level)
    volume_factors = calculate_scale_factors(weekly_volume)

    # Weekly Fatigue Manager: якщо два дні поспіль мають високе осьове
    # навантаження — трохи зменшуємо підходи осьових вправ другого дня
    axial_factors = calculate_axial_dampening(day_keys, goal, level)

    program = {}
    used_names = set()  # захист від повторів між днями

    for day_num, day_key in enumerate(day_keys, 1):
        used_patterns = set()
        day_used_names = set()  # вправи, вже вибрані СЬОГОДНІ (для Проходу 3)
        family_counts = {}  # Compatibility Engine — лічильник родин патернів за день
        axial_factor_today = axial_factors[day_num - 1]

        template = DAY_STRUCTURES.get(day_key)
        if not template:
            continue

        # День відновлення
        if day_key == "gym_recovery_4":
            program[day_num] = {
                "name": template["name"],
                "exercises": [],
                "note": template.get("note", ""),
            }
            continue

        day_exercises = []

        for muscle_group, ex_type, count in template["structure"]:

            if ex_type in ("abs", "calves"):
                # Для прес і литок — не блокуємо повтори між днями,
                # і не блокуємо патерн (у преса/литок замало патернів,
                # щоб жорстко розділяти — кілька видів скручувань за
                # тренування це нормально)
                local_used = set()
                found = find_exercises(
                    muscle_group=muscle_group,
                    ex_type=ex_type,
                    equipment=equipment,
                    level=level,
                    goal=goal,
                    used_names=local_used,
                    count=count,
                    used_patterns=None,
                )
            else:
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
                )
                day_used_names.update(e["name"] for e in found)

            # Додаємо підходи і повтори — зі скоригованим обсягом (Volume
            # Engine), і додатково демпфуємо осьові вправи, якщо вчора
            # теж було важке осьове навантаження (Weekly Fatigue Manager)
            sets, reps = get_sets_reps(ex_type, goal, level)
            sets = apply_scale_to_sets(sets, muscle_group, volume_factors)
            for ex in found:
                ex_sets = sets
                if is_axial(ex["name"]):
                    ex_sets = max(1, round(sets * axial_factor_today))
                ex["sets"] = ex_sets
                ex["reps"] = reps
                ex["ex_type"] = ex_type
                ex["_group"] = muscle_group

            day_exercises.extend(found)

        if level in (3, 4):
            day_exercises = build_supersets(day_exercises)

        program[day_num] = {
            "name": template["name"],
            "exercises": day_exercises,
            "note": template.get("note", ""),
        }

    return program


# ══════════════════════════════════════════════════════
# PROGRAM OPTIMIZATION ENGINE
# ══════════════════════════════════════════════════════
# Якщо готова програма отримує оцінку Validator нижче порогу —
# перегенеровуємо (генератор все одно частково випадковий, тож
# наступна спроба може вийти краще). Обмежена кількість спроб,
# щоб не зациклитись — беремо найкращу з усіх спроб, навіть якщо
# жодна не досягла порогу.

MIN_ACCEPTABLE_SCORE = 85
MAX_REGENERATION_ATTEMPTS = 3


def generate_optimized_program(
    location: str, equipment: list, goal: str, level: int, days: int,
    min_score: int = MIN_ACCEPTABLE_SCORE,
    max_attempts: int = MAX_REGENERATION_ATTEMPTS,
) -> tuple:
    """
    Генерує програму, перевіряє Validator-ом, і за потреби
    перегенеровує (до max_attempts спроб), якщо оцінка нижча за
    min_score. Повертає (program, report) — найкращу спробу за
    оцінкою, навіть якщо жодна не досягла порогу.
    """
    # Розширюємо обладнання ОДИН РАЗ тут (не всередині generate_program),
    # щоб і генерація, і Validator бачили той самий список — інакше
    # Validator хибно штрафує вправи на власну вагу, які generate_program
    # додав автоматично, а Validator про це "не знав".
    equipment = list(equipment)
    if "власна вага" not in equipment:
        equipment.append("власна вага")

    best_program = None
    best_report = None

    for attempt in range(1, max_attempts + 1):
        program = generate_program(location, equipment, goal, level, days)
        report = validate_program(program, level=level, equipment=equipment)

        if best_report is None or report["score"] > best_report["score"]:
            best_program = program
            best_report = report

        if report["score"] >= min_score:
            break

    return best_program, best_report


# ══════════════════════════════════════════════════════
# ФОРМАТУВАННЯ ТЕКСТУ ПРОГРАМИ
# ══════════════════════════════════════════════════════

GROUP_LABELS = {
    "груди": "Груди",
    "спина_ширина": "Спина (ширина)",
    "спина_товщина": "Спина (товщина)",
    "квадрицепс": "Квадрицепс",
    "біцепс стегна": "Задня поверхня стегна",
    "сідниці": "Сідниці",
    "плечі": "Плечі",
    "задні дельти": "Задні дельти",
    "трапеція": "Трапеція",
    "біцепс": "Біцепс",
    "трицепс": "Трицепс",
    "прес": "Прес",
    "литки": "Литки",
}


def format_program(program: dict, goal: str, level: int, days: int, equipment: list, score: int = None) -> list:
    """Повертає список частин тексту (може бути кілька, якщо довге)"""
    goal_names = {
        "маса": "💪 Набір маси",
        "рельєф": "✂️ Рельєф",
        "сила": "🏋️ Сила",
        "схуднення": "🔥 Схуднення",
        "витривалість": "🏃 Витривалість",
    }
    level_names = {
        1: "🟢 Початківець",
        2: "🟡 Середній",
        3: "🔴 Просунутий",
        4: "🔥 Атлет",
    }

    score_line = f"📊 Якість програми: {score}%\n" if score is not None else ""

    header = (
        f"🤖 <b>Твоя програма тренувань</b>\n\n"
        f"🎯 Ціль: {goal_names.get(goal, goal)}\n"
        f"⚡ Рівень: {level_names.get(level, level)}\n"
        f"📅 Днів: {days}\n"
        f"🏋️ Обладнання: {', '.join(equipment)}\n"
        f"{score_line}"
        f"━━━━━━━━━━━━━━━━\n"
    )

    parts = [header]
    current = header

    for day_num, day_data in program.items():
        day_text = f"\n📌 <b>День {day_num} — {day_data['name']}</b>\n"

        if not day_data["exercises"] and day_data.get("note"):
            day_text += day_data["note"] + "\n"
        else:
            prev_group = None
            exs = day_data["exercises"]
            i = 0
            while i < len(exs):
                ex = exs[i]
                group = ex.get("_group")
                if group != prev_group:
                    label = GROUP_LABELS.get(group, group)
                    if label:
                        day_text += f"\n<i>— {label} —</i>\n"
                prev_group = group

                sid = ex.get("superset_id")
                if sid is not None and i + 1 < len(exs) and exs[i + 1].get("superset_id") == sid:
                    partner = exs[i + 1]
                    partner_group = partner.get("_group")
                    if partner_group and partner_group != group:
                        g1 = GROUP_LABELS.get(group, group)
                        g2 = GROUP_LABELS.get(partner_group, partner_group)
                        day_text += (
                            f"🔗 <b>Суперсет</b> ({g1} + {g2}, без відпочинку):\n"
                            f"   1) {ex['name']} — {ex['sets']}×{ex['reps']}\n"
                            f"   2) {partner['name']} — {partner['sets']}×{partner['reps']}\n"
                        )
                    else:
                        day_text += (
                            "🔗 <b>Суперсет</b> (без відпочинку між вправами):\n"
                            f"   1) {ex['name']} — {ex['sets']}×{ex['reps']}\n"
                            f"   2) {partner['name']} — {partner['sets']}×{partner['reps']}\n"
                        )
                    i += 2
                    continue

                day_text += f"• {ex['name']} — {ex['sets']}×{ex['reps']}\n"
                i += 1

            if day_data.get("note"):
                day_text += f"\n{day_data['note']}\n"

        # Розбиваємо на частини якщо текст великий
        if len(current) + len(day_text) > 3800:
            parts.append(current)
            current = day_text
        else:
            current += day_text

    if current and current != header:
        if current not in parts:
            parts.append(current)
    elif len(parts) == 1:
        parts[0] = current

    tips = {
        1: "\n💡 <b>Поради:</b>\nФокус на техніці. Відпочинок 60-90 сек між підходами.",
        2: "\n💡 <b>Поради:</b>\nПрогресуй вагу щотижня. Відпочинок 90 сек між підходами.",
        3: "\n💡 <b>Поради:</b>\nБазові: 2-3 хв відпочинку. Ізоляція: 60-90 сек. Негативна фаза 2-3 сек.",
        4: "\n💡 <b>Поради:</b>\nБазові: 2-3 хв. Ізоляція: 60-90 сек. 1-2 повт до відмови. Темп 2-3 сек негатив.",
    }
    parts[-1] += tips.get(level, "")

    return parts
