"""
Exercise Selection Engine
═════════════════════════
Підбір конкретних вправ під м'язову групу/обладнання/рівень,
з урахуванням рухових патернів (щоб не ставити в один день
кілька однотипних рухів) та пріоритетних списків базових/
ізоляційних вправ.
"""

import random

from exercises_db import get_exercises
from .volume import filter_by_difficulty
from .constraints import ConstraintContext, is_allowed, register_pick
from .context_score import compute_context_penalty


# ══════════════════════════════════════════════════════
# EXERCISE SCORE ENGINE 2.0
# ══════════════════════════════════════════════════════
# При рівних умовах (той самий патерн, та сама група м'язів,
# обидві доступні під обладнання) — деякі вправи об'єктивно
# кращі за інші. П'ять критеріїв:
#
# 1. Вільна вага краща за тренажер (більше стабілізаторів,
#    краще для росту й сили)
# 2. Складність відповідає рівню користувача (новачку — легшу
#    вправу, навіть якщо доступна складніша з тим самим патерном)
# 3. Білатеральні вправи пріоритетні для базових слотів (простіше
#    прогресувати вагою), унілатеральні — для допоміжних/ізоляції
#    (краще для балансу лівого/правого)
# 4. Compound-рухи пріоритетні для базових слотів (Exercise Database 2.0)
# 5. Stimulus вправи відповідає цілі користувача (Exercise Database 2.0)
#
# 2.0: критерії 3-5 тепер читають готові поля прямо з бази
# (unilateral/compound/stimulus, записані Exercise Database 2.0),
# а не рахують патерн повторно на кожен виклик.
#
# Score НЕ робить вибір детермінованим — використовується як вага
# для випадкового вибору, щоб "Згенерувати ще" й далі давало
# різноманітність, просто з нахилом до кращих варіантів.

FREE_WEIGHT_EQUIPMENT = {"штанга", "гантелі", "гиря", "власна вага", "турнік", "бруси", "кільця", "TRX"}

# Цільове значення числового stimulus (1-10) для кожної цілі
# користувача (Database 2.1 — раніше тут була категорія-рядок)
GOAL_TO_STIMULUS_TARGET = {
    "маса": 5.0,           # гіпертрофія
    "рельєф": 5.0,
    "сила": 7.5,
    "схуднення": 2.5,
    "витривалість": 2.5,
}


def get_exercise_score(
    ex: dict, level: int, ex_type: str, goal: str = None,
    muscle_group: str = None, priority_muscle: str = None, priority_pattern: str = None,
    family_counts: dict = None,
) -> float:
    score = 0.0

    # 1. Вільна вага краще за тренажер
    equipment = ex.get("equipment", [])
    if any(eq in FREE_WEIGHT_EQUIPMENT for eq in equipment):
        score += 2.0

    # 2. Складність відповідає рівню (чим ближче — тим краще)
    difficulty = ex.get("difficulty", 3)
    score -= abs(difficulty - level) * 0.7

    # 3. Білатеральність відповідно до типу слоту (поле з бази, 2.0)
    is_unilateral = ex.get("unilateral", False)
    if ex_type == "base" and not is_unilateral:
        score += 1.0
    elif ex_type in ("assist", "isolation") and is_unilateral:
        score += 0.5

    # 4. Compound-рухи пріоритетні для базових слотів (поле з бази, 2.0)
    if ex_type == "base" and ex.get("compound"):
        score += 1.5

    # 5. Stimulus вправи відповідає цілі (поле з бази, 2.1 — числова
    #    шкала 1-10, бонус за близькістю до цільового значення)
    stimulus = ex.get("stimulus")
    target = GOAL_TO_STIMULUS_TARGET.get(goal) if goal else None
    if stimulus is not None and target is not None:
        diff = abs(stimulus - target)
        score += max(0.0, 1.5 - diff * 0.25)

    # 6. Muscle Priority Engine — бонус за співпадіння обраного
    #    користувачем акценту (групи і, опційно, патерну всередині
    #    групи, напр. incline_press для "верх грудей")
    if priority_muscle:
        from .priority import priority_score_bonus
        score += priority_score_bonus(muscle_group, ex.get("movement_pattern"), priority_muscle, priority_pattern)

    # 7. Level-Dependent Progression — новачку (рівень 1) легше
    #    ВИКОНАТИ технічно (нижча stability/skill) навіть при тій
    #    самій difficulty; профі (рівень 4) навпаки — технічніші,
    #    вимогливіші до балансу варіації дають кращий стимул, і вони
    #    вже готові до них. Рівні 2-3 — нейтрально, без цього бонусу.
    stability = ex.get("stability", 3)
    skill = ex.get("skill", 3)
    if level == 1:
        score += (3 - stability) * 0.4
        score += (3 - skill) * 0.3
    elif level == 4:
        score += (stability - 3) * 0.4
        score += (skill - 3) * 0.3

        # 8. Context Score Engine — м'який штраф за дублювання родини
        #    патернів у межах уже обраних сьогодні вправ (перед твердим
        #    лімітом Constraint Engine)
    if family_counts is not None:
        score += compute_context_penalty(ex.get("movement_pattern"), family_counts)

        return score


