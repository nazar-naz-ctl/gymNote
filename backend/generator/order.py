"""
Exercise Order Engine
══════════════════════
Будує методично правильний сценарій тренування. Base → Assist →
Isolation → Прес → Литки → Мобільність — ТВЕРДІ, гарантовані межі
(як і Прес/Литки/Мобільність з першої версії). Це виправлення
знайденого на реальному тесті бага: коли зважена сума (0.45×Тип +
0.25×Fatigue + ...) рахувалась ОДНИМ неперервним числом для всіх
вправ одразу, вправа, помилково позначена як "isolation" (через
нестачу вправ у пулі), але з високим Fatigue/Spine Load (типу важкий
жим), могла обігнати справжню "assist"-вправу за підсумковим
Priority Score — тип мав домінувати, але на практиці лише "важко
переважував", а не гарантував порядок.

Тепер: Тип вправи (base/assist/isolation) — ТВЕРДИЙ рівень, вправи з
різних рівнів НІКОЛИ не переставляються місцями одна відносно одної.
Priority Score рахується лише В МЕЖАХ одного рівня — там він і
визначає, яка з кількох, наприклад, "assist"-вправ важча за іншу.

В межах одного рівня:
    0.45 × Compound-бонус / унілатеральний штраф
    0.25 × Fatigue Score
    0.15 × Skill
    0.10 × Spine Load
    0.05 × Stimulus
"""

COMPOUND_BONUS = 20
UNILATERAL_PENALTY = 10

WEIGHT_SUBTYPE = 0.45
WEIGHT_FATIGUE = 0.25
WEIGHT_SKILL = 0.15
WEIGHT_SPINE_LOAD = 0.10
WEIGHT_STIMULUS = 0.05

# Тверді рівні — вправа з рівня 0 НІКОЛИ не опиниться після вправи
# з рівня 1, незалежно від жодного Score.
MACRO_TIER_BY_EX_TYPE = {
    "base": 0,
    "assist": 1,
    "isolation": 2,
    "abs": 3,
    "calves": 4,
}
MOBILITY_TIER = 5
DEFAULT_TIER = 2  # якщо ex_type геть невідомий — трактуємо як ізоляцію


def _macro_tier(ex: dict) -> int:
    ex_type = ex.get("ex_type")
    if ex_type in MACRO_TIER_BY_EX_TYPE:
        # Мобільність/розтяжка — завжди останні, навіть якщо якимось
        # чином позначені під звичайний ex_type
        if ex.get("type") in ("здоров'я", "розтяжка"):
            return MOBILITY_TIER
        return MACRO_TIER_BY_EX_TYPE[ex_type]
    if ex.get("type") in ("здоров'я", "розтяжка"):
        return MOBILITY_TIER
    return DEFAULT_TIER


def _unilateral_penalty_for_level(level: int | None) -> float:
    """Level-Dependent Progression: новачку (рівень 1) унілатеральні
    вправи даються важче технічно — штраф сильніший, вони йдуть
    пізніше в тренуванні. Профі (рівень 4) — навпаки, можуть братись
    за них раніше, поки свіжі, штраф слабший."""
    if level == 1:
        return 15
    if level == 4:
        return 5
    return UNILATERAL_PENALTY


def _stability_adjustment_for_level(stability: int, level: int | None) -> float:
    """Level-Dependent Progression: той самий принцип, що вже є в
    Score Engine (exercise_selector.py) — новачку простіше виконати
    вправу з нижчою stability (тренажер), профі краще підходить
    вища stability (вільна вага/баланс). Без цього дві білатеральні
    вправи (напр. Присідання з гантелями vs Жим ногами) не
    відрізнялись би за рівнем узагалі — унілатеральний штраф тут не
    допомагає, якщо жодна з них не унілатеральна."""
    if level == 1:
        return (3 - stability) * 4
    if level == 4:
        return (stability - 3) * 4
    return 0.0


def _intra_tier_score(ex: dict, level: int | None = None) -> float:
    """Вищий бал → вправа виконується раніше В МЕЖАХ того самого
    твердого рівня (base серед base, assist серед assist, ...)."""
    subtype_score = COMPOUND_BONUS if ex.get("compound") else 0
    if ex.get("unilateral"):
        subtype_score -= _unilateral_penalty_for_level(level)

    fatigue_score = ex.get("fatigue", 3) * 20
    skill_score = ex.get("skill", 3) * 20
    spine_score = ex.get("spine_load", 1) * 20
    stimulus_score = ex.get("stimulus", 5) * 10

    base_score = (
        WEIGHT_SUBTYPE * subtype_score
        + WEIGHT_FATIGUE * fatigue_score
        + WEIGHT_SKILL * skill_score
        + WEIGHT_SPINE_LOAD * spine_score
        + WEIGHT_STIMULUS * stimulus_score
    )
    return base_score + _stability_adjustment_for_level(ex.get("stability", 3), level)


# Зберігаємо стару назву як псевдонім — primary.py імпортує саме її
_priority_score = _intra_tier_score
def order_exercises(exercises: list, level: int | None = None) -> list:
    """
    Base → Assist → Isolation → Прес → Литки → Мобільність — тверді,
    гарантовані рівні. В межах кожного рівня — Priority Score
    (Fatigue/Skill/Spine Load/Stimulus/Compound/Унілатеральність,
    остання — рівень-залежна, якщо level задано).
    """
    def sort_key(ex):
        return (_macro_tier(ex), -_intra_tier_score(ex, level))

    return sorted(exercises, key=sort_key)