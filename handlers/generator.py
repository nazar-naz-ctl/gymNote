from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import random

from database import get_user, update_user_field
from exercises_db import get_exercises

router = Router()


class GeneratorStates(StatesGroup):
    location  = State()
    equipment = State()
    goal      = State()
    level     = State()
    days      = State()


LOCATION_MAP = {
    "loc_gym":     ("зал", "🏋️ Зал"),
    "loc_home":    ("дома", "🏠 Дома"),
    "loc_outdoor": ("вулиця", "🌳 Вулиця"),
}

EQUIPMENT_MAP = {
    "eq_barbell":    "штанга",
    "eq_dumbbells":  "гантелі",
    "eq_machines":   "тренажер",
    "eq_bodyweight": "власна вага",
    "eq_bands":      "резинки",
    "eq_kettlebell": "гиря",
    "eq_pullup":     "турнік",
    "eq_bars":       "бруси",
    "eq_trx":        "TRX",
    "eq_rings":      "кільця",
}

GOAL_MAP = {
    "goal_mass":      "маса",
    "goal_relief":    "рельєф",
    "goal_strength":  "сила",
    "goal_loss":      "схуднення",
    "goal_endurance": "витривалість",
}

LEVEL_MAP = {
    "lvl_1": (1, "🟢 Початківець"),
    "lvl_2": (2, "🟡 Середній"),
    "lvl_3": (3, "🔴 Просунутий"),
    "lvl_4": (4, "🔥 Атлет"),
}

MAX_DIFFICULTY_BY_LEVEL = {1: 2, 2: 3, 3: 4, 4: 5}


def filter_by_difficulty(found: list, level: int) -> list:
    max_diff = MAX_DIFFICULTY_BY_LEVEL.get(level, 5)
    return [e for e in found if e.get("difficulty", 3) <= max_diff]


def program_to_storable(program: dict) -> list:
    return [{"day_num": k, **v} for k, v in program.items()]


def program_from_storable(data: list) -> dict:
    return {int(item["day_num"]): {kk: vv for kk, vv in item.items() if kk != "day_num"} for item in data}


# ══════════════════════════════════════════════════════
# ПІДХОДИ / ПОВТОРИ
# ══════════════════════════════════════════════════════

def get_sets_reps(ex_type: str, goal: str, level: int) -> tuple:
    table = {
        "base": {
            "маса":       {1:(3,"10-12"), 2:(4,"8-10"), 3:(4,"6-8"),  4:(4,"5-8")},
            "сила":       {1:(3,"6-8"),  2:(4,"5-6"),  3:(4,"4-6"),  4:(5,"3-5")},
            "рельєф":     {1:(3,"12-15"),2:(4,"10-12"),3:(4,"10-12"),4:(4,"10-12")},
            "схуднення":  {1:(3,"15-20"),2:(3,"15"),   3:(3,"12-15"),4:(3,"12-15")},
            "витривалість":{1:(3,"20"),  2:(3,"20"),   3:(3,"15-20"),4:(3,"15-20")},
        },
        "assist": {
            "маса":       {1:(3,"10-12"),2:(4,"10"),   3:(3,"8-10"), 4:(3,"8-10")},
            "сила":       {1:(3,"8-10"), 2:(3,"8"),    3:(3,"6-8"),  4:(3,"6-8")},
            "рельєф":     {1:(3,"12-15"),2:(3,"12"),   3:(3,"12"),   4:(3,"12-15")},
            "схуднення":  {1:(3,"15"),   2:(3,"15"),   3:(3,"15"),   4:(3,"15")},
            "витривалість":{1:(3,"20"),  2:(3,"15-20"),3:(3,"15-20"),4:(3,"15-20")},
        },
        "isolation": {
            "маса":       {1:(2,"12-15"),2:(3,"12"),   3:(3,"12-15"),4:(3,"12-15")},
            "сила":       {1:(2,"10-12"),2:(3,"10"),   3:(3,"10-12"),4:(3,"10-12")},
            "рельєф":     {1:(2,"15"),   2:(3,"15"),   3:(3,"15"),   4:(3,"15")},
            "схуднення":  {1:(2,"20"),   2:(3,"20"),   3:(3,"15-20"),4:(3,"15-20")},
            "витривалість":{1:(2,"20"),  2:(3,"20"),   3:(3,"20"),   4:(3,"20")},
        },
        "abs": {g: {l:(3,"15-20") for l in [1,2,3,4]} for g in GOAL_MAP.values()},
        "calves": {g: {1:(3,"15-20"),2:(4,"15-20"),3:(5,"15-20"),4:(6,"15-20")} for g in GOAL_MAP.values()},
        "cardio": {g: {l:(3,"20 хв") for l in [1,2,3,4]} for g in GOAL_MAP.values()},
    }
    t = table.get(ex_type, table["isolation"])
    g = t.get(goal, t.get("маса", {}))
    return g.get(level, (3, "10-12"))


# ══════════════════════════════════════════════════════
# СТРУКТУРИ ДНІВ
# ══════════════════════════════════════════════════════
# Кожен елемент: (група_м'язів, тип_вправи, кількість)
# тип: base | assist | isolation | abs | calves | cardio

DAY_STRUCTURES = {

    # ════════════════════════════
    # ЗАЛ — РІВЕНЬ 1 (ФУЛБОДІ)
    # ════════════════════════════
    "gym_full_A_1": {
        "name": "Фулбоді A",
        "structure": [
            ("квадрицепс", "base", 1),
            ("груди", "base", 1),
            ("спина_ширина", "base", 1),
            ("сідниці", "base", 1),
            ("прес", "abs", 2),
        ]
    },
    "gym_full_B_1": {
        "name": "Фулбоді B",
        "structure": [
            ("квадрицепс", "base", 1),
            ("спина_товщина", "base", 1),
            ("груди", "base", 1),
            ("біцепс стегна", "base", 1),
            ("прес", "abs", 2),
        ]
    },
    "gym_full_C_1": {
        "name": "Фулбоді C",
        "structure": [
            ("сідниці", "base", 1),
            ("груди", "base", 1),
            ("спина_ширина", "base", 1),
            ("квадрицепс", "assist", 1),
            ("прес", "abs", 2),
        ]
    },

    # ════════════════════════════
    # ЗАЛ — РІВЕНЬ 2 (ВЕРХ/НИЗ)
    # ════════════════════════════
    "gym_upper_2": {
        "name": "Верхня частина тіла",
        "structure": [
            ("груди", "base", 1),
            ("спина_товщина", "base", 1),
            ("груди", "assist", 1),
            ("плечі", "assist", 1),
            ("біцепс", "isolation", 1),
            ("трицепс", "isolation", 1),
            ("прес", "abs", 2),
        ]
    },
    "gym_lower_2": {
        "name": "Нижня частина тіла",
        "structure": [
            ("квадрицепс", "base", 1),
            ("біцепс стегна", "base", 1),
            ("квадрицепс", "assist", 1),
            ("сідниці", "assist", 1),
            ("литки", "calves", 2),
            ("прес", "abs", 2),
        ]
    },

    # ════════════════════════════
    # ЗАЛ — РІВЕНЬ 3 (СПЛІТ)
    # ════════════════════════════
    "gym_chest_tri_3": {
        "name": "Груди + Трицепс",
        "structure": [
            ("груди", "base", 2),
            ("груди", "assist", 1),
            ("груди", "isolation", 1),
            ("трицепс", "base", 1),
            ("трицепс", "isolation", 2),
            ("прес", "abs", 2),
        ]
    },
    "gym_back_bi_3": {
        "name": "Спина + Біцепс",
        "structure": [
            ("спина_товщина", "base", 2),
            ("спина_ширина", "assist", 1),
            ("спина_товщина", "assist", 1),
            ("трапеція", "isolation", 1),
            ("біцепс", "base", 1),
            ("біцепс", "isolation", 1),
        ]
    },
    "gym_legs_3": {
        "name": "Ноги",
        "structure": [
            ("квадрицепс", "base", 2),
            ("квадрицепс", "assist", 1),
            ("біцепс стегна", "base", 1),
            ("сідниці", "assist", 1),
            ("квадрицепс", "isolation", 1),
            ("литки", "calves", 2),
        ]
    },
    "gym_shoulders_3": {
        "name": "Плечі + Прес",
        "structure": [
            ("плечі", "base", 2),
            ("плечі", "assist", 1),
            ("задні дельти", "isolation", 2),
            ("трапеція", "isolation", 1),
            ("прес", "abs", 4),
        ]
    },

    # ════════════════════════════
    # ЗАЛ — РІВЕНЬ 4 (ПРО СПЛІТ)
    # ════════════════════════════
    "gym_chest_bi_4": {
        "name": "День 1 — Груди + Біцепс",
        "structure": [
            ("груди", "base", 2),
            ("груди", "assist", 2),
            ("груди", "isolation", 2),
            ("біцепс", "base", 2),
            ("біцепс", "isolation", 2),
            ("прес", "abs", 2),
        ]
    },
    "gym_back_thick_4": {
        "name": "День 2 — Спина (товщина)",
        "structure": [
            ("спина_товщина", "base", 2),
            ("спина_товщина", "assist", 3),
            ("задні дельти", "isolation", 1),
            ("трапеція", "isolation", 1),
        ]
    },
    "gym_legs_quad_4": {
        "name": "День 3 — Ноги (Квадрицепс)",
        "structure": [
            ("квадрицепс", "base", 2),
            ("квадрицепс", "assist", 2),
            ("квадрицепс", "isolation", 2),
            ("литки", "calves", 2),
        ]
    },
    "gym_shoulders_tri_4": {
        "name": "День 4 — Плечі + Трицепс",
        "structure": [
            ("плечі", "base", 2),
            ("плечі", "assist", 2),
            ("задні дельти", "isolation", 2),
            ("трицепс", "base", 1),
            ("трицепс", "isolation", 2),
        ]
    },
    "gym_back_wide_4": {
        "name": "День 5 — Спина (ширина) + Біцепс",
        "structure": [
            ("спина_ширина", "base", 2),
            ("спина_ширина", "assist", 2),
            ("спина_ширина", "isolation", 1),
            ("біцепс", "isolation", 2),
        ]
    },
    "gym_legs_ham_4": {
        "name": "День 6 — Задня поверхня + Сідниці",
        "structure": [
            ("біцепс стегна", "base", 2),
            ("біцепс стегна", "assist", 2),
            ("сідниці", "base", 2),
            ("сідниці", "isolation", 1),
            ("литки", "calves", 2),
            ("прес", "abs", 2),
        ]
    },
    "gym_recovery_4": {
        "name": "День 7 — Активне відновлення",
        "structure": [
            ("прес", "abs", 3),
            ("литки", "calves", 2),
        ],
        "note": "💆 30-40 хв кардіо низької інтенсивності\n🧘 Розтяжка всього тіла\n🔄 Робота з пінним роликом"
    },

    # ════════════════════════════
    # ДОМА — РІВЕНЬ 1 (ФУЛБОДІ)
    # ════════════════════════════
    "home_full_A_1": {
        "name": "Фулбоді A",
        "structure": [
            ("квадрицепс", "base", 1),
            ("груди", "base", 1),
            ("спина_ширина", "base", 1),
            ("сідниці", "base", 1),
            ("прес", "abs", 2),
        ]
    },
    "home_full_B_1": {
        "name": "Фулбоді B",
        "structure": [
            ("сідниці", "base", 1),
            ("груди", "assist", 1),
            ("спина_товщина", "base", 1),
            ("квадрицепс", "assist", 1),
            ("прес", "abs", 2),
        ]
    },
    "home_full_C_1": {
        "name": "Фулбоді C",
        "structure": [
            ("квадрицепс", "base", 1),
            ("груди", "base", 1),
            ("біцепс стегна", "base", 1),
            ("плечі", "assist", 1),
            ("прес", "abs", 3),
        ]
    },

    # ════════════════════════════
    # ДОМА — РІВЕНЬ 2 (ВЕРХ/НИЗ)
    # ════════════════════════════
    "home_upper_2": {
        "name": "Верхня частина тіла",
        "structure": [
            ("груди", "base", 2),
            ("спина_ширина", "base", 1),
            ("груди", "assist", 1),
            ("плечі", "assist", 1),
            ("трицепс", "isolation", 1),
            ("біцепс", "isolation", 1),
            ("прес", "abs", 2),
        ]
    },
    "home_lower_2": {
        "name": "Нижня частина тіла",
        "structure": [
            ("квадрицепс", "base", 2),
            ("сідниці", "base", 1),
            ("біцепс стегна", "assist", 1),
            ("квадрицепс", "assist", 1),
            ("литки", "calves", 2),
            ("прес", "abs", 2),
        ]
    },

    # ════════════════════════════
    # ДОМА — РІВЕНЬ 3 (СПЛІТ)
    # ════════════════════════════
    "home_push_3": {
        "name": "Push — Груди + Плечі + Трицепс",
        "structure": [
            ("груди", "base", 2),
            ("груди", "assist", 2),
            ("плечі", "assist", 1),
            ("трицепс", "isolation", 2),
            ("прес", "abs", 2),
        ]
    },
    "home_pull_3": {
        "name": "Pull — Спина + Біцепс",
        "structure": [
            ("спина_ширина", "base", 2),
            ("спина_товщина", "assist", 2),
            ("задні дельти", "isolation", 1),
            ("біцепс", "isolation", 2),
        ]
    },
    "home_legs_3": {
        "name": "Legs — Ноги + Сідниці",
        "structure": [
            ("квадрицепс", "base", 2),
            ("сідниці", "base", 2),
            ("біцепс стегна", "assist", 1),
            ("квадрицепс", "assist", 1),
            ("литки", "calves", 2),
            ("прес", "abs", 2),
        ]
    },

    # ════════════════════════════
    # ДОМА — РІВЕНЬ 4 (ПРО)
    # ════════════════════════════
    "home_chest_bi_4": {
        "name": "День 1 — Груди + Біцепс",
        "structure": [
            ("груди", "base", 3),
            ("груди", "assist", 2),
            ("груди", "isolation", 1),
            ("біцепс", "base", 2),
            ("біцепс", "isolation", 1),
            ("прес", "abs", 2),
        ]
    },
    "home_back_4": {
        "name": "День 2 — Спина",
        "structure": [
            ("спина_ширина", "base", 2),
            ("спина_товщина", "base", 2),
            ("спина_ширина", "assist", 1),
            ("задні дельти", "isolation", 1),
            ("трапеція", "isolation", 1),
        ]
    },
    "home_legs_quad_4": {
        "name": "День 3 — Ноги (Квадрицепс)",
        "structure": [
            ("квадрицепс", "base", 3),
            ("квадрицепс", "assist", 2),
            ("квадрицепс", "isolation", 1),
            ("литки", "calves", 2),
        ]
    },
    "home_shoulders_tri_4": {
        "name": "День 4 — Плечі + Трицепс",
        "structure": [
            ("плечі", "base", 2),
            ("плечі", "assist", 2),
            ("задні дельти", "isolation", 1),
            ("трицепс", "base", 2),
            ("трицепс", "isolation", 1),
        ]
    },
    "home_legs_ham_4": {
        "name": "День 5 — Задня поверхня + Сідниці",
        "structure": [
            ("біцепс стегна", "base", 2),
            ("сідниці", "base", 2),
            ("сідниці", "assist", 2),
            ("біцепс стегна", "assist", 1),
            ("литки", "calves", 2),
            ("прес", "abs", 2),
        ]
    },

    # ════════════════════════════
    # ВУЛИЦЯ — РІВЕНЬ 1
    # ════════════════════════════
    "out_full_A_1": {
        "name": "Фулбоді A",
        "structure": [
            ("квадрицепс", "base", 1),
            ("груди", "base", 1),
            ("спина_ширина", "base", 1),
            ("сідниці", "base", 1),
            ("прес", "abs", 2),
        ]
    },
    "out_full_B_1": {
        "name": "Фулбоді B",
        "structure": [
            ("сідниці", "base", 1),
            ("груди", "assist", 1),
            ("спина_ширина", "base", 1),
            ("квадрицепс", "assist", 1),
            ("прес", "abs", 2),
        ]
    },

    # ════════════════════════════
    # ВУЛИЦЯ — РІВЕНЬ 2
    # ════════════════════════════
    "out_upper_2": {
        "name": "Верхня частина тіла",
        "structure": [
            ("груди", "base", 2),
            ("спина_ширина", "base", 2),
            ("плечі", "assist", 1),
            ("трицепс", "isolation", 1),
            ("біцепс", "isolation", 1),
            ("прес", "abs", 2),
        ]
    },
    "out_lower_2": {
        "name": "Нижня частина тіла",
        "structure": [
            ("квадрицепс", "base", 2),
            ("сідниці", "base", 2),
            ("біцепс стегна", "assist", 1),
            ("литки", "calves", 2),
            ("прес", "abs", 2),
        ]
    },

    # ════════════════════════════
    # ВУЛИЦЯ — РІВЕНЬ 3
    # ════════════════════════════
    "out_push_3": {
        "name": "Push — Груди + Плечі + Трицепс",
        "structure": [
            ("груди", "base", 2),
            ("груди", "assist", 2),
            ("плечі", "assist", 1),
            ("трицепс", "isolation", 2),
            ("прес", "abs", 2),
        ]
    },
    "out_pull_3": {
        "name": "Pull — Спина + Біцепс",
        "structure": [
            ("спина_ширина", "base", 3),
            ("спина_товщина", "assist", 1),
            ("задні дельти", "isolation", 1),
            ("біцепс", "isolation", 2),
        ]
    },
    "out_legs_3": {
        "name": "Legs — Ноги + Сідниці",
        "structure": [
            ("квадрицепс", "base", 2),
            ("сідниці", "base", 2),
            ("біцепс стегна", "assist", 1),
            ("литки", "calves", 2),
            ("прес", "abs", 2),
        ]
    },

    # ════════════════════════════
    # ВУЛИЦЯ — РІВЕНЬ 4
    # ════════════════════════════
    "out_chest_bi_4": {
        "name": "День 1 — Груди + Біцепс",
        "structure": [
            ("груди", "base", 3),
            ("груди", "assist", 2),
            ("груди", "isolation", 1),
            ("біцепс", "base", 2),
            ("біцепс", "isolation", 1),
            ("прес", "abs", 2),
        ]
    },
    "out_back_4": {
        "name": "День 2 — Спина",
        "structure": [
            ("спина_ширина", "base", 3),
            ("спина_ширина", "assist", 2),
            ("задні дельти", "isolation", 1),
            ("біцепс", "isolation", 1),
        ]
    },
    "out_legs_4": {
        "name": "День 3 — Ноги",
        "structure": [
            ("квадрицепс", "base", 3),
            ("квадрицепс", "assist", 2),
            ("сідниці", "base", 1),
            ("литки", "calves", 2),
        ]
    },
    "out_shoulders_tri_4": {
        "name": "День 4 — Плечі + Трицепс",
        "structure": [
            ("плечі", "base", 2),
            ("плечі", "assist", 2),
            ("задні дельти", "isolation", 1),
            ("трицепс", "base", 2),
            ("трицепс", "isolation", 1),
        ]
    },
    "out_legs_ham_4": {
        "name": "День 5 — Задня поверхня + Сідниці",
        "structure": [
            ("біцепс стегна", "base", 2),
            ("сідниці", "base", 2),
            ("сідниці", "assist", 2),
            ("литки", "calves", 2),
            ("прес", "abs", 2),
        ]
    },
}


