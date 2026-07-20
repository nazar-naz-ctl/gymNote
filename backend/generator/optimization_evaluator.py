"""
Evaluator
═════════
Для кожного кандидата: тимчасова підстановка в копію програми →
повний перерахунок ProgramState → порівняння з базовим станом за
трьома критеріями:

    1. Приріст ЦІЛЬОВОЇ метрики має бути ≥ MIN_IMPROVEMENT. Для
       більшості проблем цільова метрика — intelligence_score. Але
       для source="microcycle" — окремо, microcycle_score, бо
       Workout Intelligence Engine НЕ включає Microcycle Engine
       у свою зважену формулу (вони розроблялись окремо), і
       Δintelligence_score для мікроциклових замін часто випадково
       негативний/нульовий, навіть коли форма тижневої хвилі реально
       покращується — це виявлено емпірично на контрольованому тесті.
    2. weekly_balance_score НЕ повинен впасти нижче WEEKLY_BALANCE_FLOOR
    3. Не повинно з'явитись жодної НОВОЇ критичної проблеми

Серед усіх кандидатів, що пройшли ці три перевірки, обирається той
з найбільшим приростом цільової метрики / replacement_cost.
"""

from dataclasses import dataclass

from .program_state import build_trial_state
from .optimization_problems import collect_problems, PRIORITY_CRITICAL
from .microcycle import compute_microcycle_report

MIN_IMPROVEMENT = 0.5
WEEKLY_BALANCE_FLOOR = 70.0


@dataclass
class EvaluationResult:
    candidate: object
    accepted: bool
    delta_intelligence: float
    weekly_balance_after: float
    new_critical_count: int
    value_ratio: float
    rejection_reason: str = ""


def _apply_candidate_to_program(program: dict, candidate) -> dict:
    return candidate.apply(program)


def _count_critical(problems: list) -> int:
    return sum(1 for p in problems if p.priority == PRIORITY_CRITICAL)


def evaluate_candidate(problem, candidate, base_state, base_problems: list) -> EvaluationResult:
    trial_program = _apply_candidate_to_program(base_state.program, candidate)
    trial_state = build_trial_state(base_state, trial_program)

    weekly_balance_after = trial_state.weekly_balance_score

    if problem.source == "microcycle":
        base_micro = compute_microcycle_report(base_state.program)["microcycle_score"]
        trial_micro = compute_microcycle_report(trial_program)["microcycle_score"]
        delta_intelligence = round(trial_micro - base_micro, 2)
    else:
        delta_intelligence = round(trial_state.intelligence_score - base_state.intelligence_score, 2)

    trial_problems = collect_problems(trial_state)
    critical_before = _count_critical(base_problems)
    critical_after = _count_critical(trial_problems)
    new_critical_count = max(0, critical_after - critical_before)

    if delta_intelligence < MIN_IMPROVEMENT:
        return EvaluationResult(
            candidate=candidate, accepted=False,
            delta_intelligence=delta_intelligence, weekly_balance_after=weekly_balance_after,
            new_critical_count=new_critical_count, value_ratio=0.0,
            rejection_reason=f"приріст {delta_intelligence} нижче мінімального порогу {MIN_IMPROVEMENT}",
        )

    if weekly_balance_after < WEEKLY_BALANCE_FLOOR:
        return EvaluationResult(
            candidate=candidate, accepted=False,
            delta_intelligence=delta_intelligence, weekly_balance_after=weekly_balance_after,
            new_critical_count=new_critical_count, value_ratio=0.0,
            rejection_reason=f"weekly_balance впав до {weekly_balance_after} (поріг {WEEKLY_BALANCE_FLOOR})",
        )

    if new_critical_count > 0:
        return EvaluationResult(
            candidate=candidate, accepted=False,
            delta_intelligence=delta_intelligence, weekly_balance_after=weekly_balance_after,
            new_critical_count=new_critical_count, value_ratio=0.0,
            rejection_reason=f"з'явилось {new_critical_count} нових критичних проблем",
        )

    cost = candidate.replacement_cost if candidate.replacement_cost > 0 else 1.0
    value_ratio = round(delta_intelligence / cost, 3)

    return EvaluationResult(
        candidate=candidate, accepted=True,
        delta_intelligence=delta_intelligence, weekly_balance_after=weekly_balance_after,new_critical_count=new_critical_count, value_ratio=value_ratio,
    )


def evaluate_all_and_pick_best(problem, candidates: list, base_state, base_problems: list):
    all_results = [evaluate_candidate(problem, c, base_state, base_problems) for c in candidates]
    accepted = [r for r in all_results if r.accepted]
    if not accepted:
        return None, all_results
    best = max(accepted, key=lambda r: r.value_ratio)
    return best, all_results