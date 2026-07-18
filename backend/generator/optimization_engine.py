"""
Optimization Engine 2.0 — Крок 5: оркестратор циклу
════════════════════════════════════════════════════
Об'єднує всі попередні кроки в замкнений цикл самокорекції:

    Generate → Validate → Optimize → Validate → Optimize → ... → Output

На кожній ітерації:
    1. Будуємо ProgramState "з нуля" (актуальний стан після
       попередніх застосованих замін)
    2. Збираємо всі Problem, сортуємо за пріоритетом
    3. Беремо найвищу пріоритетну Problem, яку ще НЕ позначено
       "неоптимізовуваною"
    4. Шукаємо Strategy, що її обробляє; якщо нема — позначаємо
       неоптимізовуваною, переходимо до наступної проблеми
    5. Генеруємо кандидатів, оцінюємо всіх через Evaluator
    6. Якщо є переможець — застосовуємо ЛОКАЛЬНО (одна заміна),
       програма оновлюється; якщо нема — позначаємо Problem
       неоптимізовуваною
    7. Повторюємо, поки є необроблені Problem і не досягнуто
       MAX_ITERATIONS

Проблеми ідентифікуються "підписом" (source + affected_muscles +
affected_patterns), а не об'єктом — бо Problem перебудовується
заново з нуля щоразу (стан програми змінюється після кожної заміни),
і той самий Python-об'єкт Problem не переживає ітерацію.
"""

from .program_state import build_program_state
from .optimization_problems import collect_problems
from .optimization_strategy import STRATEGIES
from .optimization_evaluator import evaluate_all_and_pick_best, _apply_candidate_to_program

MAX_ITERATIONS = 15


def _problem_signature(problem) -> tuple:
    return (
        problem.source,
        tuple(sorted(problem.affected_muscles)),
        tuple(sorted(problem.affected_patterns)),
    )


def optimize_program(program: dict, level: int, equipment: list, goal: str = None, max_iterations: int = MAX_ITERATIONS):
    """
    Головна точка входу. Повертає (final_program, log).

    log — список dict-ів, по одному на кожну ітерацію циклу, з
    повною деталізацією: яку проблему обрано, скільки кандидатів
    розглянуто, хто переміг і чому, хто відхилений і чому.
    """
    current_program = program
    unoptimizable_signatures = set()
    log = []

    state = build_program_state(current_program, level=level, equipment=equipment, goal=goal)
    initial_intelligence = state.intelligence_score

    for iteration in range(1, max_iterations + 1):
        state = build_program_state(current_program, level=level, equipment=equipment, goal=goal)
        problems = collect_problems(state)

        candidate_problems = [p for p in problems if _problem_signature(p) not in unoptimizable_signatures]

        if not candidate_problems:
            log.append({
                "iteration": iteration,
                "stopped": True,
                "reason": "Немає більше проблем для обробки (усі вирішені або позначені неоптимізовуваними)",
                "intelligence_score": state.intelligence_score,
            })
            break

        problem = candidate_problems[0]
        signature = _problem_signature(problem)

        entry = {
            "iteration": iteration,
            "problem": {
                "source": problem.source,
                "priority": problem.priority,
                "severity": problem.severity,
                "reason": problem.reason,
            },
            "intelligence_before": state.intelligence_score,
        }

        handler = next((s for s in STRATEGIES if s.can_handle(problem)), None)
        if handler is None:
            unoptimizable_signatures.add(signature)
            entry["outcome"] = "неоптимізовувана — жодна стратегія не обробляє цей тип проблеми"
            log.append(entry)
            continue

        candidates = handler.generate(problem, current_program, level, equipment, goal)
        entry["strategy"] = handler.name
        entry["candidates_considered"] = len(candidates)

        if not candidates:
            unoptimizable_signatures.add(signature)
            entry["outcome"] = "неоптимізовувана — стратегія не знайшла жодного кандидата"
            log.append(entry)
            continue

        best, all_results = evaluate_all_and_pick_best(problem, candidates, state, problems)

        entry["candidates_detail"] = [
            {
                "name": r.candidate.exercise["name"],
                "delta_intelligence": r.delta_intelligence,
                "weekly_balance_after": r.weekly_balance_after,
                "new_critical_count": r.new_critical_count,
                "value_ratio": r.value_ratio,
                "accepted": r.accepted,
                "rejection_reason": r.rejection_reason,
            }
            for r in all_results
        ]

        if best is None:
            unoptimizable_signatures.add(signature)
            entry["outcome"] = "неоптимізовувана — жоден з кандидатів не пройшов перевірку Evaluator"
            log.append(entry)
            continue

        current_program = _apply_candidate_to_program(current_program, best.candidate)
        new_state = build_program_state(current_program, level=level, equipment=equipment, goal=goal)

        entry["outcome"] = f"застосовано заміну: «{best.candidate.exercise['name']}»"
        entry["winner"] = best.candidate.exercise["name"]
        entry["delta_intelligence"] = best.delta_intelligence
        entry["value_ratio"] = best.value_ratio
        entry["intelligence_after"] = new_state.intelligence_score
        log.append(entry)

    else:
        log.append({
            "iteration": max_iterations + 1,
            "stopped": True,
            "reason": f"Досягнуто ліміту ітерацій ({max_iterations})",
        })

    final_state = build_program_state(current_program, level=level, equipment=equipment, goal=goal)
    log.append({
        "summary": True,
        "initial_intelligence": initial_intelligence,
        "final_intelligence": final_state.intelligence_score,
        "total_improvement": round(final_state.intelligence_score - initial_intelligence, 2),
        "iterations_used": len([e for e in log if "problem" in e]),
    })

    return current_program, log


def print_optimization_log(log: list) -> None:
    """Зручний вивід логу для тестування/дебагу в консолі."""
    for entry in log:
        if entry.get("summary"):
            print(f"\n=== ПІДСУМОК ===")
            print(f"Intelligence Score: {entry['initial_intelligence']} → {entry['final_intelligence']} "
                  f"(приріст {entry['total_improvement']})")
            print(f"Використано ітерацій: {entry['iterations_used']}")
            continue
        if entry.get("stopped"):
            print(f"\n[Ітерація {entry['iteration']}] ЗУПИНКА: {entry['reason']}")
            continue

        print(f"\n[Ітерація {entry['iteration']}] Проблема: {entry['problem']['reason']} "
              f"(priority={entry['problem']['priority']}, severity={entry['problem']['severity']})")
        if "strategy" in entry:
            print(f"  Стратегія: {entry['strategy']}, кандидатів: {entry['candidates_considered']}")
        if "candidates_detail" in entry:
            for c in entry["candidates_detail"]:
                status = "✅" if c["accepted"] else f"❌ ({c['rejection_reason']})"
                print(f"    - {c['name']}: Δintel={c['delta_intelligence']}, "
                      f"value_ratio={c['value_ratio']} {status}")
        print(f"  Результат: {entry['outcome']}")
        if "delta_intelligence" in entry:
            print(f"  Intelligence: {entry['intelligence_before']} → {entry['intelligence_after']} "
                  f"(Δ{entry['delta_intelligence']})")