def _score_weighted_shuffle(
    exercises: list, level: int, ex_type: str, goal: str = None, jitter: float = 1.5,
    muscle_group: str = None, priority_muscle: str = None, priority_pattern: str = None,
    family_counts: dict = None,
) -> list:
    """Сортує список вправ за Exercise Score + випадковий шум — кращі
    вправи частіше опиняються попереду, але не гарантовано завжди."""
    scored = [
        (
            get_exercise_score(ex, level, ex_type, goal, muscle_group, priority_muscle, priority_pattern, family_counts)
            + random.uniform(-jitter, jitter),
            ex,
        )
        for ex in exercises
    ]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [ex for _, ex in scored]


# ══════════════════════════════════════════════════════
# МАПИ М'ЯЗІВ
# ══════════════════════════════════════════════════════

MUSCLE_SEARCH = {
    "груди":          ["груди", "верхні груди", "нижні груди"],
    "спина_ширина":   ["широчайні"],
    "спина_товщина":  ["спина", "широчайні", "трапеція"],
    "квадрицепс":     ["квадрицепс"],
    "біцепс стегна":  ["біцепс стегна"],
    "сідниці":        ["сідниці"],
    "плечі":          ["передні дельти", "середні дельти"],
    "задні дельти":   ["задні дельти"],
    "трапеція":       ["трапеція"],
    "біцепс":         ["біцепс"],
    "трицепс":        ["трицепс"],
    "прес":           ["прес", "нижній прес", "косі м'язи", "кор"],
    "литки":          ["литки", "камбалоподібний м'яз"],
}


# ══════════════════════════════════════════════════════
# РУХОВІ ПАТЕРНИ
# ══════════════════════════════════════════════════════
# Позначаємо, до якого типу руху належить вправа, щоб не
# ставити в один день 2-3 вправи, які по суті одне й те саме
# (наприклад три варіанти вертикального жиму на плечі).
# PATTERN_MAP — ручне тегування (пріоритетне).
# AUTO_PATTERN_MAP — згенеровано скриптом auto_tag_patterns.py,
# покриває решту бази (592/593 вправ).

# ══════════════════════════════════════════════════════
# RUKHOVI PATTERNS — читання з бази (не окремий словник)
# ══════════════════════════════════════════════════════
# PATTERN_MAP/AUTO_PATTERN_MAP переїхали в enrichment.py — там вони
# лише "насіннєві" дані для первинного заповнення бази. Тут —
# тонка обгортка "по імені", на випадок коли під рукою немає самого
# об'єкта вправи (десь усередині find_exercises є саме такий кейс,
# дивись Прохід 0). Всюди, де об'єкт вправи вже є в руках — паттерн
# читається напряму: ex.get("movement_pattern"), без цього виклику.

_PATTERN_BY_NAME_CACHE = None


