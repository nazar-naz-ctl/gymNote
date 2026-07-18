"""
Volume Engine
═════════════
Контроль тижневого обсягу тренувань (MEV/MAV/MRV) та базова
таблиця (підходи, повтори) залежно від типу вправи/цілі/рівня.
"""

# Цілі тренувань — незалежний від Telegram список
# (у handlers/generator.py callback_data мапиться на ці самі рядки)
GOALS = ["маса", "рельєф", "сила", "схуднення", "витривалість"]

MAX_DIFFICULTY_BY_LEVEL = {1: 2, 2: 3, 3: 4, 4: 5}


def filter_by_difficulty(found: list, level: int) -> list:
    max_diff = MAX_DIFFICULTY_BY_LEVEL.get(level, 5)
    return [e for e in found if e.get("difficulty", 3) <= max_diff]


def get_sets_reps(ex_type: str, goal: str, level: int) -> tuple:
    table = {
        "base": {
            "маса":       {1:(3,"10-12"), 2:(4,"8-10"), 3:(4,"6-8"),  4:(4,"5-8")},
            "сила":       {1:(3,"6-8"),  2:(4,"5-6"),  3:(4,"4-6"),  4:(5,"3-5")},
            "рельєф":     {1:(3,"12-15"),2:(4,"10-12"),3:(4,"10-12"),4:(4,"10-12")},
            "схуднення":  {1:(3,"15-20"),2:(3,"15"),   3:(3,"12-15"),4:(3,"12-15")},
            "витривалість":{1:(3,"20"),  2:(3,"20"),   3:(3,"15-20"),4:(3,"15-20")},
        },
        "assist": {
            "маса":       {1:(3,"10-12"),2:(4,"10"),   3:(3,"8-10"), 4:(3,"8-10")},
            "сила":       {1:(3,"8-10"), 2:(3,"8"),    3:(3,"6-8"),  4:(3,"6-8")},
            "рельєф":     {1:(3,"12-15"),2:(3,"12"),   3:(3,"12"),   4:(3,"12-15")},
            "схуднення":  {1:(3,"15"),   2:(3,"15"),   3:(3,"15"),   4:(3,"15")},
            "витривалість":{1:(3,"20"),  2:(3,"15-20"),3:(3,"15-20"),4:(3,"15-20")},
        },
        "isolation": {
            "маса":       {1:(2,"12-15"),2:(3,"12"),   3:(3,"12-15"),4:(3,"12-15")},
            "сила":       {1:(2,"10-12"),2:(3,"10"),   3:(3,"10-12"),4:(3,"10-12")},
            "рельєф":     {1:(2,"15"),   2:(3,"15"),   3:(3,"15"),   4:(3,"15")},
            "схуднення":  {1:(2,"20"),   2:(3,"20"),   3:(3,"15-20"),4:(3,"15-20")},
            "витривалість":{1:(2,"20"),  2:(3,"20"),   3:(3,"20"),   4:(3,"20")},
        },
        "abs": {g: {l:(3,"15-20") for l in [1,2,3,4]} for g in GOALS},
        "calves": {g: {1:(3,"15-20"),2:(4,"15-20"),3:(5,"15-20"),4:(6,"15-20")} for g in GOALS},
        "cardio": {g: {l:(3,"20 хв") for l in [1,2,3,4]} for g in GOALS},
    }
    t = table.get(ex_type, table["isolation"])
    g = t.get(goal, t.get("маса", {}))
    return g.get(level, (3, "10-12"))


# ══════════════════════════════════════════════════════
# ОБСЯГ ТРЕНУВАНЬ — MEV / MAV / MRV
# ══════════════════════════════════════════════════════
# MEV — мінімальний ефективний обсяг (менше — м'яз майже не росте)
# MAV — оптимальний обсяг для більшості людей
# MRV — максимальний обсяг, вище якого відновлення не встигає
# Значення в підходах на тиждень.

# Деякі "групи" з DAY_STRUCTURES фізично одна й та сама м'язова
# група, розділена лише для точнішого підбору вправ (наприклад
# спина_ширина/спина_товщина обидві навантажують широчайші).
# Тому для обсягу їх рахуємо разом, під одним ключем.
VOLUME_ALIAS = {
    "спина_ширина": "спина",
    "спина_товщина": "спина",
}


def real_muscle(group: str) -> str:
    """Повертає фізичну м'язову групу для обліку обсягу."""
    return VOLUME_ALIAS.get(group, group)


VOLUME_LANDMARKS = {
    "груди":         {"MEV": 8,  "MAV": 14, "MRV": 22},
    "спина":         {"MEV": 10, "MAV": 18, "MRV": 25},
    "квадрицепс":    {"MEV": 8,  "MAV": 14, "MRV": 20},
    "біцепс стегна": {"MEV": 6,  "MAV": 10, "MRV": 16},
    "сідниці":       {"MEV": 4,  "MAV": 10, "MRV": 16},
    "плечі":         {"MEV": 8,  "MAV": 16, "MRV": 22},
    "задні дельти":  {"MEV": 6,  "MAV": 14, "MRV": 20},
    "трапеція":      {"MEV": 4,  "MAV": 10, "MRV": 16},
    "біцепс":        {"MEV": 6,  "MAV": 14, "MRV": 20},
    "трицепс":       {"MEV": 6,  "MAV": 12, "MRV": 18},
    "прес":          {"MEV": 0,  "MAV": 20, "MRV": 35},
    "литки":         {"MEV": 8,  "MAV": 16, "MRV": 25},
}