# ══════════════════════════════════════════════════════
# СПЛІТИ
# ══════════════════════════════════════════════════════

SPLITS = {
    "зал": {
        1: {
            1: ["gym_full_A_1"],
            2: ["gym_full_A_1", "gym_full_B_1"],
            3: ["gym_full_A_1", "gym_full_B_1", "gym_full_C_1"],
            4: ["gym_full_A_1", "gym_full_B_1", "gym_full_A_1", "gym_full_C_1"],
            5: ["gym_full_A_1", "gym_full_B_1", "gym_full_C_1", "gym_full_A_1", "gym_full_B_1"],
            6: ["gym_full_A_1", "gym_full_B_1", "gym_full_C_1", "gym_full_A_1", "gym_full_B_1", "gym_full_C_1"],
        },
        2: {
            1: ["gym_upper_2"],
            2: ["gym_upper_2", "gym_lower_2"],
            3: ["gym_upper_2", "gym_lower_2", "gym_upper_2"],
            4: ["gym_upper_2", "gym_lower_2", "gym_upper_2", "gym_lower_2"],
            5: ["gym_upper_2", "gym_lower_2", "gym_upper_2", "gym_lower_2", "gym_upper_2"],
            6: ["gym_upper_2", "gym_lower_2", "gym_upper_2", "gym_lower_2", "gym_upper_2", "gym_lower_2"],
        },
        3: {
            1: ["gym_chest_tri_3"],
            2: ["gym_chest_tri_3", "gym_back_bi_3"],
            3: ["gym_chest_tri_3", "gym_back_bi_3", "gym_legs_3"],
            4: ["gym_chest_tri_3", "gym_back_bi_3", "gym_legs_3", "gym_shoulders_3"],
            5: ["gym_chest_tri_3", "gym_back_bi_3", "gym_legs_3", "gym_shoulders_3", "gym_back_bi_3"],
            6: ["gym_chest_tri_3", "gym_back_bi_3", "gym_legs_3", "gym_shoulders_3", "gym_chest_tri_3", "gym_legs_3"],
        },
        4: {
            1: ["gym_chest_bi_4"],
            2: ["gym_chest_bi_4", "gym_back_thick_4"],
            3: ["gym_chest_bi_4", "gym_back_thick_4", "gym_legs_quad_4"],
            4: ["gym_chest_bi_4", "gym_back_thick_4", "gym_legs_quad_4", "gym_shoulders_tri_4"],
            5: ["gym_chest_bi_4", "gym_back_thick_4", "gym_legs_quad_4", "gym_shoulders_tri_4", "gym_back_wide_4"],
            6: ["gym_chest_bi_4", "gym_back_thick_4", "gym_legs_quad_4", "gym_shoulders_tri_4", "gym_back_wide_4", "gym_legs_ham_4"],
        },
    },
    "дома": {
        1: {
            1: ["home_full_A_1"],
            2: ["home_full_A_1", "home_full_B_1"],
            3: ["home_full_A_1", "home_full_B_1", "home_full_C_1"],
            4: ["home_full_A_1", "home_full_B_1", "home_full_C_1", "home_full_A_1"],
            5: ["home_full_A_1", "home_full_B_1", "home_full_C_1", "home_full_A_1", "home_full_B_1"],
            6: ["home_full_A_1", "home_full_B_1", "home_full_C_1", "home_full_A_1", "home_full_B_1", "home_full_C_1"],
        },
        2: {
            1: ["home_upper_2"],
            2: ["home_upper_2", "home_lower_2"],
            3: ["home_upper_2", "home_lower_2", "home_upper_2"],
            4: ["home_upper_2", "home_lower_2", "home_upper_2", "home_lower_2"],
            5: ["home_upper_2", "home_lower_2", "home_upper_2", "home_lower_2", "home_upper_2"],
            6: ["home_upper_2", "home_lower_2", "home_upper_2", "home_lower_2", "home_upper_2", "home_lower_2"],
        },
        3: {
            1: ["home_push_3"],
            2: ["home_push_3", "home_pull_3"],
            3: ["home_push_3", "home_pull_3", "home_legs_3"],
            4: ["home_push_3", "home_pull_3", "home_legs_3", "home_push_3"],
            5: ["home_push_3", "home_pull_3", "home_legs_3", "home_push_3", "home_pull_3"],
            6: ["home_push_3", "home_pull_3", "home_legs_3", "home_push_3", "home_pull_3", "home_legs_3"],
        },
        4: {
            1: ["home_chest_bi_4"],
            2: ["home_chest_bi_4", "home_back_4"],
            3: ["home_chest_bi_4", "home_back_4", "home_legs_quad_4"],
            4: ["home_chest_bi_4", "home_back_4", "home_legs_quad_4", "home_shoulders_tri_4"],
            5: ["home_chest_bi_4", "home_back_4", "home_legs_quad_4", "home_shoulders_tri_4", "home_legs_ham_4"],
            6: ["home_chest_bi_4", "home_back_4", "home_legs_quad_4", "home_shoulders_tri_4", "home_legs_ham_4", "home_chest_bi_4"],
        },
    },
    "вулиця": {
        1: {
            1: ["out_full_A_1"],
            2: ["out_full_A_1", "out_full_B_1"],
            3: ["out_full_A_1", "out_full_B_1", "out_full_A_1"],
            4: ["out_full_A_1", "out_full_B_1", "out_full_A_1", "out_full_B_1"],
            5: ["out_full_A_1", "out_full_B_1", "out_full_A_1", "out_full_B_1", "out_full_A_1"],
            6: ["out_full_A_1", "out_full_B_1", "out_full_A_1", "out_full_B_1", "out_full_A_1", "out_full_B_1"],
        },
        2: {
            1: ["out_upper_2"],
            2: ["out_upper_2", "out_lower_2"],
            3: ["out_upper_2", "out_lower_2", "out_upper_2"],
            4: ["out_upper_2", "out_lower_2", "out_upper_2", "out_lower_2"],
            5: ["out_upper_2", "out_lower_2", "out_upper_2", "out_lower_2", "out_upper_2"],
            6: ["out_upper_2", "out_lower_2", "out_upper_2", "out_lower_2", "out_upper_2", "out_lower_2"],
        },
        3: {
            1: ["out_push_3"],
            2: ["out_push_3", "out_pull_3"],
            3: ["out_push_3", "out_pull_3", "out_legs_3"],
            4: ["out_push_3", "out_pull_3", "out_legs_3", "out_push_3"],
            5: ["out_push_3", "out_pull_3", "out_legs_3", "out_push_3", "out_pull_3"],
            6: ["out_push_3", "out_pull_3", "out_legs_3", "out_push_3", "out_pull_3", "out_legs_3"],
        },
        4: {
            1: ["out_chest_bi_4"],
            2: ["out_chest_bi_4", "out_back_4"],
            3: ["out_chest_bi_4", "out_back_4", "out_legs_4"],
            4: ["out_chest_bi_4", "out_back_4", "out_legs_4", "out_shoulders_tri_4"],
            5: ["out_chest_bi_4", "out_back_4", "out_legs_4", "out_shoulders_tri_4", "out_legs_ham_4"],
            6: ["out_chest_bi_4", "out_back_4", "out_legs_4", "out_shoulders_tri_4", "out_legs_ham_4", "out_chest_bi_4"],
        },
    },
}


