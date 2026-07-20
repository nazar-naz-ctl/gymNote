"""
Problem — уніфікований опис проблеми програми для Optimization Engine
════════════════════════════════════════════════════════════════════
Джерела проблем (усі вже існують, тут лише консолідуються в один
формат): Coverage gaps (недобір/відсутність патерну), Push/Pull і
Quad/Ham дисбаланс, Compound/Isolation невідповідність цілі,
Joint Balance перевищення, Microcycle (пари важких днів поспіль).

priority — критичний/важливий/бажаний, визначає порядок обробки в
оркестраторі циклу (спершу критичні).
severity — 0.0-1.0, наскільки далеко показник від норми (для
сортування ВСЕРЕДИНІ одного priority — не лише "яка категорія", а
"наскільки погано конкретно ця проблема").
"""

from dataclasses import dataclass, field

from .microcycle import compute_microcycle_report


PRIORITY_CRITICAL = "критичний"
PRIORITY_IMPORTANT = "важливий"
PRIORITY_DESIRABLE = "бажаний"

_PRIORITY_ORDER = {PRIORITY_CRITICAL: 0, PRIORITY_IMPORTANT: 1, PRIORITY_DESIRABLE: 2}


@dataclass
class Problem:
    priority: str
    severity: float          # 0.0-1.0, вище = гірше
    reason: str               # людинозрозумілий опис (для логів)
    source: str               # "coverage" | "validator_push_pull" | "validator_quad_ham" |
                              # "validator_compound_ratio" | "validator_joint_balance" |
                              # "microcycle"
    affected_muscles: list = field(default_factory=list)
    affected_patterns: list = field(default_factory=list)
    target_slot: tuple = None  # (day_num, exercise_index) — заповнюється пізніше
                                # Candidate Generator'ом, коли відомо КОНКРЕТНУ вправу для заміни
    target_day: int = None     # для microcycle-проблем — конкретний день, з якого треба
                                # знімати навантаження (другий день пари high/high)

    def sort_key(self):
        return (_PRIORITY_ORDER.get(self.priority, 99), -self.severity)


def collect_problems(state) -> list:
    """
    Формує повний список Problem з готового ProgramState.
    Не мутує state. Повертає список, відсортований за пріоритетом
    (критичні спершу), а всередині пріоритету — за severity (гірші спершу).
    """
    problems = []
    report = state.report

    # ── Coverage gaps ──────────────────────────────────────────
    for group, data in state.muscle_coverage.items():
        if data["score"] >= 0.5:
            continue
        missing = sorted(data["missing"])
        severity = round(1.0 - data["score"], 2)
        priority = PRIORITY_CRITICAL if data["score"] == 0.0 else PRIORITY_DESIRABLE
        problems.append(Problem(
            priority=priority,
            severity=severity,
            reason=f"Недостатнє покриття «{group}» ({int(data['score']*100)}%) — бракує: {', '.join(missing)}",
            source="coverage",
            affected_muscles=[group],
            affected_patterns=missing,
        ))

    # ── Push/Pull дисбаланс ────────────────────────────────────
    push = report.get("push_sets", 0)
    pull = report.get("pull_sets", 0)
    if push or pull:
        total = push + pull
        ratio = push / total
        if ratio > 0.65 or ratio < 0.35:
            severity = round(abs(ratio - 0.5) * 2, 2)
            problems.append(Problem(
                priority=PRIORITY_IMPORTANT,
                severity=severity,
                reason=f"Дисбаланс Push/Pull: {push} push проти {pull} pull підходів",
                source="validator_push_pull",
                affected_patterns=["push" if ratio > 0.5 else "pull"],
            ))

    # ── Quad/Ham дисбаланс ──────────────────────────────────────
    quad = report.get("quad_sets", 0)
    ham = report.get("ham_sets", 0)
    if quad or ham:
        total = quad + ham
        ratio = quad / total
        if ratio > 0.7 or ratio < 0.3:
            severity = round(abs(ratio - 0.5) * 2, 2)
            problems.append(Problem(
                priority=PRIORITY_IMPORTANT,
                severity=severity,
                reason=f"Дисбаланс Квадрицепс/Задня поверхня стегна: {quad} проти {ham} підходів",
                source="validator_quad_ham",
                affected_muscles=["квадрицепс" if ratio > 0.5 else "біцепс стегна"],
            ))

    # ── Joint Balance ───────────────────────────────────────────
    joint_totals = report.get("joint_totals") or {}
    if len(joint_totals) > 1:
        max_joint = max(joint_totals, key=joint_totals.get)
        max_value = joint_totals[max_joint]
        others_avg = sum(v for k, v in joint_totals.items() if k != max_joint) / (len(joint_totals) - 1)
        if others_avg > 0 and max_value > others_avg * 2.5:
            severity = round(min(1.0, (max_value / others_avg - 2.5) / 2.5), 2)
            problems.append(Problem(
                priority=PRIORITY_CRITICAL,
                severity=severity,
                reason=f"Дисбаланс навантаження на суглоби: «{max_joint}» перевантажені ({joint_totals})",
                source="validator_joint_balance",
                affected_patterns=[max_joint],
            ))

    # ── Compound/Isolation ───────────────────────────────────────
    compound_ratio = report.get("compound_ratio")
    if compound_ratio is not None and state.goal:
        from .validator import TARGET_COMPOUND_RATIO, COMPOUND_RATIO_TOLERANCE
        target = TARGET_COMPOUND_RATIO.get(state.goal)
        if target is not None and abs(compound_ratio - target) > COMPOUND_RATIO_TOLERANCE:
            severity = round(min(1.0, abs(compound_ratio - target) / 0.5), 2)
            problems.append(Problem(
                priority=PRIORITY_DESIRABLE,
                severity=severity,
                reason=f"Compound/Isolation не відповідає цілі «{state.goal}»: {int(compound_ratio*100)}% (орієнтир ~{int(target*100)}%)",
                source="validator_compound_ratio",
            ))

    # ── Microcycle (пари важких днів поспіль) ────────────────────
    micro = compute_microcycle_report(state.program)
    for day1, day2 in micro["consecutive_high_pairs"]:
        problems.append(Problem(
            priority=PRIORITY_IMPORTANT,
            severity=0.6,
            reason=f"Дні {day1} і {day2} поспіль мають високе навантаження (Microcycle Score={micro['microcycle_score']})",
            source="microcycle",
            target_day=day2,
        ))

    problems.sort(key=lambda p: p.sort_key())
    return problems
