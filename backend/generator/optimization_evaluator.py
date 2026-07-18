"""
Evaluator — Крок 4
═══════════════════
Для кожного кандидата: тимчасова підстановка в копію програми →
повний перерахунок ProgramState → порівняння з базовим станом за
трьома критеріями:

    1. Δintelligence_score має бути ≥ MIN_IMPROVEMENT (інакше приріст
       занадто дрібний, щоб виправдати втручання — захист від
       нескінченних дрібних коливань через random.uniform шум у
       Score Engine)
    2. weekly_balance_score НЕ повинен впасти нижче WEEKLY_BALANCE_FLOOR
       (жорстке обмеження — навіть велике покращення Intelligence не
       виправдовує підрив тижневого балансу обсягу/втоми)
    3. Не повинно з'явитись жодної НОВОЇ критичної проблеми (перевірка
       через повторний collect_problems на trial-стані)

Серед усіх кандидатів, що пройшли ці три перевірки, обирається той
з найбільшим Δintelligence_score / replacement_cost (найбільший
приріст на одиницю "втручання" в програму).
"""

from dataclasses import dataclass, field

from .program_state import build_trial_state, deep_copy_program
from .optimization_problems import collect_problems, PRIORITY_CRITICAL

MIN_IMPROVEMENT = 0.5
WEEKLY_BALANCE_FLOOR = 70.0


@dataclass
class EvaluationResult:
    candidate: object          # Candidate з optimization_strategy.py
    accepted: bool
    delta_intelligence: float
    weekly_balance_after: float
    new_critical_count: int
    value_ratio: float          # delta_intelligence / cost, лише якщо accepted
    rejection_reason: str = ""  # заповнено, якщо accepted=False


def _apply_candidate_to_program(program: dict, candidate) -> dict:
    """
    Повертає НОВУ (глибоку копію) програму із заміненою одною вправою
    в target-слоті. Оригінальна структурна інформація слоту (sets,
    reps, ex_type, _group, is_primary, superset_id) переноситься з
    вправи, яку заміняємо — кандидат дає лише "хто" (назва/метадані
    з бази), не "скільки підходів"/"яка роль у тренуванні".
    """
    trial_program = deep_copy_program(program)
    day_exercises = trial_program[candidate.day_num]["exercises"]
    old_ex = day_exercises[candidate.exercise_index]

    new_ex = candidate.exercise.copy()
    for key in ("sets", "reps", "ex_type", "_group", "is_primary", "intent", "superset_id"):
        if key in old_ex:
            new_ex[key] = old_ex[key]

    day_exercises[candidate.exercise_index] = new_ex
    return trial_program


def _count_critical(problems: list) -> int:
    return sum(1 for p in problems if p.priority == PRIORITY_CRITICAL)


def evaluate_candidate(problem, candidate, base_state, base_problems: list) -> EvaluationResult:
    """
    Оцінює ОДНОГО кандидата. Не мутує base_state.program.
    base_problems — список Problem з базового стану (ДО заміни),
    потрібен для порівняння кількості критичних проблем до/після.
    """
    trial_program = _apply_candidate_to_program(base_state.program, candidate)
    trial_state = build_trial_state(base_state, trial_program)

    delta_intelligence = round(trial_state.intelligence_score - base_state.intelligence_score, 2)
    weekly_balance_after = trial_state.weekly_balance_score

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
            new_critical_count=new_critical_count, value_ratio=0.0,rejection_reason=f"weekly_balance впав до {weekly_balance_after} (поріг {WEEKLY_BALANCE_FLOOR})",
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
        delta_intelligence=delta_intelligence, weekly_balance_after=weekly_balance_after,
        new_critical_count=new_critical_count, value_ratio=value_ratio,
    )


def evaluate_all_and_pick_best(problem, candidates: list, base_state, base_problems: list):
    """
    Оцінює всіх кандидатів для однієї Problem. Повертає
    (best_result_or_None, all_results) — all_results потрібен для
    детального логування (чому саме цей переміг, чому інші відхилено).
    """
    all_results = [evaluate_candidate(problem, c, base_state, base_problems) for c in candidates]
    accepted = [r for r in all_results if r.accepted]
    if not accepted:
        return None, all_results
    best = max(accepted, key=lambda r: r.value_ratio)
    return best, all_results