"""
Context Score Engine
═════════════════════
Score Engine (exercise_selector.py) оцінює кожну вправу-кандидата
ІЗОЛЬОВАНО — саму по собі, без урахування того, що вже обрано в
цьому тренуванні. Це залишає прогалину: жим лежачи сам по собі
може отримати відмінний бал, навіть якщо в тренуванні вже є жим
гантелей і жим вниз головою (та сама родина патернів — chest_press
family) — фактичний стимул уже частково задубльований, хоча
Score Engine цього не бачить.

Constraint Engine (constraints.py) вже рахує family_counts як
ТВЕРДИЙ ліміт (не більше 2 вправ однієї родини за день — повне
блокування після ліміту). Context Score додає М'ЯКШИЙ, градуальний
шар ПЕРЕД цим твердим лімітом: кожна вже обрана вправа тієї самої
родини патернів поступово знижує score наступного кандидата тієї ж
родини — перший жим повний бал, другий (ще в межах ліміту 2) уже
трохи нижчий, третій (за лімітом) все одно заблокований Constraint
Engine-ом окремо.

Навмисно перевикористовує ConstraintContext.family_counts — не
новий стейт, той самий лічильник, який уже веде Constraint Engine.
"""

from .recovery import get_family

CONTEXT_PENALTY_PER_FAMILY_MEMBER = 1.2


def compute_context_penalty(pattern: str, family_counts: dict) -> float:
    """
    Повертає від'ємний штраф (0.0 якщо нема дублювання), який
    додається до Exercise Score. Штраф росте лінійно з кількістю
    вже обраних сьогодні вправ тієї самої родини патернів.

    Патерни поза PATTERN_FAMILIES (більшість бази — лише дві родини
    визначено зараз: hip_hinge_family, chest_press_family) не мають
    штрафу — це навмисно вузький, консервативний перший крок, а не
    спроба оцінити дублювання стимулу по всій базі одразу.
    """
    if not pattern:
        return 0.0
    family = get_family(pattern)
    if not family:
        return 0.0
    count = family_counts.get(family, 0)
    return -CONTEXT_PENALTY_PER_FAMILY_MEMBER * count