# ══════════════════════════════════════════════════════
# МАПИ М'ЯЗІВ
# ══════════════════════════════════════════════════════

# Які м'язи шукати для кожної групи
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

PATTERN_MAP = {
    # Груди
    "Жим штанги лежачи": "horizontal_press",
    "Похилий жим штанги": "incline_press",
    "Жим гантелей лежачи": "horizontal_press",
    "Похилий жим гантелей": "incline_press",
    "Жим штанги вниз головою": "decline_press",
    "Жим гантелей вниз головою": "decline_press",
    "Віджимання класичні": "horizontal_press",
    "Віджимання з підвищенням ніг": "incline_press",
    "Відмивання на брусах з нахилом вперед": "decline_press",
    "Відмивання на брусах": "decline_press",
    "TRX Віджимання": "horizontal_press",
    "Жим гирі лежачи": "horizontal_press",

    # Спина ширина (вертикальні тяги)
    "Підтягування широким хватом": "vertical_pull",
    "Підтягування зворотним хватом": "vertical_pull",
    "Підтягування вузьким хватом": "vertical_pull",
    "Тяга верхнього блоку широким хватом": "vertical_pull",
    "Тяга верхнього блоку вузьким хватом": "vertical_pull",
    "Тяга верхнього блоку зворотним хватом": "vertical_pull",
    "Австралійські підтягування": "horizontal_pull",
    "Тяга на петлях TRX (TRX Row)": "horizontal_pull",
    "Підтягування з вагою": "vertical_pull",
    "Вихід силою на турніку (Мускул-ап)": "vertical_pull_explosive",

    # Спина товщина (горизонтальні тяги + станова)
    "Станова тяга класична": "hip_hinge_deadlift",
    "Станова тяга сумо": "hip_hinge_deadlift",
    "Тяга штанги в нахилі прямим хватом": "horizontal_pull",
    "Тяга штанги в нахилі зворотним хватом": "horizontal_pull",
    "Тяга Т-грифа": "horizontal_pull",
    "Тяга гантелі однією рукою": "horizontal_pull",
    "Тяга нижнього блоку сидячи вузьким хватом": "horizontal_pull",
    "Тяга нижнього блоку широким хватом": "horizontal_pull",
    "Гарне ранок зі штангою": "hip_hinge",
    "Румунська тяга зі штангою": "hip_hinge",
    "Тяга гирі до поясу": "horizontal_pull",

    # Квадрицепс
    "Присідання зі штангою на спині": "squat_bilateral",
    "Фронтальні присідання": "squat_bilateral",
    "Присідання у Смітті": "squat_bilateral",
    "Жим ногами": "squat_machine",
    "Гак-машина присідання": "squat_machine",
    "Присідання з гантелями": "squat_bilateral",
    "Гоблет-присідання з гантеллю": "squat_bilateral",
    "Присідання з власною вагою": "squat_bilateral",
    "Присідання пістолетик": "squat_unilateral",
    "Гоблет-присідання з гирею": "squat_bilateral",
    "Стрибки в присіді": "squat_explosive",

    # Біцепс стегна
    "Румунська тяга з гантелями": "hip_hinge",
    "Мертва тяга на прямих ногах зі штангою": "hip_hinge",
    "Згинання ніг лежачи": "leg_curl",
    "Згинання ніг стоячи": "leg_curl",

    # Сідниці
    "Ягідний місток зі штангою": "hip_thrust",
    "Ягідний місток з гантеллю": "hip_thrust",
    "Міст на плечах": "hip_thrust",
    "Болгарські випади зі штангою": "lunge_unilateral",
    "Болгарські випади з гантелями": "lunge_unilateral",
    "Болгарські випади": "lunge_unilateral",
    "Випади зі штангою": "lunge_unilateral",
    "Випади з гантелями": "lunge_unilateral",
    "Міст з резинкою на стегнах": "hip_thrust",
    "Міст на одній нозі": "hip_thrust_unilateral",

    # Плечі (вертикальний жим)
    "Армійський жим стоячи": "vertical_press",
    "Армійський жим сидячи": "vertical_press",
    "Жим гантелей сидячи": "vertical_press",
    "Жим гантелей стоячи": "vertical_press",
    "Жим Арнольда": "vertical_press",
    "Жим за голову": "vertical_press",
    "Стійка на руках біля стіни": "vertical_press_bodyweight",
    "Віджимання в упорі стоячи": "vertical_press_bodyweight",
    "TRX Жим плечей": "vertical_press",
    "Жим двох гирей стоячи": "vertical_press",

    # Біцепс
    "Підйом штанги на біцепс стоячи": "bicep_curl",
    "Підйом EZ-штанги на біцепс": "bicep_curl",
    "Підйом гантелей на біцепс стоячи": "bicep_curl",
    "Підйом штанги на лаві Скотта": "bicep_curl_isolated",
    "TRX Підйом на біцепс": "bicep_curl",

    # Трицепс
    "Жим штанги вузьким хватом": "horizontal_press",
    "Французький жим лежачи зі штангою": "tricep_extension",
    "Французький жим з гантеллю лежачи": "tricep_extension",
    "Відмивання від лавки або стільця": "tricep_dip",
    "TRX Розгинання трицепса": "tricep_extension",
    "Алмазні віджимання": "horizontal_press",
}


# Згенеровано автоматично — auto_tag_patterns.py
# Об'єднай з ручним PATTERN_MAP: PATTERN_MAP.get(name) or AUTO_PATTERN_MAP.get(name)

