"""
Primary Lift Engine
═════════════════════
Явно визначає ГОЛОВНУ вправу тренування — ту, що відкриває заняття
і отримує найбільший пріоритет.

Зараз Primary Lift обирається за найвищим Priority Score серед
базових вправ дня (той самий Order Engine) — це початковий крок.
Але це вже ОКРЕМЕ, явне поняття (не побічний ефект сортування),
що дозволяє в майбутньому підмінити критерій вибору — наприклад,
коли з'явиться можливість користувача задати акцент тренування
("хочу верх грудей" → Incline Bench стає Primary замість Flat
Bench, навіть якщо Flat має вищий Priority Score).
"""

from .order import _priority_score


def select_primary_lift(exercises: list) -> dict | None:
    """
    Обирає й позначає Primary Lift дня. Мутує список: рівно одна
    вправа отримує is_primary=True, решта — is_primary=False.

    Спершу шукає серед БІЛАТЕРАЛЬНИХ базових вправ (Primary Lift —
    це "головний важкий підйом дня", і за задумом тренера ним майже
    завжди є білатеральна вправа з вільною вагою — присідання зі
    штангою, а не пістолетик, навіть якщо пістолетик технічно
    складніший і тому міг би виграти за Skill у загальному Priority
    Score). Унілатеральні вправи розглядаються лише як запасний
    варіант, якщо білатеральних базових узагалі немає.

    Повертає обрану вправу (або None, якщо базових вправ немає).
    """
    for ex in exercises:
        ex["is_primary"] = False

    base_candidates = [ex for ex in exercises if ex.get("ex_type") == "base"]
    if not base_candidates:
        return None

    bilateral_base = [ex for ex in base_candidates if not ex.get("unilateral")]
    pool = bilateral_base if bilateral_base else base_candidates

    primary = max(pool, key=_priority_score)
    primary["is_primary"] = True
    return primary