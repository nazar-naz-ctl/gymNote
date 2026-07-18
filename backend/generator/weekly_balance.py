"""
Weekly Balance Engine
════════════════════════
Не нова перевірка, а ОБ'ЄДНАННЯ двох уже наявних речей за весь
тиждень в один Weekly Balance Score:

    Volume Balance    — чи обсяг КОЖНОЇ реально тренованої групи
                        м'язів потрапляє в діапазон MEV-MRV (не
                        замало, не забагато), з тим самим
                        VOLUME_LANDMARKS, що вже використовує
                        Volume Engine
    Fatigue Distribution — чи немає двох днів поспіль з надмірним
                        сумарним системним/суглобовим навантаженням
                        без дня відновлення між ними (той самий
                        принцип, що вже є в Weekly Fatigue Manager,
                        але тепер оцінюється як окремий показник
                        ФАКТИЧНО згенерованої програми, а не лише
                        застосовується як демпфування під час
                        генерації)
"""

from .volume import VOLUME_LANDMARKS, real_muscle


def compute_volume_balance(program: dict) -> dict:
    """
    Для кожної реально тренованої за тиждень групи м'язів — фактичний
    обсяг (сети) і де він потрапляє відносно MEV/MAV/MRV.

    Повертає {група: {"sets": int, "status": "under"/"ok"/"over", "score": 0-100}}
    """
    sets_by_group = {}
    for day in program.values():
        for ex in day.get("exercises", []):
            group = ex.get("_group")
            if not group:
                continue
            key = real_muscle(group)
            sets_by_group[key] = sets_by_group.get(key, 0) + ex.get("sets", 0)

    result = {}
    for group, sets in sets_by_group.items():
        landmarks = VOLUME_LANDMARKS.get(group)
        if not landmarks:
            continue
        mev, mav, mrv = landmarks["MEV"], landmarks["MAV"], landmarks["MRV"]

        if sets < mev:
            status = "under"
            # чим далі нижче MEV — тим гірше
            score = max(0.0, 100.0 * sets / mev) if mev > 0 else 100.0
        elif sets > mrv:
            status = "over"
            overshoot = (sets - mrv) / mrv if mrv > 0 else 1.0
            score = max(0.0, 100.0 - overshoot * 150)
        else:
            status = "ok"
            # найкраще — ближче до MAV
            distance_from_mav = abs(sets - mav) / max(mav, 1)
            score = max(60.0, 100.0 - distance_from_mav * 60)

        result[group] = {"sets": sets, "mev": mev, "mav": mav, "mrv": mrv, "status": status, "score": round(score, 1)}

    return result


def compute_fatigue_distribution(program: dict) -> dict:
    """
    Перевіряє, чи не йдуть підряд (сусідні номери днів) два дні з
    навантаженням, ПОМІТНО вищим за власний середній рівень цього
    тижня — ознака недостатнього розподілу важких навантажень.

    Поріг ВІДНОСНИЙ (не фіксоване число): "важким" вважається день,
    що щонайменше на 15% перевищує середнє навантаження за тиждень.
    Фіксована константа тут не працює — загальний обсяг дня сильно
    залежить від спліту/кількості вправ і легко відрізняється в
    рази між різними програмами, тому те, що "важко" для одного
    користувача, може бути звичайним днем для іншого.

    Повертає {"daily_load": {день: сумарне навантаження}, "score": 0-100,
    "overloaded_pairs": [(день1, день2), ...]}
    """
    daily_load = {}
    for day_num, day in program.items():
        total = sum(ex.get("systemic_fatigue", 2) * ex.get("sets", 0) for ex in day.get("exercises", []))
        daily_load[day_num] = total

    if not daily_load:
        return {"daily_load": {}, "score": 100.0, "overloaded_pairs": []}

    avg_load = sum(daily_load.values()) / len(daily_load)
    threshold = avg_load * 1.15

    sorted_days = sorted(daily_load.keys())
    overloaded_pairs = []
    for i in range(len(sorted_days) - 1):
        d1, d2 = sorted_days[i], sorted_days[i + 1]
        if daily_load[d1] >= threshold and daily_load[d2] >= threshold:
            overloaded_pairs.append((d1, d2))

    score = max(0.0, 100.0 - len(overloaded_pairs) * 25)

    return {"daily_load": daily_load, "score": round(score, 1), "overloaded_pairs": overloaded_pairs}

def compute_weekly_balance_score(program: dict) -> dict:
    """Об'єднує Volume Balance і Fatigue Distribution в один
    Weekly Balance Score (0-100)."""
    volume_balance = compute_volume_balance(program)
    fatigue_distribution = compute_fatigue_distribution(program)

    volume_scores = [v["score"] for v in volume_balance.values()]
    volume_avg = sum(volume_scores) / len(volume_scores) if volume_scores else 100.0

    weekly_balance_score = round(volume_avg * 0.6 + fatigue_distribution["score"] * 0.4, 1)

    return {
        "weekly_balance_score": weekly_balance_score,
        "volume_balance": volume_balance,
        "fatigue_distribution": fatigue_distribution,
    }