AUTO_PATTERN_MAP = {
    'TRX Болгарські випади': 'lunge_unilateral',
    'TRX Випади': 'lunge_unilateral',
    'TRX Віджимання': 'horizontal_press',
    'TRX Гірський альпініст': 'core_flexion',
    'TRX Жим від грудей стоячи': 'horizontal_press',
    'TRX Жим плечей': 'vertical_press',
    'TRX Зворотнє розведення': 'rear_delt_fly',
    'TRX Міст': 'hip_thrust',
    'TRX Планка': 'core_stability',
    'TRX Похилі віджимання': 'incline_press',
    'TRX Присідання': 'squat_bilateral',
    'TRX Присідання на одній нозі': 'squat_unilateral',
    'TRX Підйом на біцепс': 'bicep_curl',
    'TRX Підтягування': 'vertical_pull',
    'TRX Розгинання трицепса': 'tricep_extension',
    'TRX Ротація тулуба': 'core_rotation',
    'V-підйом': 'core_flexion',
    'Y-розведення з гантелями': 'rear_delt_fly',
    'Ізометричний опір шиї вперед': 'neck',
    'Ізометричний опір шиї назад': 'neck',
    'Інтервальне тренування щохвилини (EMOM)': 'conditioning',
    'Інтервальний біг': 'conditioning',
    'Їзда на велосипеді': 'core_flexion',
    'Австралійські підтягування': 'vertical_pull',
    'Аквааеробіка': 'conditioning',
    'Активація сідниць лежачи': 'hip_thrust',
    'Алмазні віджимання': 'horizontal_press',
    'Апперкоти по мішку': 'core_flexion',
    'Армійський жим зі штовханням': 'vertical_press',
    'Армійський жим сидячи': 'vertical_press',
    'Армійський жим стоячи': 'vertical_press',
    'Батерфляй (плавання)': 'core_flexion',
    'Батут (стрибки)': 'core_flexion',
    'Берпі': 'conditioning',
    'Берпі з підтягуванням': 'vertical_pull',
    'Берпі з підтягуванням та вибухом': 'vertical_pull',
    'Бойові мотузки (Battle ropes)': 'core_flexion',
    'Боковий кидок медбола': 'core_flexion',
    'Бокові перекати з грифом': 'core_flexion',
    'Болгарські випади': 'lunge_unilateral',
    'Болгарські випади з гантелями': 'lunge_unilateral',
    'Болгарські випади зі штангою': 'lunge_unilateral',
    'Брас (плавання)': 'core_flexion',
    'Бігова доріжка': 'conditioning',
    'Бігова розминка на місці': 'conditioning',
    'Бічна планка': 'core_stability',
    'Бічна планка з підйомом ноги': 'core_flexion',
    'Бічна планка на фітболі': 'core_stability',
    'Бічна розтяжка стоячи': 'core_flexion',
    'Бічні випади': 'lunge_unilateral',
    'Вакуум живота': 'core_flexion',
    'Ведмежа прогулянка': 'core_flexion',
    'Велосипед': 'core_flexion',
    'Велотренажер': 'conditioning',
    'Велотренажер інтервалами': 'conditioning',
    'Верблюд (Camel pose)': 'mobility',
    'Вибухові віджимання': 'horizontal_press',
    'Випади з гантелями': 'lunge_unilateral',
    'Випади з гирею над головою': 'lunge_unilateral',
    'Випади зі штангою': 'lunge_unilateral',
    'Випади крокові': 'lunge_unilateral',
    'Випади на місці': 'lunge_unilateral',
    'Випади назад з гантелями на місці': 'lunge_unilateral',
    'Вис в упорі (L-вис підготовка)': 'core_flexion',
    'Вис на одній руці (підготовка)': 'forearm',
    'Вис на турніку': 'forearm',
    'Високе піднімання колін': 'core_flexion',
    'Вихід силою на кільцях (Мускул-ап)': 'vertical_pull_explosive',
    'Вихід силою на турнику (Muscle-up transition)': 'vertical_pull_explosive',
    'Вихід силою на турніку (Мускул-ап)': 'vertical_pull_explosive',
    'Внутрішня ротація плеча з резинкою': 'rotation',
    'Воїн 1 (Warrior I)': 'core_flexion',
    'Воїн 2 (Warrior II)': 'core_flexion',
    'Воїн 3 (Warrior III)': 'core_flexion',
    'Вправи з булавами (Indian clubs)': 'core_flexion',
    'Вправи з гімнастичною палицею': 'core_flexion',
    'Вухо-вухо (бокс в парі)': 'core_flexion',
    'Відведення ноги з резинкою стоячи': 'hip_abduction',
    'Відведення ноги назад з резинкою': 'hip_abduction',
    'Відведення ноги назад у тренажері': 'hip_abduction',
    'Відведення ноги у тренажері': 'hip_abduction',
    'Віджимання в упорі стоячи': 'vertical_press',
    'Віджимання вузьким хватом': 'horizontal_press',
    'Віджимання від дивана на трицепс': 'horizontal_press',
    'Віджимання з оплеском': 'horizontal_press',
    'Віджимання з підвищенням ніг': 'incline_press',
    'Віджимання з підвищенням рук': 'horizontal_press',
    'Віджимання з резинкою на спині': 'horizontal_press',
    'Віджимання класичні': 'horizontal_press',
    'Віджимання на брусах з піднятими ногами': 'horizontal_press',
    'Віджимання на кулаках': 'horizontal_press',
    "Віджимання на кулаках з підтримкою зап'ястя": 'horizontal_press',
    'Віджимання на кільцях в упорі': 'horizontal_press',
    'Віджимання на нестабільній платформі (BOSU)': 'horizontal_press',
    'Віджимання на паралетах': 'horizontal_press',
    'Віджимання широким хватом': 'horizontal_press',
    'Відмивання від лавки або стільця': 'horizontal_press',
    'Відмивання на брусах': 'horizontal_press',
    'Відмивання на брусах з вагою': 'horizontal_press',
    'Відмивання на брусах з джгутом (полегшені)': 'horizontal_press',
    'Відмивання на брусах з нахилом вперед': 'horizontal_press',
    'Відмивання на кільцях': 'horizontal_press',
    'Гарне ранок зі штангою': 'hip_hinge',
    'Глибокий випад з поворотом': 'lunge_unilateral',
    'Голуб (Pigeon pose повний)': 'mobility',
    'Голубець (pigeon pose)': 'mobility',
    'Горизонтальна тяга в тренажері': 'horizontal_pull',
    'Горизонтальний вис — підготовка до планша (Planche)': 'core_flexion',
    'Гребля на тренажері інтервалами': 'core_flexion',
    'Гребний тренажер': 'core_flexion',
    'Гіперекстензія': 'hip_hinge',
    'Гіперекстензія в неповну амплітуду': 'hip_hinge',
    'Гірський альпініст': 'core_flexion',
    'Гірський альпініст хрест': 'core_flexion',
    'Дерево (Tree pose)': 'core_flexion',
    'Джеб-крос комбінація': 'core_flexion',
    'Динамічне розкриття грудного відділу': 'mobility',
    'Динамічні випади в русі (розминка)': 'lunge_unilateral',
    'Дихальні скручування (діафрагмальні)': 'core_flexion',
    'Дракон флаг (підготовка)': 'core_flexion',
    'Дракон флаг з зігнутими колінами (легка версія)': 'core_flexion',
    'Еліпсоїд': 'conditioning',
    'Жим Арнольда': 'vertical_press',
    'Жим від грудей без закидання голови': 'horizontal_press',
    'Жим від грудей в тренажері (низький кут)': 'horizontal_press',
    'Жим від грудей сидячи в тренажері': 'horizontal_press',
    'Жим гантелей вниз головою': 'decline_press',
    'Жим гантелей лежачи': 'horizontal_press',
    'Жим гантелей на похилій лаві вниз головою': 'decline_press',
    'Жим гантелей сидячи': 'vertical_press',
    'Жим гантелей сидячи під кутом': 'vertical_press',
    'Жим гантелей стоячи': 'vertical_press',
    'Жим гантелей стоячи на одній нозі': 'vertical_press',
    'Жим гантелей у нейтральному хваті лежачи': 'horizontal_press',
    'Жим гирі з коліна (Windmill)': 'vertical_press',
    'Жим гирі лежачи': 'horizontal_press',
    'Жим гирі однією рукою стоячи': 'vertical_press',
    'Жим двох гирей стоячи': 'vertical_press',
    'Жим з резинкою лежачи': 'horizontal_press',
    'Жим за голову': 'vertical_press',
    'Жим лежачи з важким джгутом': 'horizontal_press',
    'Жим лежачи з ланцюгами': 'horizontal_press',
    'Жим лежачи з паузою': 'horizontal_press',
    'Жим медбола лежачи': 'horizontal_press',
    'Жим ногами': 'squat_machine',
    'Жим ногами в неповну амплітуду': 'squat_machine',
    'Жим ногами вузькою постановкою': 'squat_machine',
    'Жим ногами однією ногою': 'squat_machine',
    'Жим ногами під кутом 45': 'squat_machine',
    'Жим ногами широкою постановкою': 'squat_machine',
    'Жим плечей у тренажері': 'vertical_press',
    'Жим пляшками з водою лежачи': 'horizontal_press',
    'Жим резинки стоячи': 'vertical_press',
    'Жим рюкзака лежачи': 'horizontal_press',
    'Жим у тренажері Сміта (груди)': 'horizontal_press',
    'Жим у тренажері Сміта (плечі)': 'vertical_press',
    'Жим штанги вниз головою': 'decline_press',
    'Жим штанги вузьким хватом': 'horizontal_press',
    'Жим штанги з паузою на стійках (Pin Press)': 'horizontal_press',
    'Жим штанги лежачи': 'horizontal_press',
    'Жим штовхаючи вгору з присіду (Squat Push Press)': 'squat_bilateral',
    'Жим із зігнутим тілом на брусах (Pike Press)': 'vertical_press',
    'Забіг по сходах': 'conditioning',
    'Закочування фітболу': 'core_flexion',
    'Закручування штанги на передпліччя': 'forearm',
    'Заминка — глибоке дихання лежачи': 'mobility',
    'Захльости гомілкою назад': 'conditioning',
    'Зашагування на лаву з гантелями': 'lunge_unilateral',
    'Зашагування на лаву зі штангою': 'lunge_unilateral',
    'Зашагування на степ з гирею': 'lunge_unilateral',
    'Зашагування на стілець': 'lunge_unilateral',
    'Зведення в кросовері верхній блок': 'chest_fly',
    'Зведення в кросовері нижній блок': 'chest_fly',
    'Зведення ніг з резинкою лежачи': 'hip_adduction',
    'Зведення ніг у тренажері': 'hip_adduction',
    'Зведення рук лежачи на підлозі (без лави)': 'chest_fly',
    'Зворотна гіперекстензія': 'hip_hinge',
    'Зворотна гіперекстензія лежачи': 'hip_hinge',
    'Зворотне розведення з резинкою': 'rear_delt_fly',
    'Зворотні випади з власною вагою': 'lunge_unilateral',
    'Зворотні випади з гантелями': 'lunge_unilateral',
    'Зворотні випади зі штангою': 'lunge_unilateral',
    'Зворотні зведення на блоці': 'rear_delt_fly',
    "Зворотні згинання зап'ясть": 'forearm',
    'Зворотні скручування': 'core_flexion',
    'Зворотні скручування з підйомом таза': 'core_flexion',
    'Зворотній випад з підйомом руки': 'lunge_unilateral',
    'Зворотній пек-дек': 'rear_delt_fly',
    "Згинання зап'ясть з гантелями": 'forearm',
    "Згинання зап'ясть зі штангою": 'forearm',
    'Згинання ніг лежачи': 'leg_curl',
    'Згинання ніг стоячи': 'leg_curl',
    'Згинання ніг у тренажері сидячи (памп)': 'leg_curl',
    'Згинання однієї ноги лежачи': 'leg_curl',
    'Згинання рук на біцепс на похилій лаві': 'bicep_curl',
    'Згинання шиї вперед з опором': 'neck',
    'Зміна рук з гирею у висі': 'core_flexion',
    'Зовнішня ротація плеча з резинкою': 'rotation',
    'Кабельні перехрещення (crossover)': 'chest_fly',
    'Кидок медбола над головою': 'core_flexion',
    'Кидок медбола об стіну': 'core_flexion',
    "Кидок набивного м'яча об підлогу": 'core_flexion',
    'Кистьовий еспандер': 'forearm',
    'Кистьовий ролик (Wrist Roller)': 'forearm',
    'Кобра': 'core_flexion',
    'Колесо для преса': 'core_flexion',
    'Колесо для преса з колін': 'core_flexion',
    'Колесо для преса стоячи': 'core_flexion',
    'Комплекс присід-віджимання-стрибок (Burpee Box)': 'squat_bilateral',
    'Комплексна вправа з гантелями (Man Maker)': 'carry',
    "Комплексна розтяжка всього тіла (World's Greatest Stretch)": 'mobility',
    'Концентровані підйоми': 'bicep_curl_isolated',
    'Кроки з обтяженням (weighted walking)': 'core_flexion',
    'Кроки крабом з резинкою': 'hip_abduction',
    'Крокуючі випади з гантелями': 'lunge_unilateral',
    'Кроль (плавання)': 'core_flexion',
    'Кругові махи гирею': 'hip_hinge',
    'Кругові оберти плечима': 'mobility',
    'Кругові оберти тазом': 'core_flexion',
    'Кут (Angle pose)': 'core_flexion',
    'Кут у висі': 'core_flexion',
    'Кікбек з гантеллю': 'tricep_extension',
    'Лебідь на підлозі (Swan)': 'mobility',
    'Легкий біг підтюпцем': 'conditioning',
    'Лучник (Archer pull-up)': 'vertical_pull_explosive',
    'Максимум кіл за відведений час (AMRAP)': 'conditioning',
    'Махи гирею двома руками (Swing)': 'hip_hinge',
    'Махи гирею однією рукою': 'hip_hinge',
    'Мертва тяга з гантелями': 'hip_hinge_deadlift',
    'Мертва тяга з гирею': 'hip_hinge_deadlift',
    'Мертва тяга на прямих ногах зі штангою': 'hip_hinge_deadlift',
    'Мертвий жук — почергові рухи рук і ніг лежачи (Dead Bug)': 'core_flexion',
    'Метелик (розтяжка паху)': 'mobility',
    'Мобілізація гомілковостопного суглоба': 'mobility',
    'Молотки з гантелями': 'bicep_curl',
    'Молотки з резинкою': 'bicep_curl',
    'Міст (Bridge pose)': 'hip_thrust',
    'Міст з резинкою на стегнах': 'hip_thrust',
    'Міст на одній нозі': 'hip_thrust_unilateral',
    'Міст на плечах': 'hip_thrust',
    'Місяць (Half Moon pose)': 'core_flexion',
    'Нахил в тазостегновому суглобі (Хіп-хінж)': 'mobility',
    'Нахил шиї в сторону з опором': 'neck',
    'Нахили з гантеллю в сторону': 'core_rotation',
    'Нахили зі штангою в сторони': 'core_rotation',
    "Нахили стоячи на косі м'язи": 'core_rotation',
    'Негативні відмивання на брусах': 'horizontal_press',
    'Негативні підтягування': 'vertical_pull',
    'Ножиці': 'core_flexion',
    'Ножиці пілатес': 'core_flexion',
    'Нордичне згинання гомілки': 'leg_curl',
    'Носки до перекладини (Toes to Bar)': 'core_flexion',
    'Обертання гирі навколо голови (Хало)': 'core_flexion',
    "Обертання зап'ястків": 'forearm',
    'Обертання шиї': 'neck',
    'Одна нога кола (Single leg circle)': 'core_flexion',
    'Одноруке віджимання': 'horizontal_press',
    'Пайк на підлозі': 'core_flexion',
    'Пек-дек (метелик)': 'chest_fly',
    'Перекати штанги по підлозі': 'core_flexion',
    'Перекочування на спині (Rolling like a ball)': 'core_flexion',
    'Плавання з дошкою (ноги)': 'conditioning',
    'Плавання на спині': 'conditioning',
    'Плавання на швидкість': 'conditioning',
    'Планка "супермен"': 'hip_hinge',
    'Планка з дотиком плеча': 'core_stability',
    'Планка з опорою на лаву (полегшена)': 'core_stability',
    'Планка з переступанням (Plank Jacks)': 'core_stability',
    'Планка з підйомом ноги': 'core_flexion',
    'Планка з підйомом ноги та руки (Bird-Dog)': 'core_flexion',
    'Планка з підйомом руки': 'core_flexion',
    'Планка з підйомом руки і ноги': 'core_flexion',
    'Планка на ліктях': 'core_stability',
    'Планка на нестабільній платформі (BOSU)': 'core_stability',
    'Планка на руках': 'core_stability',
    'Планка на фітболі': 'core_stability',
    'Планш на брусах (підготовка)': 'core_flexion',
    'Планш на кільцях (підготовка)': 'core_flexion',
    'Планш на паралетах (підготовка)': 'core_flexion',
    'Подвійні прокрути скакалки за стрибок (Double Under)': 'conditioning',
    'Подвійні стрибки зі скакалкою': 'conditioning',
    'Поза дитини': 'mobility',
    'Поза орла (Eagle Pose)': 'core_flexion',
    'Поза саранчі (Locust Pose)': 'mobility',
    'Похила розводка гантелей': 'incline_press',
    'Похилий жим гантелей': 'incline_press',
    'Похилий жим штанги': 'incline_press',
    'Поштовх гирі': 'olympic_press',
    'Поштовх двох гирей': 'olympic_press',
    'Поштовх штанги над головою (Поштовх)': 'olympic_press',
    'Привітання сонцю (Surya Namaskar)': 'mobility',
    'Присід гирі на плечі (Front Rack Squat)': 'squat_bilateral',
    'Присід з жимом гантелей (Squat to Press)': 'squat_bilateral',
    'Присід з жимом гантелей над головою (Трастер)': 'squat_bilateral',
    'Присід з жимом штанги над головою (Трастер)': 'squat_bilateral',
    'Присід зі стрибком (Squat Jump)': 'squat_explosive',
    'Присід у машині Сміта сумо': 'squat_bilateral',
    'Присідання в неповну амплітуду': 'squat_bilateral',
    'Присідання в тренажері Смітта вузько': 'squat_machine',
    'Присідання з важким джгутом': 'squat_bilateral',
    'Присідання з власною вагою': 'squat_bilateral',
    'Присідання з вузькою постановкою ніг': 'squat_bilateral',
    'Присідання з гантеллю перед грудьми (Гоблет-присідання)': 'squat_bilateral',
    'Присідання з гантелями': 'squat_bilateral',
    'Присідання з гирею над головою': 'squat_bilateral',
    'Присідання з гирею перед грудьми (Гоблет-присідання)': 'squat_bilateral',
    'Присідання з кидком медбола': 'squat_bilateral',
    'Присідання з ланцюгами': 'squat_bilateral',
    'Присідання з медболом над головою': 'squat_bilateral',
    'Присідання з паузою': 'squat_bilateral',
    'Присідання з поясом (Belt Squat)': 'squat_bilateral',
    'Присідання з поясом без навантаження на спину (Belt Squat)': 'squat_bilateral',
    'Присідання з резинкою': 'squat_bilateral',
    'Присідання з рюкзаком': 'squat_bilateral',
    'Присідання з стрибком і гантелями': 'squat_explosive',
    'Присідання зі стрибком і жимом гантелей': 'squat_explosive',
    'Присідання зі штангою на спині': 'squat_bilateral',
    'Присідання зі штангою над головою (Overhead Squat)': 'squat_bilateral',
    'Присідання на балансувальній дошці': 'squat_bilateral',
    'Присідання на нестабільній платформі (BOSU)': 'squat_bilateral',
    'Присідання на одній нозі з опорою (Skater Squat)': 'squat_unilateral',
    'Присідання на одній нозі на нестабільній платформі (BOSU)': 'squat_unilateral',
    'Присідання пістолетик': 'squat_unilateral',
    'Присідання сумо з власною вагою': 'squat_bilateral',
    'Присідання сумо з гантеллю': 'squat_bilateral',
    'Присідання сумо з гирею': 'squat_bilateral',
    'Присідання сумо з резинкою': 'squat_bilateral',
    'Присідання у Смітті': 'squat_bilateral',
    'Присідання у Смітті вузьким хватом': 'squat_bilateral',
    'Присідання у тренажері Гакк (Гак-машина)': 'squat_machine',
    'Присідання у тренажері Гакк (Гак-присідання)': 'squat_machine',
    'Прогин спини кішка-корова (Кіт-корова)': 'core_flexion',
    'Прогулянка на руках': 'core_flexion',
    'Пронація та супінація з гантеллю': 'forearm',
    'Проніс гирі між ніг назад (Hike Pass)': 'core_flexion',
    'Протяжка штанги широким хватом': 'lateral_raise',
    'Пуловер з гантеллю': 'pullover',
    'Пуловер зі штангою': 'pullover',
    'Пуловер на верхньому блоці': 'lat_pullover',
    'Пульсуючі присідання': 'squat_bilateral',
    'Підйом EZ-штанги зворотним хватом': 'bicep_curl',
    'Підйом EZ-штанги на біцепс': 'bicep_curl',
    'Підйом гантелей в сторони': 'lateral_raise',
    'Підйом гантелей в сторони в нахилі': 'rear_delt_fly',
    'Підйом гантелей в сторони до рівня плеча': 'lateral_raise',
    'Підйом гантелей в сторони сидячи': 'lateral_raise',
    'Підйом гантелей вперед': 'front_raise',
    'Підйом гантелей зворотним хватом': 'bicep_curl',
    'Підйом гантелей на біцепс стоячи': 'bicep_curl',
    'Підйом гантелей на лаві Скотта': 'bicep_curl_isolated',
    'Підйом гантелей почергово': 'bicep_curl',
    'Підйом гантелі в сторону лежачи на боці': 'lateral_raise',
    'Підйом гантелі лежачи на похилій лаві': 'bicep_curl',
    'Підйом каната': 'bicep_curl',
    'Підйом колін стоячи': 'core_flexion',
    'Підйом колін у висі': 'core_flexion',
    'Підйом литок у тренажері для преса': 'calf_raise',
    'Підйом на блоці в сторону однією рукою': 'lateral_raise',
    'Підйом на біцепс в кросовері': 'bicep_curl',
    'Підйом на біцепс в тренажері': 'bicep_curl',
    'Підйом на біцепс з гирею': 'bicep_curl',
    'Підйом на біцепс з резинкою': 'bicep_curl',
    'Підйом на біцепс мотузкою': 'bicep_curl',
    'Підйом на біцепс на нижньому блоці': 'bicep_curl',
    'Підйом на носки в тренажері жим ногами': 'squat_machine',
    'Підйом на носки з гантелями': 'calf_raise',
    'Підйом на носки з резинкою': 'calf_raise',
    'Підйом на носки зі штангою': 'calf_raise',
    'Підйом на носки зі штангою сидячи': 'calf_raise',
    'Підйом на носки на одній нозі': 'calf_raise',
    'Підйом на носки на одній нозі з гантеллю': 'calf_raise',
    'Підйом на носки сидячи з гантелями': 'calf_raise',
    'Підйом на носки сидячи у тренажері': 'calf_raise',
    'Підйом на носки стоячи': 'calf_raise',
    'Підйом на носки стоячи у тренажері': 'calf_raise',
    'Підйом ніг лежачи': 'core_flexion',
    'Підйом ніг на брусах': 'core_flexion',
    'Підйом ніг на похилій лаві': 'core_flexion',
    'Підйом ніг у висі з поворотом': 'core_rotation',
    'Підйом ніг у висі прямих': 'core_flexion',
    'Підйом ніг у тренажері': 'core_flexion',
    'Підйом резинки в сторони': 'lateral_raise',
    'Підйом резинки вперед': 'front_raise',
    'Підйом таза з гантеллю з опорою на лаву': 'hip_thrust',
    'Підйом таза лежачи з опорою на лаву (Hip Thrust)': 'hip_thrust',
    'Підйом штанги зворотним хватом': 'bicep_curl',
    'Підйом штанги на біцепс стоячи': 'bicep_curl',
    'Підйом штанги на лаві Скотта': 'bicep_curl_isolated',
    'Підтягування вузьким нейтральним хватом': 'vertical_pull',
    'Підтягування вузьким хватом': 'vertical_pull',
    'Підтягування до грудей': 'vertical_pull',
    'Підтягування з вагою': 'vertical_pull',
    'Підтягування з джгутом (полегшені)': 'vertical_pull',
    'Підтягування з затримкою вгорі': 'vertical_pull',
    'Підтягування зворотним хватом': 'vertical_pull',
    'Підтягування на кільцях': 'vertical_pull',
    'Підтягування нейтральним хватом': 'vertical_pull',
    'Підтягування хвилею': 'vertical_pull',
    'Підтягування широким хватом': 'vertical_pull',
    'Підтягування широким хватом до грудей (акцент на широчайші)': 'vertical_pull',
    'Ривкова тяга від стегна (Кліп)': 'olympic_pull',
    'Ривкова тяга зі штангою до плечей (Кліп)': 'olympic_pull',
    'Ривок гирі': 'olympic_pull',
    'Ривок штанги над головою (Снеч)': 'olympic_pull',
    'Розведення в сторони в тренажері (Lateral Raise Machine)': 'lateral_raise',
    'Розведення в сторони на блоці стоячи': 'lateral_raise',
    'Розведення гантелей в нахилі': 'rear_delt_fly',
    'Розведення гантелей на похилій лаві вниз головою': 'decline_press',
    'Розведення на задні дельти в кросовері': 'rear_delt_fly',
    'Розведення на задні дельти в тренажері': 'rear_delt_fly',
    'Розводка гантелей лежачи': 'chest_fly',
    'Розводка з резинкою': 'chest_fly',
    'Розводка на кільцях': 'chest_fly',
    'Розгинання гантелі з-за голови стоячи': 'tricep_extension',
    'Розгинання двох гантелей з-за голови': 'tricep_extension',
    "Розгинання зап'ясть з гантелями": 'forearm',
    "Розгинання зап'ясть зі штангою": 'forearm',
    'Розгинання на блоці зворотним хватом': 'tricep_extension',
    'Розгинання на блоці мотузкою': 'tricep_extension',
    'Розгинання на блоці прямою рукояткою': 'tricep_extension',
    'Розгинання ніг у неповну амплітуду': 'leg_curl',
    'Розгинання ніг у тренажері': 'leg_curl',
    'Розгинання рук в кросовері з мотузкою над головою': 'tricep_extension',
    'Розгинання рук у тренажері на трицепс': 'tricep_extension',
    'Розгинання спини на римському стільці': 'hip_hinge',
    'Розгинання спини на фітболі': 'hip_hinge',
    'Розгинання трицепса з гирею': 'tricep_extension',
    'Розгинання трицепса з резинкою над головою': 'tricep_extension',
    'Розгинання трицепса з резинкою стоячи': 'tricep_extension',
    'Розгинання шиї назад з опором': 'neck',
    'Розгойдування в позі складеного тіла (Hollow Rock)': 'core_flexion',
    'Розтягування резинки за спиною': 'rear_delt_fly',
    'Розтяжка IT-стрічки': 'mobility',
    'Розтяжка ахілового сухожилля': 'mobility',
    'Розтяжка біцепса стегна лежачи': 'mobility',
    'Розтяжка грудей біля стіни': 'mobility',
    'Розтяжка грудей у дверному проході': 'mobility',
    'Розтяжка грудної клітки на ролику': 'mobility',
    'Розтяжка задньої поверхні стегна стоячи': 'mobility',
    'Розтяжка квадрицепса стоячи': 'mobility',
    "Розтяжка косих м'язів стоячи": 'core_flexion',
    'Розтяжка литок стоячи': 'calf_raise',
    'Розтяжка передпліччя': 'forearm',
    'Розтяжка плеча поперек тіла': 'mobility',
    'Розтяжка спини сидячи (нахил вперед)': 'mobility',
    'Розтяжка стегна 90/90': 'mobility',
    'Розтяжка стегна лежачи на спині (коліно до грудей)': 'mobility',
    'Розтяжка сідниць лежачи': 'mobility',
    'Розтяжка трапеції нахилом голови': 'neck',
    'Розтяжка трицепса над головою': 'mobility',
    'Розтяжка широчайніх стоячи': 'mobility',
    'Розтяжка шиї бічна': 'neck',
    'Ролик для мобілізації хребта': 'core_flexion',
    'Ролик для спини (пінний)': 'mobility',
    'Російські скручування': 'core_flexion',
    'Ротаційна планка': 'core_stability',
    'Ротація з медболом стоячи': 'core_rotation',
    'Ротація плечей': 'rotation',
    'Ротація тулуба на блоці': 'core_rotation',
    'Румунська тяга в тренажері Сміта': 'hip_hinge',
    'Румунська тяга з гантелями': 'hip_hinge',
    'Румунська тяга з опорою на лаву однією ногою': 'hip_hinge',
    'Румунська тяга зі штангою': 'hip_hinge',
    'Румунська тяга на одній нозі з гантелею': 'hip_hinge',
    'Рядок на кільцях': 'horizontal_pull',
    'Скандинавська ходьба': 'conditioning',
    'Скапулярні підтягування': 'vertical_pull',
    'Складання тіла (Teaser)': 'core_flexion',
    'Складання тіла на петлях TRX (TRX Pike)': 'core_flexion',
    'Скручування': 'core_flexion',
    'Скручування з диском': 'core_flexion',
    'Скручування з медболом': 'core_flexion',
    'Скручування з поворотом': 'core_rotation',
    'Скручування з піднятими ногами': 'core_flexion',
    'Скручування з резинкою': 'core_flexion',
    "Скручування зап'ястя зі штангою": 'core_flexion',
    'Скручування лежачи (Supine twist)': 'core_flexion',
    "Скручування на м'ячі з опорою на ноги": 'core_flexion',
    'Скручування на похилій лаві': 'core_flexion',
    'Скручування на фітболі': 'core_flexion',
    'Скручування на фітболі з поворотом': 'core_rotation',
    'Скручування у тренажері': 'core_flexion',
    'Собака мордою вгору': 'mobility',
    'Собака мордою вниз': 'mobility',
    'Сотня (Pilates Hundred)': 'core_flexion',
    'Спринт 30м': 'conditioning',
    'Спринт в гору': 'conditioning',
    'Спринт на місці': 'conditioning',
    'Станова тяга з дефіцитом (стоячи на підвищенні)': 'hip_hinge_deadlift',
    'Станова тяга з паузою': 'hip_hinge_deadlift',
    'Станова тяга класична': 'hip_hinge_deadlift',
    'Станова тяга сумо': 'hip_hinge_deadlift',
    'Стояння на одній нозі': 'core_flexion',
    'Стояння на одній нозі на нестабільній платформі (BOSU)': 'core_flexion',
    'Стрибки Джека': 'conditioning',
    'Стрибки в глибину': 'conditioning',
    'Стрибки в присіді': 'squat_explosive',
    'Стрибки зі зміною ніг': 'conditioning',
    'Стрибки зі скакалкою': 'conditioning',
    'Стрибки на лавку': 'conditioning',
    'Стрибки на носках': 'calf_raise',
    'Стрибки на скакалці в повільному темпі': 'conditioning',
    'Стрибки на тумбу': 'conditioning',
    'Стрибки по сходах через одну': 'conditioning',
    'Стрибки через уявну лінію': 'core_flexion',
    'Стрибок у довжину з місця': 'conditioning',
    'Стійка на руках біля стіни': 'vertical_press',
    'Стійка на руках на кільцях': 'vertical_press',
    'Стійка на руках на паралетах': 'vertical_press',
    'Стілець (Chair pose)': 'core_flexion',
    'Стінне присідання': 'squat_bilateral',
    'Супермен': 'hip_hinge',
    'Супермен по черзі': 'hip_hinge',
    'Сходинковий тренажер (степер)': 'conditioning',
    'Трикутник (Triangle pose)': 'core_flexion',
    'Турецький підйом': 'core_flexion',
    'Тяга Т-грифа': 'horizontal_pull',
    'Тяга в стрибок': 'olympic_pull',
    'Тяга в тренажері сидячи широким хватом': 'horizontal_pull',
    'Тяга верхнього блоку вузьким хватом': 'vertical_pull',
    'Тяга верхнього блоку за голову': 'vertical_pull',
    'Тяга верхнього блоку зворотним хватом': 'vertical_pull',
    'Тяга верхнього блоку однією рукою': 'vertical_pull',
    'Тяга верхнього блоку однією рукою вузьким хватом': 'vertical_pull',
    'Тяга верхнього блоку широким хватом': 'vertical_pull',
    'Тяга гантелей до підборіддя': 'upright_row',
    'Тяга гантелей до підборіддя нахилившись': 'upright_row',
    'Тяга гантелі в нахилі з опорою на одну ногу (Single-leg Row)': 'horizontal_pull',
    'Тяга гантелі в упорі грудьми на похилу лаву': 'horizontal_pull',
    'Тяга гантелі в упорі на лаву': 'horizontal_pull',
    'Тяга гантелі однією рукою': 'horizontal_pull',
    'Тяга гирі в стилі сумо': 'horizontal_pull',
    'Тяга гирі до поясу': 'horizontal_pull',
    'Тяга двох гантелей в нахилі': 'horizontal_pull',
    'Тяга до обличчя на блоці (Face Pull)': 'rear_delt_fly',
    'Тяга до обличчя резинкою (Face Pull)': 'rear_delt_fly',
    'Тяга жгута стоячи в нахилі': 'horizontal_pull',
    'Тяга з паралельними рукоятками (нейтральний хват)': 'horizontal_pull',
    'Тяга на петлях TRX (TRX Row)': 'horizontal_pull',
    'Тяга на петлях TRX з поворотом (TRX Row)': 'horizontal_pull',
    'Тяга нижнього блоку сидячи вузьким хватом': 'horizontal_pull',
    'Тяга нижнього блоку сидячи з підтримкою спини': 'horizontal_pull',
    'Тяга нижнього блоку широким хватом': 'horizontal_pull',
    'Тяга однією рукою в тренажері': 'horizontal_pull',
    'Тяга однієї гантелі в упорі на коліно': 'horizontal_pull',
    'Тяга прямими руками на блоці (Straight-Arm Pulldown)': 'horizontal_pull',
    'Тяга резинки до поясу стоячи': 'horizontal_pull',
    'Тяга резинки до підборіддя': 'upright_row',
    'Тяга резинки з-за голови': 'horizontal_pull',
    'Тяга рушника до себе': 'horizontal_pull',
    'Тяга рюкзака в нахилі': 'horizontal_pull',
    'Тяга саней': 'horizontal_pull',
    'Тяга саней назад': 'carry',
    'Тяга сумо з підтягуванням до підборіддя (Sumo Deadlift High Pull)': 'upright_row',
    'Тяга у нахилі з двома пляшками води': 'horizontal_pull',
    'Тяга штанги в нахилі зворотним хватом': 'horizontal_pull',
    'Тяга штанги в нахилі прямим хватом': 'horizontal_pull',
    'Тяга штанги до підборіддя': 'upright_row',
    'Тіньовий бокс': 'core_flexion',
    'Удари по лапах': 'core_flexion',
    'Удари по мішку': 'core_flexion',
    'Утримання гантелі пальцями': 'forearm',
    'Утримання диска пальцями (Plate Pinch)': 'forearm',
    'Утримання ніг вперед на брусах (L-сит)': 'core_flexion',
    'Утримання ніг вперед на кільцях (L-сит)': 'core_flexion',
    'Утримання ніг вперед на паралетах (L-сит)': 'core_flexion',
    'Утримання ніг вперед на петлях TRX (L-сит)': 'core_flexion',
    'Утримання порожньої постави (Hollow Hold)': 'core_flexion',
    'Фермерська прогулянка з гантелями': 'shrug',
    'Фермерська прогулянка з гирями': 'shrug',
    'Фермерська прогулянка на пальцях': 'shrug',
    'Французький жим EZ-штангою': 'tricep_extension',
    'Французький жим з гантеллю лежачи': 'tricep_extension',
    'Французький жим лежачи зі штангою': 'tricep_extension',
    'Французький жим однією рукою': 'tricep_extension',
    'Французький жим сидячи зі штангою': 'tricep_extension',
    'Фронтальні присідання': 'squat_bilateral',
    'Хвилі важким канатом (Battle Ropes)': 'core_flexion',
    'Ходьба на носках': 'calf_raise',
    "Ходьба на п'ятках": 'calf_raise',
    'Ходьба у швидкому темпі (Power Walk)': 'conditioning',
    'Човник (Boat pose)': 'core_flexion',
    'Шраги в тренажері Сміта': 'shrug',
    'Шраги для трапеції та шиї': 'shrug',
    'Шраги з гантелями': 'shrug',
    'Шраги з гирею': 'shrug',
    'Шраги зі штангою': 'shrug',
    'Шраги на верхньому блоці': 'shrug',
    'Штовхання саней': 'carry',
    'Ягідний місток з гантеллю': 'hip_thrust',
    'Ягідний місток зі штангою': 'hip_thrust',
    'Ягідний місток у тренажері': 'hip_thrust',
}


