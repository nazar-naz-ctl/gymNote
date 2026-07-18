"""
Constraint Engine
═════════════════
Єдина точка входу для ВСІХ жорстких правил підбору вправи ("чи
можна взяти цю вправу зараз"), які раніше були розкидані по різних
місцях find_exercises() і викликалися вручну, кожне окремо:

    - filter_by_difficulty()   (volume.py)      — складність vs рівень
    - family_cap_reached()     (recovery.py)    — ліміт родин патернів
    - used_names                                — заборона повтору вправи
    - used_patterns                             — заборона повтору патерну
    - avoid_today                               — заборона вправ з інших
                                                   слотів сьогодні

Мета: будь-який майбутній модуль, що підбирає чи замінює вправу
(Optimization Engine 2.0, Context Score Engine), викликає ОДИН метод
is_allowed() замість того, щоб пам'ятати й повторно імпортувати всі
п'ять правил окремо. Один забутий виклик — і майбутній модуль може
згенерувати вправу, яка порушує правило, що діяло всюди інде
(конкретний прецедент: забутий priority_pattern у виклику
select_primary_lift в focus.py, знайдений і виправлений раніше).

MRV Enforcement (volume.py, enforce_mrv) свідомо НЕ входить сюди —
це не фільтр вибору "чи можна взяти вправу зараз", а пост-обробка
вже готового обсягу (скільки СЕТІВ дозволено після того, як вправи
вже обрані). Різна категорія обмежень, різний момент застосування.
"""

from .volume import filter_by_difficulty
from .recovery import family_cap_reached, register_family_pick


class ConstraintContext:
    """Пакет усіх стейтфул-лічильників, які потрібні для перевірки
    обмежень на один виклик підбору. Замінює розрізнені позиційні
    аргументи (used_names, used_patterns, avoid_today, family_counts)
    одним об'єктом — новий код передає один context, а не 4 окремі
    змінні, які легко переплутати місцями або забути одну з них."""

    def __init__(self, used_names=None, used_patterns=None, avoid_today=None, family_counts=None):
        self.used_names = used_names if used_names is not None else set()
        self.used_patterns = used_patterns  # None = патерн не блокується (напр. abs/calves)
        self.avoid_today = avoid_today if avoid_today is not None else set()
        self.family_counts = family_counts if family_counts is not None else {}


def is_allowed(ex: dict, level: int, context: ConstraintContext, *, check_pattern: bool = True, check_family: bool = True) -> bool:
    """
    Єдина перевірка "чи можна взяти цю вправу зараз". Повертає
    True/False, нічого не мутує (побічні ефекти — окремо, через
    register_pick(), після того як вправа дійсно обрана).

    check_pattern/check_family — вимикаються на пізніх проходах
    фолбеку (Прохід 2/3 у find_exercises), де правило свідомо
    послаблюється через обмеженість пулу вправ.
    """
    name = ex.get("name")
    if name in context.used_names:
        return False

    if context.avoid_today and name in context.avoid_today:
        return False

    difficulty = ex.get("difficulty", 3)
    if not filter_by_difficulty([ex], level):
        return False

    pattern = ex.get("movement_pattern")
    if check_pattern and context.used_patterns is not None and pattern and pattern in context.used_patterns:
        return False

    if check_family and pattern and family_cap_reached(pattern, context.family_counts):
        return False

    return True


def register_pick(ex: dict, context: ConstraintContext) -> None:
    """Після того як вправа дійсно обрана — реєструє її у всіх
    відповідних лічильниках одразу (замінює ручні виклики
    used_names.add() + used_patterns.add() + register_family_pick()
    у трьох різних місцях find_exercises)."""
    name = ex.get("name")
    pattern = ex.get("movement_pattern")

    context.used_names.add(name)
    if context.used_patterns is not None and pattern:
        context.used_patterns.add(pattern)
    if pattern:
        register_family_pick(pattern, context.family_counts)