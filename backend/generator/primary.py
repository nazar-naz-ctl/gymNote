"""
Primary Lift Engine
═════════════════════
Явно визначає ГОЛОВНУ вправу тренування — ту, що відкриває заняття
і отримує найбільший пріоритет.

Primary Lift обирається за найвищим Priority Score серед базових
вправ дня. Якщо задано priority_muscle (Muscle Priority Engine) —
спершу звужує кандидатів до вправ ІМЕННО цієї групи (якщо такі є
серед базових); якщо ні — розглядає всі базові.

Спершу шукає серед БІЛАТЕРАЛЬНИХ вправ — Primary Lift за задумом
тренера майже завжди білатеральна вправа з вільною вагою
(присідання зі штангою, а не пістолетик), навіть якщо пістолетик
технічно складніший і тому міг би виграти за Skill у Priority Score.
Унілатеральні — лише запасний варіант.
"""

from .order import _priority_score
from .priority import priority_score_bonus


def select_primary_lift(exercises: list, priority_muscle: str = None, priority_pattern: str = None) -> dict | None:
    """
    Обирає й позначає Primary Lift дня. Мутує список: рівно одна
    вправа отримує is_primary=True, решта — is_primary=False.

    Повертає обрану вправу (або None, якщо базових вправ немає).
    """
    for ex in exercises:
        ex["is_primary"] = False

    base_candidates = [ex for ex in exercises if ex.get("ex_type") == "base"]
    if not base_candidates:
        return None

    # Muscle Priority Engine: спершу пробуємо звузити до пріоритетної
    # групи — якщо серед базових є хоч одна вправа цієї групи
    if priority_muscle:
        priority_base = [ex for ex in base_candidates if ex.get("_group") == priority_muscle]
        if priority_base:
            base_candidates = priority_base

    # Якщо задано ще й priority_pattern (напр. "верх грудей") — так
    # само твердий фільтр, не м'який бонус. М'який бонус виявився
    # ненадійним: різниця у Fatigue/Spine Load між двома вправами
    # тієї самої групи (Жим лежачи vs Похилий жим) часто більша за
    # бонус, і "акцент" користувача просто губився в шумі.
    if priority_pattern:
        pattern_base = [ex for ex in base_candidates if ex.get("movement_pattern") == priority_pattern]
        if pattern_base:
            base_candidates = pattern_base

    bilateral_base = [ex for ex in base_candidates if not ex.get("unilateral")]
    pool = bilateral_base if bilateral_base else base_candidates

    def _combined_score(ex):
        score = _priority_score(ex)
        if priority_muscle:
            score += priority_score_bonus(ex.get("_group"), ex.get("movement_pattern"), priority_muscle, priority_pattern)
        return score

    primary = max(pool, key=_combined_score)
    primary["is_primary"] = True
    return primary