def get_pattern(name: str) -> str | None:
    """Ручний PATTERN_MAP має пріоритет над автоматичним AUTO_PATTERN_MAP."""
    return PATTERN_MAP.get(name) or AUTO_PATTERN_MAP.get(name)


# Які вправи вважаються базовими для кожної групи
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

# Вправи ізоляції для кожної групи
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


def find_exercises(
    muscle_group: str,
    ex_type: str,
    equipment: list,
    level: int,
    goal: str,
    used_names: set,
    count: int,
    used_patterns: set = None,
) -> list:
    """
    Знаходить вправи для конкретної групи м'язів.
    Спочатку шукає з пріоритетного списку, потім з бази.
    """
    results = []

    if ex_type == "base":
        priority_list = BASE_EXERCISES.get(muscle_group, [])
    elif ex_type == "isolation":
        priority_list = ISOLATION_EXERCISES.get(muscle_group, [])
    else:
        priority_list = BASE_EXERCISES.get(muscle_group, []) + ISOLATION_EXERCISES.get(muscle_group, [])

    for name in random.sample(priority_list, min(len(priority_list), len(priority_list))):
        if name in used_names:
            continue
        found = get_exercises(
            muscles=MUSCLE_SEARCH.get(muscle_group, [muscle_group]),
            equipment=equipment,
            level=level,
        )
        pattern = get_pattern(name)
        if used_patterns is not None and pattern and pattern in used_patterns:
            continue

        matched = filter_by_difficulty([e for e in found if e["name"] == name], level)
        if matched:
            ex = matched[0].copy()
            results.append(ex)
            used_names.add(name)
            if used_patterns is not None and pattern:
                used_patterns.add(pattern)
            if len(results) >= count:
                return results

    if len(results) < count:
        muscle_list = MUSCLE_SEARCH.get(muscle_group, [muscle_group])

        def _primary_match(ex):
            return ex.get("muscles") and ex["muscles"][0] in muscle_list

        found = get_exercises(equipment=equipment, level=level, goal=goal, ex_type="сила")
        found = filter_by_difficulty(found, level)
        found = [e for e in found if _primary_match(e)]

        if not found:
            found = get_exercises(equipment=equipment, goal=goal)
            found = filter_by_difficulty(found, level)
            found = [e for e in found if _primary_match(e)]

        if not found:
            found = get_exercises(equipment=equipment)
            found = filter_by_difficulty(found, level)
            found = [e for e in found if _primary_match(e)]

        random.shuffle(found)

        # Прохід 1: звичайний підбір з блокуванням і used_names, і патерну
        for ex in found:
            if ex["name"] in used_names or len(results) >= count:
                continue
            ex_pattern = get_pattern(ex["name"])
            if used_patterns is not None and ex_pattern and ex_pattern in used_patterns:
                continue
            results.append(ex.copy())
            used_names.add(ex["name"])
            if used_patterns is not None and ex_pattern:
                used_patterns.add(ex_pattern)

        # Прохід 2: якщо не вистачає — дозволяємо повторення патерну
        # (used_names все ще блокує)
        if len(results) < count:
            for ex in found:
                if ex["name"] in used_names or len(results) >= count:
                    continue
                results.append(ex.copy())
                used_names.add(ex["name"])

        # Прохід 3: якщо навіть після цього не вистачає (обладнання дуже
        # обмежене, всі підходящі вправи вже використані раніше цього тижня)
        # — дозволяємо повторити ту саму вправу в інший день. Це нормальна
        # практика в реальних програмах, краще за порожній день.
        if len(results) < count and found:
            already_in_this_slot = {e["name"] for e in results}
            for ex in found:
                if len(results) >= count:
                    break
                if ex["name"] in already_in_this_slot:
                    continue
                results.append(ex.copy())
                already_in_this_slot.add(ex["name"])

    return results