def get_pattern(name: str) -> str | None:
    """Пошук патерну вправи по імені — читає з уже збагаченої бази
    (exercises_db), а не з окремого словника."""
    global _PATTERN_BY_NAME_CACHE
    if _PATTERN_BY_NAME_CACHE is None:
        from exercises_db import exercises as _all_exercises
        _PATTERN_BY_NAME_CACHE = {e["name"]: e.get("movement_pattern") for e in _all_exercises}
    return _PATTERN_BY_NAME_CACHE.get(name)




# ══════════════════════════════════════════════════════
# ПРІОРИТЕТНІ СПИСКИ ВПРАВ
# ══════════════════════════════════════════════════════

BASE_EXERCISES = {
    "груди": [
        "Жим штанги лежачи", "Похилий жим штанги", "Жим гантелей лежачи",
        "Похилий жим гантелей", "Жим штанги вниз головою",
        "Жим гантелей вниз головою", "Жим у Смітті (груди)",
        "Віджимання класичні", "Віджимання з підвищенням ніг",
        "Відмивання на брусах з нахилом вперед", "Відмивання на брусах",
        "TRX Віджимання", "Жим гирі лежачи",
    ],
    "спина_ширина": [
        "Підтягування широким хватом", "Підтягування зворотним хватом",
        "Підтягування вузьким хватом", "Тяга верхнього блоку широким хватом",
        "Тяга верхнього блоку вузьким хватом", "Тяга верхнього блоку зворотним хватом",
        "Австралійські підтягування", "TRX Рядок (Row)", "Підтягування з вагою",
        "Мускул-ап на турніку",
    ],
    "спина_товщина": [
        "Станова тяга класична", "Станова тяга сумо", "Тяга штанги в нахилі прямим хватом",
        "Тяга штанги в нахилі зворотним хватом", "Тяга Т-грифа",
        "Тяга гантелі однією рукою", "Тяга нижнього блоку сидячи вузьким хватом",
        "Тяга нижнього блоку широким хватом", "Гарне ранок зі штангою",
        "Румунська тяга зі штангою", "Тяга гирі до поясу",
    ],
    "квадрицепс": [
        "Присідання зі штангою на спині", "Фронтальні присідання",
        "Присідання у Смітті", "Жим ногами", "Гак-машина присідання",
        "Присідання з гантелями", "Гоблет-присідання з гантеллю",
        "Присідання з власною вагою", "Присідання пістолетик",
        "Гоблет-присідання з гирею", "Стрибки в присіді",
    ],
    "біцепс стегна": [
        "Румунська тяга зі штангою", "Румунська тяга з гантелями",
        "Мертва тяга на прямих ногах зі штангою", "Гарне ранок зі штангою",
        "Згинання ніг лежачи", "Згинання ніг стоячи",
    ],
    "сідниці": [
        "Ягідний місток зі штангою", "Ягідний місток з гантеллю",
        "Міст на плечах", "Болгарські випади зі штангою",
        "Болгарські випади з гантелями", "Болгарські випади",
        "Випади зі штангою", "Випади з гантелями",
        "Міст з резинкою на стегнах", "Міст на одній нозі",
    ],
    "плечі": [
        "Армійський жим стоячи", "Армійський жим сидячи",
        "Жим гантелей сидячи", "Жим гантелей стоячи",
        "Жим Арнольда", "Жим за голову",
        "Стійка на руках біля стіни", "Віджимання в упорі стоячи",
        "TRX Жим плечей", "Жим двох гирей стоячи",
    ],
    "біцепс": [
        "Підйом штанги на біцепс стоячи", "Підйом EZ-штанги на біцепс",
        "Підйом гантелей на біцепс стоячи", "Підйом штанги на лаві Скотта",
        "TRX Підйом на біцепс", "Підтягування зворотним хватом",
    ],
    "трицепс": [
        "Жим штанги вузьким хватом", "Французький жим лежачи зі штангою",
        "Французький жим з гантеллю лежачи", "Відмивання на брусах",
        "Відмивання від лавки або стільця", "TRX Розгинання трицепса",
        "Алмазні віджимання",
    ],
    "прес": [
        "Підйом ніг у висі прямих", "Підйом колін у висі",
        "Скручування", "Зворотні скручування", "Планка на ліктях",
        "Планка на руках", "Гірський альпініст", "V-підйом",
        "Велосипед", "Ножиці", "Підйом ніг лежачи",
        "Скручування у тренажері", "Колесо для преса",
        "Підйом ніг у тренажері",
    ],
    "литки": [
        "Підйом на носки стоячи у тренажері", "Підйом на носки сидячи у тренажері",
        "Підйом на носки з гантелями", "Підйом на носки зі штангою",
        "Підйом на носки стоячи", "Підйом на носки на одній нозі",
        "Підйом на носки з резинкою",
    ],
}

