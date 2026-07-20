"""
Microcycle Engine (Етап 1: лише оцінка)
═════════════════════════════════════════
Оцінює ФОРМУ ХВИЛІ навантаження на весь тиждень — не окремі сусідні
дні (це вже робить Weekly Fatigue Manager, recovery.py), а загальну
послідовність Важкий/Середній/Легкий по всіх днях разом.

Daily Load Score для дня = зважена сума:
    cns_cost × sets  (нервове навантаження)
  + joint_fatigue × sets × 0.5  (навантаження на суглоби, менша вага)
  + compound_density × 20  (частка компаунд-вправ від усіх вправ дня)

Класифікація дня (High/Medium/Low) — відносна, за порогами до
середнього по тижню (той самий підхід, що вже використаний у
Weekly Balance Engine для Fatigue Distribution): High ≥ 1.15×
середнього, Low ≤ 0.75× середнього, решта — Medium.

Etап 1: лише розрахунок і звіт, без автозаміни. Виправлення (якщо
знайдена погана форма хвилі) — майбутня задача Optimization Engine
через окрему Problem/Strategy, аналогічно тому, як Coverage Engine
спочатку був лише оцінкою, і лише пізніше отримав ReplaceExerciseStrategy.
"""

HIGH_THRESHOLD_FACTOR = 1.15
LOW_THRESHOLD_FACTOR = 0.75

JOINT_WEIGHT = 0.5
COMPOUND_DENSITY_WEIGHT = 20


def compute_daily_load(day: dict) -> float:
    """Daily Load Score для одного дня програми (dict з ключем 'exercises')."""
    exercises = day.get("exercises", [])
    if not exercises:
        return 0.0

    total = 0.0
    compound_count = 0
    for ex in exercises:
        sets = ex.get("sets", 0)
        cns = ex.get("cns_cost", 2)
        joint = ex.get("joint_fatigue", 2)
        total += cns * sets
        total += joint * sets * JOINT_WEIGHT
        if ex.get("compound"):
            compound_count += 1

    compound_density = compound_count / len(exercises)
    total += compound_density * COMPOUND_DENSITY_WEIGHT

    return round(total, 1)


def classify_day(load: float, week_average: float) -> str:
    if week_average <= 0:
        return "Low"
    if load >= week_average * HIGH_THRESHOLD_FACTOR:
        return "High"
    if load <= week_average * LOW_THRESHOLD_FACTOR:
        return "Low"
    return "Medium"


def compute_microcycle_report(program: dict) -> dict:
    """
    Повертає {
        "daily_loads": {day_num: load},
        "daily_categories": {day_num: "High"/"Medium"/"Low"},
        "week_average": float,
        "consecutive_high_pairs": [(day_num1, day_num2), ...],
        "has_wave_shape": bool,   # чи є хоч один не-High день між High-днями
        "microcycle_score": 0-100,
    }
    Дні відновлення (порожній exercises) отримують load=0, category="Low".
    """
    day_nums = sorted(program.keys())
    loads = {d: compute_daily_load(program[d]) for d in day_nums}

    non_zero_loads = [l for l in loads.values() if l > 0]
    week_average = sum(non_zero_loads) / len(non_zero_loads) if non_zero_loads else 0.0

    categories = {d: classify_day(loads[d], week_average) for d in day_nums}

    # Дні поспіль обидва High — це саме те, що Weekly Fatigue Manager
    # мав би вже пом'якшити на рівні підходів; тут лише фіксуємо факт
    consecutive_high_pairs = []
    for i in range(len(day_nums) - 1):
        d1, d2 = day_nums[i], day_nums[i + 1]
        if categories[d1] == "High" and categories[d2] == "High":
            consecutive_high_pairs.append((d1, d2))

    # Форма хвилі: чи є хоч один Medium/Low день МІЖ будь-якими двома
    # High-днями за весь тиждень (не обов'язково сусідніми) — ознака
    # того, що тиждень дає тілу відновитись, а не тримає постійний максимум
    high_days = [d for d in day_nums if categories[d] == "High"]
    has_wave_shape = True
    if len(high_days) >= 2:
        first_high, last_high = high_days[0], high_days[-1]
        between = [categories[d] for d in day_nums if first_high < d < last_high]
        has_wave_shape = any(c != "High" for c in between) if between else True

    # Score: штрафуємо за кожну пару High-поспіль і за відсутність
    # форми хвилі при 2+ важких днях
    score = 100
    score -= len(consecutive_high_pairs) * 15
    if len(high_days) >= 2 and not has_wave_shape:
        score -= 20
    score = max(0, min(100, score))

    return {"daily_loads": loads,
        "daily_categories": categories,
        "week_average": round(week_average, 1),
        "consecutive_high_pairs": consecutive_high_pairs,
        "has_wave_shape": has_wave_shape,
        "microcycle_score": score,
    }