# ══════════════════════════════════════════════════════
# ГЕНЕРАТОР ПРОГРАМИ
# ══════════════════════════════════════════════════════


SUPERSET_PAIRS = {
    frozenset({"груди", "трицепс"}),
    frozenset({"груди", "біцепс"}),
    frozenset({"спина_ширина", "біцепс"}),
    frozenset({"спина_товщина", "біцепс"}),
    frozenset({"плечі", "трицепс"}),
    frozenset({"плечі", "задні дельти"}),
    frozenset({"квадрицепс", "біцепс стегна"}),
}


def build_supersets(day_exercises: list) -> list:
    """Для рівнів 3-4 об'єднує ізоляційні вправи в суперсети,
    зберігаючи їх на початковій позиції в списку (а не в кінці)."""
    n = len(day_exercises)
    iso_idx = [i for i, e in enumerate(day_exercises) if e.get("ex_type") == "isolation"]

    by_group = {}
    for i in iso_idx:
        g = day_exercises[i].get("_group", "")
        by_group.setdefault(g, []).append(i)

    pairs = []
    groups = list(by_group.keys())
    for gi in range(len(groups)):
        for gj in range(gi + 1, len(groups)):
            g1, g2 = groups[gi], groups[gj]
            if frozenset({g1, g2}) in SUPERSET_PAIRS:
                while by_group[g1] and by_group[g2]:
                    pairs.append((by_group[g1].pop(0), by_group[g2].pop(0)))

    for items in by_group.values():
        while len(items) >= 2:
            pairs.append((items.pop(0), items.pop(0)))

    skip = set()
    anchor_pair = {}
    sid = 1
    for a, b in pairs:
        anchor = min(a, b)
        partner = max(a, b)
        anchor_pair[anchor] = partner
        skip.add(partner)
        day_exercises[a]["superset_id"] = sid
        day_exercises[b]["superset_id"] = sid
        sid += 1

    result = []
    for i in range(n):
        if i in skip:
            continue
        result.append(day_exercises[i])
        if i in anchor_pair:
            result.append(day_exercises[anchor_pair[i]])
    return result