ISOLATION_EXERCISES = {
    "груди": [
        "Розводка гантелей лежачи", "Похила розводка гантелей",
        "Зведення в кросовері верхній блок", "Зведення в кросовері нижній блок",
        "Пек-дек (метелик)", "Пуловер з гантеллю", "Кабельні перехрещення (crossover)",
        "Розводка з резинкою",
    ],
    "спина_ширина": [
        "Тяга верхнього блоку за голову", "TRX Рядок (Row)",
        "TRX Рядок з поворотом", "Австралійські підтягування",
    ],
    "спина_товщина": [
        "Горизонтальна тяга в тренажері", "Зворотна гіперекстензія",
        "Гіперекстензія", "Розгинання спини на римському стільці",
        "Супермен",
    ],
    "квадрицепс": [
        "Розгинання ніг у тренажері", "Зашагування на лаву з гантелями",
        "Зашагування на степ з гирею", "Випади на місці",
        "Випади крокові", "Бічні випади", "Стінне присідання",
    ],
    "біцепс стегна": [
        "Румунська тяга з гантелями", "Мертва тяга з гирею",
        "Гіперекстензія", "Зворотна гіперекстензія лежачи",
    ],
    "сідниці": [
        "Відведення ноги у тренажері", "Відведення ноги з резинкою стоячи",
        "Кроки крабом з резинкою", "Зведення ніг з резинкою лежачи",
        "Зворотні випади з гантелями", "Зворотні випади з власною вагою",
    ],
    "плечі": [
        "Підйом гантелей в сторони", "Підйом гантелей вперед",
        "Підйом резинки в сторони", "Підйом резинки вперед",
        "Тяга резинки до підборіддя", "Тяга штанги до підборіддя",
        "TRX Зворотнє розведення",
    ],
    "задні дельти": [
        "Розведення гантелей в нахилі", "Зворотні зведення на блоці",
        "Зворотній пек-дек", "TRX Зворотнє розведення",
        "Зворотне розведення з резинкою",
    ],
    "трапеція": [
        "Шраги зі штангою", "Шраги з гантелями", "Шраги з гирею",
        "Тяга штанги до підборіддя", "Фермерська прогулянка з гантелями",
    ],
    "біцепс": [
        "Молотки з гантелями", "Концентровані підйоми",
        "Підйом гантелей на лаві Скотта", "Підйом гантелей зворотним хватом",
        "Підйом на біцепс з резинкою", "Молотки з резинкою",
        "Підйом на біцепс з гирею",
    ],
    "трицепс": [
        "Розгинання на блоці прямою рукояткою", "Розгинання на блоці мотузкою",
        "Кікбек з гантеллю", "Розгинання гантелі з-за голови стоячи",
        "TRX Розгинання трицепса", "Розгинання трицепса з резинкою стоячи",
        "Розгинання трицепса з гирею",
    ],
    "прес": [
        "Бічна планка", "Російські скручування", "Скручування з поворотом",
        "Планка з підйомом руки і ноги", "Гірський альпініст хрест",
        "Dead Bug", "Ведмежа прогулянка", "Вакуум живота",
    ],
    "литки": [
        "Підйом на носки сидячи у тренажері", "Підйом на носки на одній нозі",
        "Підйом на носки з резинкою",
    ],
}


