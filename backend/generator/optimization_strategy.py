"""
Optimization Strategies
════════════════════════
ReplaceExerciseStrategy: заміна однієї вправи в межах тієї самої
м'язової групи — вирішує Coverage-проблеми (source="coverage").

AdjustSetsStrategy: зміна кількості підходів у вже наявних вправах —
вирішує Push/Pull і Quad/Ham дисбаланс (source="validator_push_pull",
"validator_quad_ham"). Не чіпає саму вправу, лише зменшує сети на
"надлишковій" стороні дисбалансу — це м'якше, дешевше втручання, ніж
заміна вправи, і природно підходить для проблем, які за суттю є
"забагато обсягу тут відносно там", а не "неправильна вправа".

Обидва типи кандидатів (Candidate, SetsAdjustCandidate) мають метод
apply(program) — самі знають, як застосувати себе до копії програми.
Це дозволяє Evaluator/оркестратору працювати з кандидатами уніфіковано,
не знаючи деталей конкретної стратегії.
"""

from dataclasses import dataclass, field

from .exercise_selector import find_exercises, get_exercise_score
from .program_state import deep_copy_program
from .validator import PUSH_PATTERNS, PULL_PATTERNS


# Вага "вартості заміни" за типом слоту — вища вартість = сильніше
# втручання в програму, при рівних умовах оптимізатор має обирати
# дешевшу заміну.
EX_TYPE_COST = {"base": 3, "assist": 2, "isolation": 1}
PRIMARY_LIFT_COST_MULTIPLIER = 2.0  # заміна Primary Lift (🎯) — найдорожче втручання
SETS_ADJUST_COST_FACTOR = 0.5  # зміна сетів дешевша за повну заміну вправи


def compute_replacement_cost(ex: dict, day_exercises: list = None, exercise_index: int = None) -> float:
    """
    Вартість заміни/коригування конкретної вправи. База — вага типу
    слоту (base > assist > isolation). Якщо вправа позначена як
    Primary Lift (🎯) — додатковий множник. day_exercises/exercise_index
    лишені в сигнатурі для сумісності виклику, самі не використовуються.
    """
    ex_type = ex.get("ex_type", "isolation")
    base_cost = EX_TYPE_COST.get(ex_type, 1)
    if ex.get("is_primary"):
        base_cost *= PRIMARY_LIFT_COST_MULTIPLIER
    return base_cost


@dataclass
class Candidate:
    """Кандидат ReplaceExerciseStrategy — заміна вправи в конкретному слоті."""
    exercise: dict
    day_num: int
    exercise_index: int
    replacement_cost: float
    raw_score: float

    def apply(self, program: dict) -> dict:
        trial_program = deep_copy_program(program)
        day_exercises = trial_program[self.day_num]["exercises"]
        old_ex = day_exercises[self.exercise_index]

        new_ex = self.exercise.copy()
        for key in ("sets", "reps", "ex_type", "_group", "is_primary", "intent", "superset_id"):
            if key in old_ex:
                new_ex[key] = old_ex[key]

        day_exercises[self.exercise_index] = new_ex
        return trial_program


@dataclass
class SetsAdjustCandidate:
    """Кандидат AdjustSetsStrategy — зміна кількості сетів наявної
    вправи, без заміни самої вправи. exercise — dict лише для
    відображення в логах ({"name": "Опис зміни..."})."""
    exercise: dict
    day_num: int
    exercise_index: int
    replacement_cost: float
    new_sets: int
    raw_score: float = 0.0

    def apply(self, program: dict) -> dict:
        trial_program = deep_copy_program(program)
        trial_program[self.day_num]["exercises"][self.exercise_index]["sets"] = self.new_sets
        return trial_program


# ══════════════════════════════════════════════════════
# ReplaceExerciseStrategy
# ══════════════════════════════════════════════════════

def _find_target_slot(problem, program: dict):
    """
    Для Coverage-проблеми: знаходить конкретну вправу в програмі, яку
    варто спробувати замінити. Пріоритет — вправа, чий патерн уже
    дублюється іншою вправою тієї самої групи десь у тижні. Якщо
    дубліката нема — беремо вправу з найдешевшим replacement_cost.
    """
    if not problem.affected_muscles:
        return None
    group = problem.affected_muscles[0]

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

    duplicated = [
        (d, i, ex) for d, i, ex in group_slots
        if pattern_counts.get(ex.get("movement_pattern"), 0) > 1
    ]
    pool = duplicated if duplicated else group_slots

    pool_sorted = sorted(pool, key=lambda t: compute_replacement_cost(t[2]))
    return pool_sorted[0]


