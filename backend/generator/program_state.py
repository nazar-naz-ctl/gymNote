"""
ProgramState — єдиний знімок стану програми
═════════════════════════════════════════════
Для Optimization Engine 2.0: один об'єкт, що інкапсулює програму
разом з УСІМА вже порахованими похідними метриками (Coverage,
Validator issues, Intelligence Score, Weekly Balance Score).

Мета: жоден компонент Optimization Engine (Candidate Generator,
Evaluator, оркестратор циклу) не рахує метрики самостійно і
незалежно — усі читають один спільний ProgramState. Це і дає
"безкоштовний відкат": якщо кандидат не підходить, просто викидаємо
його ProgramState — оригінал жодного разу не мутувався.

validate_program() (validator.py) вже сам викликає
compute_muscle_coverage() + compute_intelligence_score() +
compute_weekly_balance_score() і повертає все в одному звіті —
ProgramState лише консолідує це в одну зручну структуру з разом
збереженими вхідними параметрами (level/equipment/goal), які
знадобляться, якщо доведеться перевалідувати ще раз після заміни.
"""

from dataclasses import dataclass, field
from copy import deepcopy

from .validator import validate_program


@dataclass(frozen=True)
class ProgramState:
    program: dict
    level: int
    equipment: list
    goal: str

    report: dict = field(repr=False)

    @property
    def score(self) -> int:
        return self.report["score"]

    @property
    def intelligence_score(self) -> float:
        return self.report["intelligence_score"]

    @property
    def weekly_balance_score(self) -> float:
        return self.report["weekly_balance_score"]

    @property
    def issues(self) -> list:
        return self.report["issues"]

    @property
    def muscle_coverage(self) -> dict:
        return self.report["muscle_coverage"]

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    def __repr__(self) -> str:
        return (
            f"ProgramState(intelligence={self.intelligence_score:.1f}, "
            f"weekly_balance={self.weekly_balance_score:.1f}, "
            f"score={self.score}, issues={self.issue_count})"
        )


def build_program_state(program: dict, level: int, equipment: list, goal: str = None) -> ProgramState:
    """
    Будує ProgramState з нуля — повний перерахунок усіх метрик через
    validate_program(). Викликається один раз одразу після генерації,
    і повторно ПІСЛЯ КОЖНОЇ пробної локальної заміни (тимчасова копія
    програми, ще не застосована остаточно).
    """
    report = validate_program(program, level=level, equipment=equipment, goal=goal)
    return ProgramState(program=program, level=level, equipment=equipment, goal=goal, report=report)


def build_trial_state(base_state: ProgramState, modified_program: dict) -> ProgramState:
    """
    Зручний ярлик для Evaluator: будує новий ProgramState для
    ЗМІНЕНОЇ копії програми, перевикористовуючи ті самі level/
    equipment/goal, що й у базового стану. Не мутує base_state.
    """
    return build_program_state(modified_program, base_state.level, base_state.equipment, base_state.goal)


def deep_copy_program(program: dict) -> dict:
    """
    Глибока копія програми для пробної заміни — Evaluator НІКОЛИ не
    змінює оригінальний program напряму, тільки цю копію. Окрема
    функція (а не голий deepcopy() у викликах), щоб було одне явне
    місце для майбутньої оптимізації (deepcopy на великій структурі
    програми може стати вузьким місцем при частих ітераціях —
    тоді заміна реалізації тут не вимагатиме правок деінде).
    """
    return deepcopy(program)