# ══════════════════════════════════════════════════════
# ПІДБІР ВПРАВ
# ══════════════════════════════════════════════════════


def find_exercises(
    muscle_group: str,
    ex_type: str,
    equipment: list,
    level: int,
    goal: str,
    used_names: set,
    count: int,
    used_patterns: set = None,
    avoid_today: set = None,
    family_counts: dict = None,
    priority_muscle: str = None,
    priority_pattern: str = None,
) -> list:
    """
    Знаходить вправи для конкретної групи м'язів.
    Спочатку шукає з пріоритетного списку, потім з бази.
    """
    results = []
    _ctx = ConstraintContext(
        used_names=used_names,
        used_patterns=used_patterns,
        avoid_today=avoid_today,
        family_counts=family_counts if family_counts is not None else {},
    )

    if ex_type == "base":
        priority_list = BASE_EXERCISES.get(muscle_group, [])
    elif ex_type == "isolation":
        priority_list = ISOLATION_EXERCISES.get(muscle_group, [])
    else:
        priority_list = BASE_EXERCISES.get(muscle_group, []) + ISOLATION_EXERCISES.get(muscle_group, [])

    # Muscle Priority Engine: якщо задано priority_pattern для ЦІЄЇ
    # групи — імена, що відповідають патерну, йдуть ПЕРШИМИ навіть
    # тут, у Проході 0. Без цього Прохід 0 міг заповнити весь слот
    # (і вийти з функції на "return results" нижче) звичайними
    # вправами ще ДО того, як пріоритет патерну взагалі встиг би
    # спрацювати десь далі в каскаді.
    if priority_pattern and muscle_group == priority_muscle:
        matching_names = [n for n in priority_list if get_pattern(n) == priority_pattern]
        other_names = [n for n in priority_list if n not in matching_names]
        random.shuffle(matching_names)
        random.shuffle(other_names)
        priority_list = matching_names + other_names
    else:
        priority_list = random.sample(priority_list, len(priority_list))

    for name in priority_list:
        if name in _ctx.used_names:
            continue
        found = get_exercises(
            muscles=MUSCLE_SEARCH.get(muscle_group, [muscle_group]),
            equipment=equipment,
            level=level,
        )

        matched = [e for e in found if e["name"] == name]
        if not matched:
            continue
        ex = matched[0]
        if not is_allowed(ex, level, _ctx):
            continue

        ex = ex.copy()
        results.append(ex)
        register_pick(ex, _ctx)
        if len(results) >= count:
            return results

    if len(results) < count:
        muscle_list = MUSCLE_SEARCH.get(muscle_group, [muscle_group])

        def _primary_match(ex):
            return ex.get("muscles") and ex["muscles"][0] in muscle_list

        found = get_exercises(equipment=equipment, level=level, goal=goal, ex_type="сила")
        found = filter_by_difficulty(found, level)
        found = [e for e in found if _primary_match(e)]

        # Виключаємо розтяжку/мобільність — це не силові вправи,
        # їм не місце в робочих підходах.
        def _is_working_type(ex):
            return ex.get("type") not in ("розтяжка", "здоров'я")

        if not found:
            found = get_exercises(equipment=equipment, goal=goal)
            found = filter_by_difficulty(found, level)
            found = [e for e in found if _primary_match(e) and _is_working_type(e)]

        if not found:
            found = get_exercises(equipment=equipment)
            found = filter_by_difficulty(found, level)
            found = [e for e in found if _primary_match(e) and _is_working_type(e)]

        # Muscle Priority Engine: якщо задано priority_pattern для
        # ЦІЄЇ групи (напр. incline_press для "верх грудей") — твердий
        # пріоритет, а не м'який бонус. М'який бонус (у Score Engine
        # нижче) виявився ненадійним для base-слоту: натуральна різниця
        # Fatigue/Skill/SpineLoad між двома вправами тієї самої групи
        # часто переважує +2 бали бонусу, і акцент користувача програє
        # конкуренцію за місце в слоті — той самий баг, що вже був
        # виправлений для Primary Lift, тепер виправлений тут само,
        # на рівень раніше (щоб потрібна вправа взагалі потрапила в
        # base, а не лише в assist/isolation).
        if priority_pattern and muscle_group == priority_muscle:
            pattern_matched = [e for e in found if e.get("movement_pattern") == priority_pattern]
            if pattern_matched:
                found = pattern_matched

        found = _score_weighted_shuffle(found, level, ex_type, goal, muscle_group=muscle_group, priority_muscle=priority_muscle, priority_pattern=priority_pattern, family_counts=_ctx.family_counts)

        # Прохід 1: звичайний підбір через Constraint Engine — блокує
        # used_names, патерн і родину патернів (Compatibility Engine)
        for ex in found:
            if len(results) >= count:
                break
            if not is_allowed(ex, level, _ctx):
                continue
            ex = ex.copy()
            results.append(ex)
            register_pick(ex, _ctx)

        # Прохід 2: дозволяємо повторення ТОЧНОГО патерну, але ще тримаємо
        # ліміт родини (Compatibility Engine) — це саме той випадок, коли
        # м'язова група (напр. задня поверхня стегна) має по суті лише
        # 2 реальні патерни в базі, і без цього кроку відразу довелось би
        # стрибати в найагресивніший фолбек, ігноруючи родину повністю.
        #
        # Пул тут — БЕЗ фільтра по цілі (тільки обладнання + рівень):
        # деякі вправи в базі протеговані лише під одну ціль (напр.
        # "Згинання ніг стоячи" — лише "рельєф"), хоча по суті придатні
        # для будь-якої цілі. На цьому кроці, коли вибір і так обмежений,
        # не варто губити придатну альтернативу через таке тегування.
        if len(results) < count:
            wide_found = get_exercises(equipment=equipment, level=level)
            wide_found = filter_by_difficulty(wide_found, level)
            wide_found = [e for e in wide_found if _primary_match(e) and _is_working_type(e)]
            wide_found = _score_weighted_shuffle(wide_found, level, ex_type, goal, muscle_group=muscle_group, priority_muscle=priority_muscle, priority_pattern=priority_pattern, family_counts=_ctx.family_counts)
            for ex in wide_found:
                if len(results) >= count:
                    break
                # Прохід 2 свідомо дозволяє повторення ТОЧНОГО патерну
                # (check_pattern=False) — родина патернів все ще ліміт
                if not is_allowed(ex, level, _ctx, check_pattern=False):
                    continue
                ex = ex.copy()
                results.append(ex)
                register_pick(ex, _ctx)

                # Прохід 3: остаточний фолбек — ігноруємо і патерн, і родину
                # (used_names все ще блокує)
                if len(results) < count:
                    for ex in found:
                        if len(results) >= count:
                            break
                        if not is_allowed(ex, level, _ctx, check_pattern=False, check_family=False):
                            continue
                        ex = ex.copy()
                        results.append(ex)
                        register_pick(ex, _ctx)

                # Прохід 4: якщо навіть після цього не вистачає (обладнання дуже
                # обмежене, всі підходящі вправи вже використані раніше цього тижня)
                # — дозволяємо повторити ту саму вправу в інший день. Це нормальна
                # практика в реальних програмах, краще за порожній день.
                # avoid_today все ще перевіряється напряму (не через is_allowed) —
                # тут свідомо ІГНОРУЄМО used_names (це і є суть Проходу 4: дозволити
                # вправу, вже використану СЬОГОДНІ В ЦЬОМУ СЛОТІ раніше — перевірка
                # йде проти already_in_this_slot, окремого локального сету).
                if len(results) < count and found:
                    already_in_this_slot = {e["name"] for e in results}
                    for ex in found:
                        if len(results) >= count:
                            break
                        if ex["name"] in already_in_this_slot:
                            continue
                        if _ctx.avoid_today and ex["name"] in _ctx.avoid_today:
                            continue
                        results.append(ex.copy())
                        already_in_this_slot.add(ex["name"])

    return results