def generate_candidates(problem, program: dict, level: int, equipment: list, goal: str, top_n: int = 5) -> list:
    """Для Coverage-проблеми: генерує до top_n кандидатів на заміну
    конкретного знайденого слоту, відсортованих за Exercise Score."""
    target = _find_target_slot(problem, program)
    if target is None:
        return []

    day_num, exercise_index, target_ex = target
    group = target_ex.get("_group")
    ex_type = target_ex.get("ex_type", "isolation")
    missing_pattern = problem.affected_patterns[0] if problem.affected_patterns else None

    used_names = set()
    for day in program.values():
        for ex in day.get("exercises", []):
            if ex is not target_ex:
                used_names.add(ex["name"])

    family_counts = {}

    found = find_exercises(
        muscle_group=group,
        ex_type=ex_type,
        equipment=equipment,
        level=level,
        goal=goal,
        used_names=used_names,
        count=top_n * 2,
        priority_pattern=missing_pattern,
        priority_muscle=group,
    )

    scored = [
        (get_exercise_score(ex, level, ex_type, goal, muscle_group=group, priority_pattern=missing_pattern, family_counts=family_counts), ex)
        for ex in found
    ]
    scored.sort(key=lambda t: t[0], reverse=True)

    cost = compute_replacement_cost(target_ex)
    candidates = [
        Candidate(exercise=ex, day_num=day_num, exercise_index=exercise_index, replacement_cost=cost, raw_score=score)
        for score, ex in scored[:top_n]
    ]
    return candidates


class ReplaceExerciseStrategy:
    name = "replace_exercise"

    @staticmethod
    def can_handle(problem) -> bool:
        return problem.source == "coverage"

    @staticmethod
    def generate(problem, program: dict, level: int, equipment: list, goal: str, top_n: int = 5) -> list:
        return generate_candidates(problem, program, level, equipment, goal, top_n)


# ══════════════════════════════════════════════════════
# AdjustSetsStrategy
# ══════════════════════════════════════════════════════

def _iter_program_exercises(program: dict):
    for day_num, day in program.items():
        for idx, ex in enumerate(day.get("exercises", [])):
            yield day_num, idx, ex


def generate_sets_adjust_candidates(problem, program: dict, top_n: int = 5) -> list:
    """
    Для Push/Pull або Quad/Ham дисбалансу: знаходить вправи на
    "надлишковій" стороні дисбалансу (problem.affected_patterns[0]
    для push/pull, problem.affected_muscles[0] для quad/ham) і
    пропонує зменшити їхній обсяг на 1 сет — по одній вправі за
    кандидата, дешевші (isolation, не Primary Lift) спершу.
    """
    if problem.source == "validator_push_pull":
        excess_side = problem.affected_patterns[0] if problem.affected_patterns else None
        pattern_set = PUSH_PATTERNS if excess_side == "push" else PULL_PATTERNS
        matches = [
            (d, i, ex) for d, i, ex in _iter_program_exercises(program)
            if ex.get("movement_pattern") in pattern_set and ex.get("sets", 0) > 1
        ]
    elif problem.source == "validator_quad_ham":
        excess_group = problem.affected_muscles[0] if problem.affected_muscles else None
        matches = [
            (d, i, ex) for d, i, ex in _iter_program_exercises(program)
            if ex.get("_group") == excess_group and ex.get("sets", 0) > 1
        ]
    else:
        return []

    matches.sort(key=lambda t: compute_replacement_cost(t[2]))

    candidates = []
    for d, i, ex in matches[:top_n]:
        old_sets = ex.get("sets", 1)
        new_sets = max(1, old_sets - 1)
        if new_sets == old_sets:
            continue
        cost = compute_replacement_cost(ex) * SETS_ADJUST_COST_FACTOR
        candidates.append(SetsAdjustCandidate(
            exercise={"name": f"{ex['name']}: {old_sets}→{new_sets} сетів"},
            day_num=d,
            exercise_index=i,
            replacement_cost=cost,
            new_sets=new_sets,
        ))
    return candidates


class AdjustSetsStrategy:
    """Друга робоча стратегія — вирішує Push/Pull і Quad/Ham
    дисбаланс зменшенням обсягу надлишкової сторони."""

    name = "adjust_sets"

    @staticmethod
    def can_handle(problem) -> bool:
        return problem.source in ("validator_push_pull", "validator_quad_ham")

    @staticmethod
    def generate(problem, program: dict, level: int, equipment: list, goal: str, top_n: int = 5) -> list:
        return generate_sets_adjust_candidates(problem, program, top_n=top_n)


STRATEGIES = [ReplaceExerciseStrategy, AdjustSetsStrategy]
