"""
Optimization Strategies
════════════════════════
ReplaceExerciseStrategy: заміна однієї вправи в межах тієї самої
м'язової групи — вирішує Coverage-проблеми (source="coverage").

AdjustSetsStrategy: зміна кількості підходів у вже наявних вправах —
вирішує:
    - Push/Pull дисбаланс (source="validator_push_pull")
    - Quad/Ham дисбаланс (source="validator_quad_ham")
    - Joint Balance перевантаження (source="validator_joint_balance") —
      знімає сети з вправ, що навантажують саме перевантажений
      тип суглоба (JOINT_TYPE_BY_PATTERN з validator.py)
    - Compound/Isolation невідповідність цілі (source="validator_compound_ratio") —
      визначає напрямок дисбалансу (забагато compound чи забагато
      isolation відносно цільового співвідношення для цілі
      користувача) і ріже сети саме тієї категорії, що в надлишку
    - Microcycle (source="microcycle") — знімає сети з конкретного
      "цільового" важкого дня (другий день пари high/high)
"""

from dataclasses import dataclass

from .exercise_selector import find_exercises, get_exercise_score
from .program_state import deep_copy_program
from .validator import PUSH_PATTERNS, PULL_PATTERNS, JOINT_TYPE_BY_PATTERN, TARGET_COMPOUND_RATIO


EX_TYPE_COST = {"base": 3, "assist": 2, "isolation": 1}
PRIMARY_LIFT_COST_MULTIPLIER = 2.0
SETS_ADJUST_COST_FACTOR = 0.5


def compute_replacement_cost(ex: dict, day_exercises: list = None, exercise_index: int = None) -> float:
    ex_type = ex.get("ex_type", "isolation")
    base_cost = EX_TYPE_COST.get(ex_type, 1)
    if ex.get("is_primary"):
        base_cost *= PRIMARY_LIFT_COST_MULTIPLIER
    return base_cost


@dataclass
class Candidate:
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


@dataclass
class BatchSetsAdjustCandidate:
    """Одна пробна зміна одночасно чіпає КІЛЬКА вправ того самого
    дня (кожній −1 сет). Потрібно для проблем на дискретних,
    ступінчастих метриках (Microcycle Score) — там зняти сет з
    ОДНІЄЇ вправи майже завжди дає Δ=0 (день не перескакує поріг
    категорії High→Medium), тоді як кілька змін разом реально
    можуть перевести день у нижчу категорію за один крок Evaluator."""
    exercise: dict
    day_num: int
    adjustments: list  # [(exercise_index, new_sets), ...]
    replacement_cost: float
    raw_score: float = 0.0

    def apply(self, program: dict) -> dict:
        trial_program = deep_copy_program(program)
        day_exercises = trial_program[self.day_num]["exercises"]
        for idx, new_sets in self.adjustments:
            day_exercises[idx]["sets"] = new_sets
        return trial_program


# ══════════════════════════════════════════════════════
# ReplaceExerciseStrategy
# ══════════════════════════════════════════════════════

def _find_target_slot(problem, program: dict):
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


def _build_sets_adjust_candidates(matches: list, top_n: int) -> list:
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


def _generate_microcycle_batch_candidates(target_day: int, program: dict, top_n: int) -> list:
    """Для проблеми Microcycle генерує кілька ПАКЕТНИХ кандидатів —
    кожен знімає по 1 сету одразу з N найдешевших вправ цільового
    дня (N = 2, 3, 4, 5, ...). Сортує вправи за вартістю (ізоляція,
    не Primary Lift — спершу), щоб найдешевший пакет пробувався
    першим."""
    day_exercises = program[target_day].get("exercises", [])
    eligible = [
        (i, ex) for i, ex in enumerate(day_exercises) if ex.get("sets", 0) > 1
    ]
    if not eligible:
        return []

    eligible.sort(key=lambda t: compute_replacement_cost(t[1]))

    candidates = []
    max_batch = min(len(eligible), top_n + 1)
    for batch_size in range(2, max_batch + 1):
        batch = eligible[:batch_size]
        adjustments = [(i, max(1, ex.get("sets", 1) - 1)) for i, ex in batch]
        names = ", ".join(ex["name"] for _, ex in batch)
        total_cost = sum(compute_replacement_cost(ex) for _, ex in batch) * SETS_ADJUST_COST_FACTOR

        candidates.append(BatchSetsAdjustCandidate(
            exercise={"name": f"−1 сет одразу у {batch_size} вправ ({names})"},
            day_num=target_day,
            adjustments=adjustments,
            replacement_cost=total_cost,
        ))

    return candidates[:top_n]


def generate_sets_adjust_candidates(problem, program: dict, goal: str = None, top_n: int = 5) -> list:
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

    elif problem.source == "validator_joint_balance":
        overloaded_joint = problem.affected_patterns[0] if problem.affected_patterns else None
        matches = [
            (d, i, ex) for d, i, ex in _iter_program_exercises(program)
            if JOINT_TYPE_BY_PATTERN.get(ex.get("movement_pattern")) == overloaded_joint and ex.get("sets", 0) > 1
        ]

    elif problem.source == "validator_compound_ratio":
        target = TARGET_COMPOUND_RATIO.get(goal) if goal else None
        if target is None:
            return []

        all_exercises = list(_iter_program_exercises(program))
        compound_sets = sum(ex.get("sets", 0) for _, _, ex in all_exercises if ex.get("compound"))
        isolation_sets = sum(ex.get("sets", 0) for _, _, ex in all_exercises if not ex.get("compound"))
        total = compound_sets + isolation_sets
        if total == 0:
            return []
        ratio = compound_sets / total

        if ratio > target:
            matches = [(d, i, ex) for d, i, ex in all_exercises if ex.get("compound") and ex.get("sets", 0) > 1]
        else:
            matches = [(d, i, ex) for d, i, ex in all_exercises if not ex.get("compound") and ex.get("sets", 0) > 1]

    elif problem.source == "microcycle":
        target_day = problem.target_day
        if target_day is None or target_day not in program:
            return []
        return _generate_microcycle_batch_candidates(target_day, program, top_n)

    else:
        return []

    return _build_sets_adjust_candidates(matches, top_n)


class AdjustSetsStrategy:
    """Друга робоча стратегія — вирішує Push/Pull, Quad/Ham, Joint
    Balance, Compound/Isolation та Microcycle дисбаланси зменшенням
    обсягу надлишкової сторони."""

    name = "adjust_sets"

    @staticmethod
    def can_handle(problem) -> bool:
        return problem.source in (
            "validator_push_pull",
            "validator_quad_ham",
            "validator_joint_balance",
            "validator_compound_ratio",
            "microcycle",
        )

    @staticmethod
    def generate(problem, program: dict, level: int, equipment: list, goal: str, top_n: int = 5) -> list:
        return generate_sets_adjust_candidates(problem, program, goal=goal, top_n=top_n)


STRATEGIES = [ReplaceExerciseStrategy, AdjustSetsStrategy]
