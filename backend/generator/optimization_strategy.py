"""
Optimization Strategies — Крок 3
══════════════════════════════════
ReplaceExerciseStrategy: єдина поки що реалізована стратегія.
Обробляє ЛИШЕ Problem з source="coverage" — заміна однієї вправи
в межах тієї самої м'язової групи на вправу, що закриває
відсутній/недобраний руховий патерн.

Push/Pull, Quad/Ham, Joint Balance дисбаланси НЕ вирішуються цією
стратегією — вони вимагають міжгрупового втручання (зміна обсягу
між групами, а не заміна вправи в одному слоті), що поза межами
"локальної заміни вправи". Для них потрібна майбутня
AdjustSetsStrategy (заглушка нижче, без реалізації).

Архітектура Strategy Pattern: диспетчер can_handle(problem) визначає,
чи ця стратегія взагалі береться за проблему — оркестратор циклу
(Крок 5) питає кожну зареєстровану стратегію по черзі.
"""

from dataclasses import dataclass

from .exercise_selector import find_exercises, get_exercise_score
from .constraints import ConstraintContext
from .context_score import compute_context_penalty


# Вага "вартості заміни" за типом слоту — вища вартість = сильніше
# втручання в програму, при рівних умовах оптимізатор має обирати
# дешевшу заміну.
EX_TYPE_COST = {"base": 3, "assist": 2, "isolation": 1}
PRIMARY_LIFT_COST_MULTIPLIER = 2.0  # заміна Primary Lift (🎯) — найдорожче втручання


@dataclass
class Candidate:
    exercise: dict
    day_num: int
    exercise_index: int
    replacement_cost: float
    raw_score: float


def compute_replacement_cost(ex: dict, day_exercises: list, exercise_index: int) -> float:
    """
    Вартість заміни конкретної вправи в конкретній позиції.
    База — вага типу слоту (base > assist > isolation). Якщо вправа
    позначена як Primary Lift (🎯) — додатковий множник, бо це
    найбільш "видима" й архітектурно значуща вправа тренування.
    """
    ex_type = ex.get("ex_type", "isolation")
    base_cost = EX_TYPE_COST.get(ex_type, 1)
    if ex.get("is_primary"):
        base_cost *= PRIMARY_LIFT_COST_MULTIPLIER
    return base_cost


def _find_target_slot(problem, program: dict):
    """
    Для Coverage-проблеми: знаходить КОНКРЕТНУ вправу в програмі, яку
    варто спробувати замінити. Пріоритет — вправа, чий патерн уже
    ДУБЛЮЄТЬСЯ іншою вправою тієї самої групи десь у тижні (заміна
    дубліката втрачає найменше, бо той самий патерн лишається
    представленим іншою вправою). Якщо дубліката нема — беремо
    вправу з НАЙДЕШЕВШИМ replacement_cost (isolation, не Primary Lift).

    Повертає (day_num, exercise_index, exercise) або None, якщо
    групу взагалі не знайдено в програмі (нема що замінювати).
    """
    if not problem.affected_muscles:
        return None
    group = problem.affected_muscles[0]

    # Збираємо всі вправи цієї групи по всій програмі разом з позицією
    group_slots = []
    pattern_counts = {}
    for day_num, day in program.items():
        for idx, ex in enumerate(day.get("exercises", [])):
            if ex.get("_group") == group:
                group_slots.append((day_num, idx, ex))
                pattern = ex.get("movement_pattern")
                if pattern:
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    if not group_slots:
        return None

    # Спершу шукаємо дубльований патерн (count > 1)
    duplicated = [
        (d, i, ex) for d, i, ex in group_slots
        if pattern_counts.get(ex.get("movement_pattern"), 0) > 1
    ]
    pool = duplicated if duplicated else group_slots

    # З пулу — обираємо найдешевшу заміну
    pool_sorted = sorted(
        pool,
        key=lambda t: compute_replacement_cost(t[2], program[t[0]]["exercises"], t[1])
    )
    return pool_sorted[0]


def generate_candidates(problem, program: dict, level: int, equipment: list, goal: str, top_n: int = 5) -> list:
    """
    Для Coverage-проблеми: генерує до top_n кандидатів на заміну
    конкретного знайденого слоту. Кандидати шукаються через уже
    готовий find_exercises(), з priority_pattern = один з відсутніх
    патернів (перший за списком problem.affected_patterns), і
    відсортовані за Exercise Score (Context Score вже врахований
    усередині get_exercise_score через family_counts).

        Повертає [] якщо слот не знайдено або кандидатів немає.
        """
    target = _find_target_slot(problem, program)
    if target is None:
        return []

    day_num, exercise_index, target_ex = target
    group = target_ex.get("_group")
    ex_type = target_ex.get("ex_type", "isolation")
    missing_pattern = problem.affected_patterns[0] if problem.affected_patterns else None

    # used_names — усі вправи, вже присутні в програмі (крім самої
    # заміщуваної), щоб не запропонувати дублікат імені
    used_names = set()
    for day in program.values():
        for ex in day.get("exercises", []):
            if ex is not target_ex:
                used_names.add(ex["name"])

    family_counts = {}  # свіжий контекст для оцінки кандидатів — не
    # той самий, що в оригінальній генерації

    found = find_exercises(
        muscle_group=group,
        ex_type=ex_type,
        equipment=equipment,
        level=level,
        goal=goal,
        used_names=used_names,
        count=top_n * 2,  # беремо із запасом, відсортуємо і відріжемо top_n
        priority_pattern=missing_pattern,
        priority_muscle=group,
    )

    scored = [
        (get_exercise_score(ex, level, ex_type, goal, muscle_group=group, priority_pattern=missing_pattern,
                            family_counts=family_counts), ex)
        for ex in found
    ]
    scored.sort(key=lambda t: t[0], reverse=True)

    cost = compute_replacement_cost(target_ex, program[day_num]["exercises"], exercise_index)
    candidates = [
        Candidate(exercise=ex, day_num=day_num, exercise_index=exercise_index, replacement_cost=cost, raw_score=score)
        for score, ex in scored[:top_n]
    ]
    return candidates


class ReplaceExerciseStrategy:
    """Єдина поки що реалізована Strategy. can_handle визначає, чи
    ця стратегія береться за проблему — зараз лише source='coverage'."""

    name = "replace_exercise"

    @staticmethod
    def can_handle(problem) -> bool:
        return problem.source == "coverage"

    @staticmethod
    def generate(problem, program: dict, level: int, equipment: list, goal: str, top_n: int = 5) -> list:
        return generate_candidates(problem, program, level, equipment, goal, top_n)


class AdjustSetsStrategy:
    """ЗАГЛУШКА — не реалізовано. Вирішувала б MRV/Push-Pull/Quad-Ham
    через зміну кількості сетів, а не заміну вправи. Явно не
    приймає жодної проблеми, щоб оркестратор коректно позначав такі
    Problem як 'неоптимізовувані' замість мовчазного пропуску."""

    name = "adjust_sets"

    @staticmethod
    def can_handle(problem) -> bool:
        return False

    @staticmethod
    def generate(problem, program: dict, level: int, equipment: list, goal: str, top_n: int = 5) -> list:
        raise NotImplementedError("AdjustSetsStrategy ще не реалізовано")


STRATEGIES = [ReplaceExerciseStrategy, AdjustSetsStrategy]