def calculate_weekly_volume(day_keys: list, goal: str, level: int) -> dict:
    """Рахує сумарний тижневий обсяг (підходи) по кожній м'язовій групі,
    враховуючи, що один day_key може повторюватись кілька разів на тиждень."""
    from .split import DAY_STRUCTURES  # локальний імпорт — уникаємо циклічної залежності

    volume = {}
    for day_key in day_keys:
        template = DAY_STRUCTURES.get(day_key)
        if not template:
            continue
        for muscle_group, ex_type, count in template["structure"]:
            key = real_muscle(muscle_group)
            sets, _ = get_sets_reps(ex_type, goal, level)
            volume[key] = volume.get(key, 0) + count * sets
    return volume


def calculate_scale_factors(volume: dict) -> dict:
    """Для груп, що перевищують MRV — коефіцієнт зменшення (0-1).
    Групи нижче MEV поки не займаємо (factor=1) — це окрема задача.

    Це "м'який", наближений механізм — застосовується через
    apply_scale_to_sets() ще ПІД ЧАС генерації (одна вправа за
    раз, до того як відомо, скільки всього вправ цієї групи
    буде за тиждень). Для гарантованого дотримання MRV
    (жорсткий ліміт) використовується окремий фінальний прохід —
    дивись enforce_mrv() нижче."""
    factors = {}
    for group, total in volume.items():
        lm = VOLUME_LANDMARKS.get(group)
        if not lm or total <= lm["MRV"]:
            factors[group] = 1.0
        else:
            factors[group] = round(lm["MRV"] / total, 3)
    return factors


def apply_scale_to_sets(base_sets: int, muscle_group: str, factors: dict) -> int:
    """Застосовує коефіцієнт корекції до кількості підходів,
    не даючи опуститись нижче 1 підходу."""
    key = real_muscle(muscle_group)
    factor = factors.get(key, 1.0)
    return max(1, round(base_sets * factor))


# ══════════════════════════════════════════════════════
# MRV ENFORCEMENT — фінальна, точна гарантія ліміту
# ══════════════════════════════════════════════════════
# calculate_scale_factors + apply_scale_to_sets — наближений
# механізм: round() застосовується до КОЖНОЇ вправи окремо, в
# момент її генерації, без знання підсумкової суми за весь
# тиждень/тренування. Коли реальне перевищення дрібне відносно
# кількості вправ у групі (напр. треба зняти 1 сет із 21),
# round() повертає ту саму кількість на кожній вправі — і ліміт
# мовчки ігнорується.
#
# enforce_mrv() — жорсткий, точний прохід ПІСЛЯ повної генерації
# (усіх днів тижня разом, або одного фокус-тренування). Рахує
# РЕАЛЬНУ сумарну кількість сетів на групу і, якщо є перевищення,
# знімає його по одному цілому сету за раз із конкретних вправ,
# у порядку пріоритету зняття: isolation → assist → base
# (найменш специфічні для конкретики групи вправи ріжемо
# першими, основні базові — в останню чергу).

EX_TYPE_CUT_PRIORITY = {"isolation": 0, "assist": 1, "base": 2}


def enforce_mrv(exercises: list) -> None:
    """Мутує ex["sets"] на місці. `exercises` — плаский список
    словників-вправ з уже проставленими 'sets', '_group', 'ex_type'.
    Викликач сам вирішує, який зріз передати: всі дні тижня разом
    (generate_program) чи одне фокус-тренування (generate_focus_workout)."""
    sets_by_group = {}
    for ex in exercises:
        group = ex.get("_group")
        if not group:
            continue
        key = real_muscle(group)
        sets_by_group[key] = sets_by_group.get(key, 0) + ex.get("sets", 0)

    for group_key, total in sets_by_group.items():
        landmarks = VOLUME_LANDMARKS.get(group_key)
        if not landmarks or total <= landmarks["MRV"]:
            continue

        excess = total - landmarks["MRV"]
        group_exercises = [ex for ex in exercises if real_muscle(ex.get("_group", "")) == group_key]
        group_exercises.sort(key=lambda e: EX_TYPE_CUT_PRIORITY.get(e.get("ex_type"), 1))

        idx = 0
        steps = 0
        safety_cap = len(group_exercises) * 30 + 100  # запобіжник від зависання
        while excess > 0 and group_exercises and steps < safety_cap:
            ex = group_exercises[idx % len(group_exercises)]
            if ex["sets"] > 1:
                ex["sets"] -= 1
                excess -= 1
            idx += 1
            steps += 1
