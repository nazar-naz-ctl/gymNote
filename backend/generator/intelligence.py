"""
Workout Intelligence Engine
═══════════════════════════════
Не нова перевірка, а ОБ'ЄДНАННЯ всього, що вже є в Validator
(Push/Pull, Quad/Ham, Compound/Isolation, Diversity, Joint Balance,
Muscle Coverage) плюс нове — Horizontal/Vertical Balance — в один
підсумковий Intelligence Score.

Головна відмінність від звичайного report["score"]: той — штрафна
оцінка (100 мінус довільні штрафи за кожну проблему, де серйозність
штрафу підібрана вручну). Intelligence Score — зважене СЕРЕДНЄ семи
незалежних під-оцінок (кожна своя 0-100), тому краще показує, В
ЯКОМУ САМЕ вимірі програма слабка, а не лише загальний "щось не так".
"""

HORIZONTAL_PATTERNS = {
    "horizontal_press", "horizontal_pull", "decline_press", "incline_press",
}
VERTICAL_PATTERNS = {
    "vertical_press", "vertical_pull", "vertical_pull_explosive",
}

WEIGHTS = {
    "push_pull": 0.15,
    "horizontal_vertical": 0.15,
    "quad_ham": 0.15,
    "compound_isolation": 0.15,
    "diversity": 0.15,
    "joint_balance": 0.15,
    "coverage": 0.10,
}


def _balance_subscore(a: float, b: float, low: float = 0.35, high: float = 0.65) -> float:
    """100, якщо співвідношення a/(a+b) в межах [low, high]; інакше
    штраф пропорційний відхиленню за межу."""
    total = a + b
    if total == 0:
        return 100.0
    ratio = a / total
    if low <= ratio <= high:
        return 100.0
    deviation = (low - ratio) if ratio < low else (ratio - high)
    return max(0.0, 100.0 - deviation * 300)


def compute_horizontal_vertical(program: dict) -> tuple:
    """Повертає (horizontal_sets, vertical_sets) за весь тиждень."""
    h_sets, v_sets = 0, 0
    for day in program.values():
        for ex in day.get("exercises", []):
            pattern = ex.get("movement_pattern")
            sets = ex.get("sets", 0)
            if pattern in HORIZONTAL_PATTERNS:
                h_sets += sets
            elif pattern in VERTICAL_PATTERNS:
                v_sets += sets
    return h_sets, v_sets


def compute_intelligence_score(report: dict, program: dict) -> dict:
    """
    Приймає вже готовий report від validate_program() (з push_sets,
    pull_sets, quad_sets, ham_sets, diversity_by_day, joint_totals,
    compound_ratio, muscle_coverage) і сам program (для
    Horizontal/Vertical, якого ще нема в report). Повертає
    {"intelligence_score": 0-100, "breakdown": {...}}.
    """
    breakdown = {}

    breakdown["push_pull"] = _balance_subscore(report.get("push_sets", 0), report.get("pull_sets", 0))
    breakdown["quad_ham"] = _balance_subscore(report.get("quad_sets", 0), report.get("ham_sets", 0), 0.3, 0.7)

    h_sets, v_sets = compute_horizontal_vertical(program)
    breakdown["horizontal_vertical"] = _balance_subscore(h_sets, v_sets)

    compound_ratio = report.get("compound_ratio")
    breakdown["compound_isolation"] = 100.0 if compound_ratio is None else max(0.0, 100.0 - abs(compound_ratio - 0.5) * 200)

    diversity_values = list(report.get("diversity_by_day", {}).values())
    breakdown["diversity"] = round(sum(diversity_values) / len(diversity_values) * 100, 1) if diversity_values else 100.0

    joint_totals = report.get("joint_totals", {})
    if joint_totals and len(joint_totals) > 1:
        max_value = max(joint_totals.values())
        others_avg = (sum(joint_totals.values()) - max_value) / (len(joint_totals) - 1)
        breakdown["joint_balance"] = 100.0 if others_avg == 0 else max(0.0, 100.0 - max(0.0, (max_value / others_avg - 1)) * 40)
    else:
        breakdown["joint_balance"] = 100.0

    coverage = report.get("muscle_coverage", {})
    coverage_values = [d["score"] for d in coverage.values()]
    breakdown["coverage"] = round(sum(coverage_values) / len(coverage_values) * 100, 1) if coverage_values else 100.0

    intelligence_score = round(sum(breakdown[k] * WEIGHTS[k] for k in WEIGHTS), 1)

    return {
        "intelligence_score": intelligence_score,
        "breakdown": {k: round(v, 1) for k, v in breakdown.items()},
    }