# ══════════════════════════════════════════════════════
# ОБСЯГ ТРЕНУВАНЬ — MEV / MAV / MRV
# ══════════════════════════════════════════════════════
# MEV — мінімальний ефективний обсяг (менше — м'яз майже не росте)
# MAV — оптимальний обсяг для більшості людей
# MRV — максимальний обсяг, вище якого відновлення не встигає
# Значення в підходах на тиждень.

# Деякі "групи" в DAY_STRUCTURES фізично одна й та сама м'язова
# група, розділена лише для точнішого підбору вправ (наприклад
# спина_ширина/спина_товщина обидві навантажують широчайші).
# Тому для обсягу їх рахуємо разом, під одним ключем.
VOLUME_ALIAS = {
    "спина_ширина": "спина",
    "спина_товщина": "спина",
}


def real_muscle(group: str) -> str:
    """Повертає фізичну м'язову групу для обліку обсягу."""
    return VOLUME_ALIAS.get(group, group)


VOLUME_LANDMARKS = {
    "груди":         {"MEV": 8,  "MAV": 14, "MRV": 22},
    "спина":         {"MEV": 10, "MAV": 18, "MRV": 25},
    "квадрицепс":    {"MEV": 8,  "MAV": 14, "MRV": 20},
    "біцепс стегна": {"MEV": 6,  "MAV": 10, "MRV": 16},
    "сідниці":       {"MEV": 4,  "MAV": 10, "MRV": 16},
    "плечі":         {"MEV": 8,  "MAV": 16, "MRV": 22},
    "задні дельти":  {"MEV": 6,  "MAV": 14, "MRV": 20},
    "трапеція":      {"MEV": 4,  "MAV": 10, "MRV": 16},
    "біцепс":        {"MEV": 6,  "MAV": 14, "MRV": 20},
    "трицепс":       {"MEV": 6,  "MAV": 12, "MRV": 18},
    "прес":          {"MEV": 0,  "MAV": 20, "MRV": 35},
    "литки":         {"MEV": 8,  "MAV": 16, "MRV": 25},
}


def calculate_weekly_volume(day_keys: list, goal: str, level: int) -> dict:
    """Рахує сумарний тижневий обсяг (підходи) по кожній м'язовій групі,
    враховуючи, що один day_key може повторюватись кілька разів на тиждень."""
    volume = {}
    for day_key in day_keys:
        template = DAY_STRUCTURES.get(day_key)
        if not template:
            continue
        for muscle_group, ex_type, count in template["structure"]:
            key = real_muscle(muscle_group)
            sets, _ = get_sets_reps(ex_type, goal, level)
            volume[key] = volume.get(key, 0) + count * sets
    return volume


def calculate_scale_factors(volume: dict) -> dict:
    """Для груп, що перевищують MRV — коефіцієнт зменшення (0-1).
    Групи нижче MEV поки не займаємо (factor=1) — це окрема задача."""
    factors = {}
    for group, total in volume.items():
        lm = VOLUME_LANDMARKS.get(group)
        if not lm or total <= lm["MRV"]:
            factors[group] = 1.0
        else:
            factors[group] = round(lm["MRV"] / total, 3)
    return factors


def apply_scale_to_sets(base_sets: int, muscle_group: str, factors: dict) -> int:
    """Застосовує коефіцієнт корекції до кількості підходів,
    не даючи опуститись нижче 1 підходу."""
    key = real_muscle(muscle_group)
    factor = factors.get(key, 1.0)
    return max(1, round(base_sets * factor))


def generate_program(location: str, equipment: list, goal: str, level: int, days: int) -> dict:
    split_key = SPLITS.get(location, SPLITS["зал"])
    level_splits = split_key.get(level, split_key[1])
    day_keys = level_splits.get(days, level_splits[min(days, max(level_splits.keys()))])

    # ── НОВЕ: рахуємо тижневий обсяг ОДИН РАЗ, до генерації днів ──
    weekly_volume = calculate_weekly_volume(day_keys, goal, level)
    volume_factors = calculate_scale_factors(weekly_volume)

    program = {}
    used_names = set()  # захист від повторів між днями

    for day_num, day_key in enumerate(day_keys, 1):
        used_patterns = set()
        template = DAY_STRUCTURES.get(day_key)
        if not template:
            continue

        # День відновлення
        if day_key == "gym_recovery_4":
            program[day_num] = {
                "name": template["name"],
                "exercises": [],
                "note": template.get("note", ""),
            }
            continue

        day_exercises = []

        for muscle_group, ex_type, count in template["structure"]:

            if ex_type in ("abs", "calves"):
                # Для прес і литок — не блокуємо повтори між днями,
                # і не блокуємо патерн (у преса/литок замало патернів,
                # щоб жорстко розділяти — кілька видів скручувань за
                # тренування це нормально)
                local_used = set()
                found = find_exercises(
                    muscle_group=muscle_group,
                    ex_type=ex_type,
                    equipment=equipment,
                    level=level,
                    goal=goal,
                    used_names=local_used,
                    count=count,
                    used_patterns=None,
                )
            else:
                found = find_exercises(
                    muscle_group=muscle_group,
                    ex_type=ex_type,
                    equipment=equipment,
                    level=level,
                    goal=goal,
                    used_names=used_names,
                    count=count,
                    used_patterns=used_patterns,
                )


            # Додаємо підходи і повтори — тепер зі скоригованим обсягом
            sets, reps = get_sets_reps(ex_type, goal, level)
            sets = apply_scale_to_sets(sets, muscle_group, volume_factors)  # НОВЕ
            for ex in found:
                ex["sets"] = sets
                ex["reps"] = reps
                ex["ex_type"] = ex_type
                ex["_group"] = muscle_group

            day_exercises.extend(found)

        if level in (3, 4):
            day_exercises = build_supersets(day_exercises)

        program[day_num] = {
            "name": template["name"],
            "exercises": day_exercises,
            "note": template.get("note", ""),
        }

    return program


# ══════════════════════════════════════════════════════
# ФОРМАТУВАННЯ ТЕКСТУ ПРОГРАМИ
# ══════════════════════════════════════════════════════


GROUP_LABELS = {
    "груди": "Груди",
    "спина_ширина": "Спина (ширина)",
    "спина_товщина": "Спина (товщина)",
    "квадрицепс": "Квадрицепс",
    "біцепс стегна": "Задня поверхня стегна",
    "сідниці": "Сідниці",
    "плечі": "Плечі",
    "задні дельти": "Задні дельти",
    "трапеція": "Трапеція",
    "біцепс": "Біцепс",
    "трицепс": "Трицепс",
    "прес": "Прес",
    "литки": "Литки",
}


def format_program(program: dict, goal: str, level: int, days: int, equipment: list) -> list:
    """Повертає список частин тексту (може бути кілька якщо довге)"""
    goal_names = {
        "маса": "💪 Набір маси",
        "рельєф": "✂️ Рельєф",
        "сила": "🏋️ Сила",
        "схуднення": "🔥 Схуднення",
        "витривалість": "🏃 Витривалість",
    }
    level_names = {
        1: "🟢 Початківець",
        2: "🟡 Середній",
        3: "🔴 Просунутий",
        4: "🔥 Атлет",
    }

    header = (
        f"🤖 <b>Твоя програма тренувань</b>\n\n"
        f"🎯 Ціль: {goal_names.get(goal, goal)}\n"
        f"⚡ Рівень: {level_names.get(level, level)}\n"
        f"📅 Днів: {days}\n"
        f"🏋️ Обладнання: {', '.join(equipment)}\n"
        f"━━━━━━━━━━━━━━━━\n"
    )

    parts = [header]
    current = header

    for day_num, day_data in program.items():
        day_text = f"\n📌 <b>День {day_num} — {day_data['name']}</b>\n"

        if not day_data["exercises"] and day_data.get("note"):
            day_text += day_data["note"] + "\n"
        else:
            prev_group = None
            exs = day_data["exercises"]
            i = 0
            while i < len(exs):
                ex = exs[i]
                group = ex.get("_group")
                if group != prev_group:
                    label = GROUP_LABELS.get(group, group)
                    if label:
                        day_text += f"\n<i>— {label} —</i>\n"
                prev_group = group

                sid = ex.get("superset_id")
                if sid is not None and i + 1 < len(exs) and exs[i + 1].get("superset_id") == sid:
                    partner = exs[i + 1]
                    partner_group = partner.get("_group")
                    if partner_group and partner_group != group:
                        g1 = GROUP_LABELS.get(group, group)
                        g2 = GROUP_LABELS.get(partner_group, partner_group)
                        day_text += (
                            f"🔗 <b>Суперсет</b> ({g1} + {g2}, без відпочинку):\n"
                            f"   1) {ex['name']} — {ex['sets']}×{ex['reps']}\n"
                            f"   2) {partner['name']} — {partner['sets']}×{partner['reps']}\n"
                        )
                    else:
                        day_text += (
                            "🔗 <b>Суперсет</b> (без відпочинку між вправами):\n"
                            f"   1) {ex['name']} — {ex['sets']}×{ex['reps']}\n"
                            f"   2) {partner['name']} — {partner['sets']}×{partner['reps']}\n"
                        )
                    i += 2
                    continue

                day_text += f"• {ex['name']} — {ex['sets']}×{ex['reps']}\n"
                i += 1

            if day_data.get("note"):
                day_text += f"\n{day_data['note']}\n"

        # Розбиваємо на частини якщо текст великий
        if len(current) + len(day_text) > 3800:
            parts.append(current)
            current = day_text
        else:
            current += day_text

    if current and current != header:
        if current not in parts:
            parts.append(current)
    elif len(parts) == 1:
        parts[0] = current

    # Поради по рівню
    tips = {
        1: "\n💡 <b>Поради:</b>\nФокус на техніці. Відпочинок 60-90 сек між підходами.",
        2: "\n💡 <b>Поради:</b>\nПрогресуй вагу щотижня. Відпочинок 90 сек між підходами.",
        3: "\n💡 <b>Поради:</b>\nБазові: 2-3 хв відпочинку. Ізоляція: 60-90 сек. Негативна фаза 2-3 сек.",
        4: "\n💡 <b>Поради:</b>\nБазові: 2-3 хв. Ізоляція: 60-90 сек. 1-2 повт до відмови. Темп 2-3 сек негатив.",
    }
    parts[-1] += tips.get(level, "")

    return parts


# ══════════════════════════════════════════════════════
# ХЕНДЛЕРИ TELEGRAM
# ══════════════════════════════════════════════════════

async def check_generation_limit(callback: CallbackQuery) -> bool:
    user = await get_user(callback.from_user.id)
    sub = user.get("subscription", "free") if user else "free"
    if sub == "free":
        last_gen = user.get("last_generation_date", "") if user else ""
        if last_gen:
            try:
                last_date = datetime.strptime(last_gen, "%d.%m.%Y")
                if datetime.now() - last_date < timedelta(days=7):
                    next_date = (last_date + timedelta(days=7)).strftime("%d.%m.%Y")
                    await callback.answer(
                        f"❌ Безкоштовно — 1 генерація на тиждень.\nНаступна: {next_date}",
                        show_alert=True
                    )
                    return False
            except ValueError:
                pass
    return True


async def generate_and_send(callback: CallbackQuery, state: FSMContext, location, equipment, goal, level, days):
    await callback.message.edit_text("⏳ Генерую програму...")

    program = generate_program(location, equipment, goal, level, days)

    if not program:
        await callback.message.edit_text(
            "❌ Не вдалося знайти вправи для твоїх параметрів.\n"
            "Спробуй додати більше обладнання або змінити локацію.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Спробувати ще раз", callback_data="open_generator")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
            ]),
        )
        return

    await state.update_data(
        current_program=program_to_storable(program),
        current_goal=goal,
        current_level=level,
        current_days=days,
        current_equipment=equipment,
    )

    parts = format_program(program, goal, level, days, equipment)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data="regen_program")],
        [InlineKeyboardButton(text="🔁 Замінити вправу", callback_data="replace_start")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])

    for i, part in enumerate(parts):
        if i == 0:
            await callback.message.edit_text(part, reply_markup=kb if len(parts) == 1 else None)
        elif i == len(parts) - 1:
            await callback.message.answer(part, reply_markup=kb)
        else:
            await callback.message.answer(part)

    user = await get_user(callback.from_user.id)
    sub = user.get("subscription", "free") if user else "free"
    if sub == "free":
        await update_user_field(
            callback.from_user.id,
            "last_generation_date",
            datetime.now().strftime("%d.%m.%Y")
        )


