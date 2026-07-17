"""
Muscle Priority Engine
════════════════════════
Акцент — це НЕ фільтр вправ, а фактор, що перебудовує програму на
кількох рівнях одночасно:

    Volume Engine    — пріоритетна група отримує бонус тижневого
                        обсягу (ближче до MRV, а не просто MAV)
    Score Engine      — вправи пріоритетної групи/патерну отримують
                        додатковий бал при виборі
    Primary Lift      — обирається з переваги для пріоритетної групи
    Exercise Order     — ті самі бали природно піднімають пріоритетні
                        вправи вище в Order Engine (через Score)

Працює для БУДЬ-ЯКОЇ групи м'язів (не хардкожено під конкретну) —
priority_muscle приймає той самий ключ, що вже використовується
всюди в генераторі (напр. "груди", "спина_ширина", "квадрицепс").

priority_pattern — опціональний, тонший акцент УСЕРЕДИНІ групи
(напр. priority_muscle="груди" + priority_pattern="incline_press"
== "хочу верх грудей", а не просто "хочу груди"). Працює лише для
груп, де такий патерн реально існує в базі (верх/низ грудей вже
розрізнені як incline_press/decline_press) — для груп без такого
розрізнення (напр. "біцепс") просто ігнорується.
"""

VOLUME_BOOST_FACTOR = 1.15   # +15% обсягу пріоритетній групі
MAX_VOLUME_FACTOR = 1.3      # не більше +30% сумарно, навіть якщо група й так недовантажена

SCORE_BONUS_GROUP = 1.5      # бонус Score Engine за співпадіння групи
SCORE_BONUS_PATTERN = 2.0    # додатковий (сильніший) бонус за співпадіння патерну


def boost_volume_factors(volume_factors: dict, priority_muscle: str, real_muscle_fn) -> dict:
    """Підвищує коефіцієнт обсягу для пріоритетної групи (Volume Engine).
    Не мутує вхідний dict — повертає новий."""
    if not priority_muscle:
        return volume_factors
    key = real_muscle_fn(priority_muscle)
    boosted = dict(volume_factors)
    current = boosted.get(key, 1.0)
    boosted[key] = min(MAX_VOLUME_FACTOR, current * VOLUME_BOOST_FACTOR)
    return boosted


def priority_score_bonus(muscle_group: str, pattern: str, priority_muscle: str, priority_pattern: str = None) -> float:
    """
    Бонус для Score Engine. muscle_group/pattern — контекст вправи,
    яку зараз оцінюємо (з find_exercises), priority_muscle/
    priority_pattern — те, що обрав користувач.
    """
    bonus = 0.0
    if priority_muscle and muscle_group == priority_muscle:
        bonus += SCORE_BONUS_GROUP
        if priority_pattern and pattern == priority_pattern:
            bonus += SCORE_BONUS_PATTERN
    return bonus