@router.callback_query(F.data == "open_generator")
async def generator_start(callback: CallbackQuery, state: FSMContext):
    if not await check_generation_limit(callback):
        return

    await state.set_state(GeneratorStates.location)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ Тренажерний зал", callback_data="loc_gym")],
        [InlineKeyboardButton(text="🏠 Вдома", callback_data="loc_home")],
        [InlineKeyboardButton(text="🌳 Вулиця / Майданчик", callback_data="loc_outdoor")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "🤖 <b>Генератор програм</b>\n\n"
        "Крок 1/5 — Де будеш тренуватись?",
        reply_markup=kb,
    )


@router.callback_query(GeneratorStates.location, F.data.startswith("loc_"))
async def generator_location(callback: CallbackQuery, state: FSMContext):
    location, loc_name = LOCATION_MAP[callback.data]
    await state.update_data(location=location, selected_equipment=[])

    if location == "зал":
        buttons = [
            [InlineKeyboardButton(text="🏋️ Штанга", callback_data="eq_barbell"),
             InlineKeyboardButton(text="💪 Гантелі", callback_data="eq_dumbbells")],
            [InlineKeyboardButton(text="⚙️ Тренажери", callback_data="eq_machines"),
             InlineKeyboardButton(text="🎽 Гиря", callback_data="eq_kettlebell")],
            [InlineKeyboardButton(text="🔵 TRX", callback_data="eq_trx"),
             InlineKeyboardButton(text="🔴 Резинки", callback_data="eq_bands")],
            [InlineKeyboardButton(text="✅ Далі →", callback_data="eq_done")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
        ]
    elif location == "дома":
        buttons = [
            [InlineKeyboardButton(text="💪 Гантелі", callback_data="eq_dumbbells"),
             InlineKeyboardButton(text="🎽 Гиря", callback_data="eq_kettlebell")],
            [InlineKeyboardButton(text="🔴 Резинки", callback_data="eq_bands"),
             InlineKeyboardButton(text="🔵 TRX", callback_data="eq_trx")],
            [InlineKeyboardButton(text="🏃 Власна вага", callback_data="eq_bodyweight")],
            [InlineKeyboardButton(text="✅ Далі →", callback_data="eq_done")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="🔝 Турнік", callback_data="eq_pullup"),
             InlineKeyboardButton(text="🤸 Бруси", callback_data="eq_bars")],
            [InlineKeyboardButton(text="🔴 Резинки", callback_data="eq_bands"),
             InlineKeyboardButton(text="🏃 Власна вага", callback_data="eq_bodyweight")],
            [InlineKeyboardButton(text="⭕ Кільця", callback_data="eq_rings"),
             InlineKeyboardButton(text="🎽 Гиря", callback_data="eq_kettlebell")],
            [InlineKeyboardButton(text="✅ Далі →", callback_data="eq_done")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
        ]

    await state.set_state(GeneratorStates.equipment)
    await callback.message.edit_text(
        f"📍 Локація: <b>{loc_name}</b>\n\n"
        "Крок 2/5 — Яке обладнання є?\n"
        "<i>Вибери кілька → натисни Далі</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(GeneratorStates.equipment, F.data.startswith("eq_"))
async def generator_equipment(callback: CallbackQuery, state: FSMContext):
    if callback.data == "eq_done":
        data = await state.get_data()
        selected = data.get("selected_equipment", [])

        # Якщо нічого не вибрано — додаємо власну вагу
        if not selected:
            selected = ["власна вага"]
            await state.update_data(selected_equipment=selected)

        await ask_goal(callback, state)
        return

    data = await state.get_data()
    selected = data.get("selected_equipment", [])
    eq_name = EQUIPMENT_MAP.get(callback.data, "")

    if eq_name in selected:
        selected.remove(eq_name)
        if eq_name == "тренажер" and "блок" in selected:
            selected.remove("блок")
        await callback.answer(f"❌ {eq_name} прибрано")
    else:
        selected.append(eq_name)
        if eq_name == "тренажер" and "блок" not in selected:
            selected.append("блок")
        await callback.answer(f"✅ {eq_name} додано")

    await state.update_data(selected_equipment=selected)
    selected_text = ", ".join(selected) if selected else "нічого"
    data = await state.get_data()
    loc_name = {"зал": "🏋️ Зал", "дома": "🏠 Дома", "вулиця": "🌳 Вулиця"}.get(data["location"], "")

    await callback.message.edit_text(
        f"📍 Локація: <b>{loc_name}</b>\n"
        f"🏋️ Обрано: <b>{selected_text}</b>\n\n"
        "Крок 2/5 — Яке обладнання є?\n"
        "<i>Вибери кілька → натисни Далі</i>",
        reply_markup=callback.message.reply_markup,
    )


async def ask_goal(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GeneratorStates.goal)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💪 Набір маси", callback_data="goal_mass")],
        [InlineKeyboardButton(text="✂️ Рельєф / Сушка", callback_data="goal_relief")],
        [InlineKeyboardButton(text="🏋️ Сила", callback_data="goal_strength")],
        [InlineKeyboardButton(text="🔥 Схуднення", callback_data="goal_loss")],
        [InlineKeyboardButton(text="🏃 Витривалість", callback_data="goal_endurance")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "Крок 3/5 — Яка твоя ціль?",
        reply_markup=kb,
    )


@router.callback_query(GeneratorStates.goal, F.data.startswith("goal_"))
async def generator_goal(callback: CallbackQuery, state: FSMContext):
    goal = GOAL_MAP[callback.data]
    await state.update_data(goal=goal)
    await state.set_state(GeneratorStates.level)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Початківець — до 6 місяців", callback_data="lvl_1")],
        [InlineKeyboardButton(text="🟡 Середній — 6-18 місяців", callback_data="lvl_2")],
        [InlineKeyboardButton(text="🔴 Просунутий — 1.5-3 роки", callback_data="lvl_3")],
        [InlineKeyboardButton(text="🔥 Атлет — 3+ роки", callback_data="lvl_4")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "Крок 4/5 — Твій рівень підготовки?",
        reply_markup=kb,
    )


@router.callback_query(GeneratorStates.level, F.data.startswith("lvl_"))
async def generator_level(callback: CallbackQuery, state: FSMContext):
    level_num, _ = LEVEL_MAP[callback.data]
    await state.update_data(level=level_num)
    await state.set_state(GeneratorStates.days)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 день", callback_data="days_1"),
            InlineKeyboardButton(text="2 дні", callback_data="days_2"),
            InlineKeyboardButton(text="3 дні", callback_data="days_3"),
        ],
        [
            InlineKeyboardButton(text="4 дні", callback_data="days_4"),
            InlineKeyboardButton(text="5 днів", callback_data="days_5"),
            InlineKeyboardButton(text="6 днів", callback_data="days_6"),
        ],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "Крок 5/5 — Скільки днів на тиждень тренуєшся?",
        reply_markup=kb,
    )


@router.callback_query(GeneratorStates.days, F.data.startswith("days_"))
async def generator_days(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.replace("days_", ""))
    data = await state.get_data()

    location = data["location"]
    equipment = data["selected_equipment"]
    goal = data["goal"]
    level = data["level"]

    await state.update_data(
        last_location=location,
        last_equipment=equipment,
        last_goal=goal,
        last_level=level,
        last_days=days,
    )
    await state.set_state(None)

    await generate_and_send(callback, state, location, equipment, goal, level, days)


@router.callback_query(F.data == "regen_program")
async def regen_program(callback: CallbackQuery, state: FSMContext):
    if not await check_generation_limit(callback):
        return

    data = await state.get_data()
    location = data.get("last_location")
    equipment = data.get("last_equipment")
    goal = data.get("last_goal")
    level = data.get("last_level")
    days = data.get("last_days")

    if not all([location, equipment, goal, level, days]):
        await callback.answer("⚠️ Параметри втрачені, почни спочатку", show_alert=True)
        await generator_start(callback, state)
        return

    await generate_and_send(callback, state, location, equipment, goal, level, days)


@router.callback_query(F.data == "replace_start")
async def replace_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    stored = data.get("current_program")
    if not stored:
        await callback.answer("⚠️ Спочатку згенеруй програму", show_alert=True)
        return
    program = program_from_storable(stored)

    buttons = []
    for day_num, day_data in program.items():
        if not day_data.get("exercises"):
            continue
        buttons.append([InlineKeyboardButton(
            text=f"День {day_num} — {day_data['name']}",
            callback_data=f"replace_day:{day_num}",
        )])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="replace_cancel")])

    await callback.message.answer(
        "🔁 <b>Заміна вправи</b>\n\nОбери день:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("replace_day:"))
async def replace_day(callback: CallbackQuery, state: FSMContext):
    day_num = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    stored = data.get("current_program")
    if not stored:
        await callback.answer("⚠️ Програма застаріла", show_alert=True)
        return
    program = program_from_storable(stored)
    day_data = program.get(day_num)
    if not day_data:
        await callback.answer("⚠️ День не знайдено", show_alert=True)
        return

    buttons = []
    for i, ex in enumerate(day_data["exercises"]):
        label = ex["name"]
        if len(label) > 45:
            label = label[:42] + "..."
        buttons.append([InlineKeyboardButton(text=f"{i + 1}. {label}", callback_data=f"replace_ex:{day_num}:{i}")])
    buttons.append([InlineKeyboardButton(text="❌ Скасувати", callback_data="replace_cancel")])

    await callback.message.edit_text(
        f"🔁 <b>День {day_num} — {day_data['name']}</b>\n\nЯку вправу замінити?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("replace_ex:"))
async def replace_ex(callback: CallbackQuery, state: FSMContext):
    _, day_num_str, idx_str = callback.data.split(":")
    day_num = int(day_num_str)
    idx = int(idx_str)

    data = await state.get_data()
    stored = data.get("current_program")
    equipment = data.get("current_equipment", [])
    level = data.get("current_level", 1)
    goal = data.get("current_goal", "маса")
    days = data.get("current_days", 1)

    if not stored:
        await callback.answer("⚠️ Програма застаріла", show_alert=True)
        return

    program = program_from_storable(stored)
    day_data = program.get(day_num)
    if not day_data or idx >= len(day_data["exercises"]):
        await callback.answer("⚠️ Вправу не знайдено", show_alert=True)
        return

    old_ex = day_data["exercises"][idx]
    used_names = {e["name"] for e in day_data["exercises"]}

    candidates = []
    for alt_name in old_ex.get("alternatives", []):
        matches = [e for e in get_exercises(equipment=equipment) if e["name"] == alt_name]
        matches = filter_by_difficulty(matches, level)
        candidates.extend(m for m in matches if m["name"] not in used_names)

    if not candidates:
        fallback = find_exercises(
            muscle_group=old_ex.get("_group", ""),
            ex_type=old_ex.get("ex_type", "isolation"),
            equipment=equipment,
            level=level,
            goal=goal,
            used_names=set(used_names),
            count=1,
        )
        candidates = fallback

    if not candidates:
        await callback.answer("😔 Немає доступної заміни під твоє обладнання", show_alert=True)
        return

    new_ex = random.choice(candidates).copy()
    new_ex["sets"] = old_ex["sets"]
    new_ex["reps"] = old_ex["reps"]
    new_ex["ex_type"] = old_ex.get("ex_type")
    new_ex["_group"] = old_ex.get("_group")
    if "superset_id" in old_ex:
        new_ex["superset_id"] = old_ex["superset_id"]

    day_data["exercises"][idx] = new_ex
    program[day_num] = day_data

    await state.update_data(current_program=program_to_storable(program))

    parts = format_program(program, goal, level, days, equipment)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data="regen_program")],
        [InlineKeyboardButton(text="🔁 Замінити вправу", callback_data="replace_start")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])

    await callback.message.edit_text(f"✅ Замінено: {old_ex['name']} → {new_ex['name']}")

    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            await callback.message.answer(part, reply_markup=kb)
        else:
            await callback.message.answer(part)

    await callback.answer("Вправу замінено ✅")


@router.callback_query(F.data == "replace_cancel")
async def replace_cancel(callback: CallbackQuery):
    await callback.message.edit_text("Гаразд, залишаємо як є 🙂")
    await callback.answer()