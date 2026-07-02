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


# ══════════════════════════════════════════════════════
# ПІДХОДИ / ПОВТОРИ
# ══════════════════════════════════════════════════════

def get_sets_reps(ex_type: str, goal: str, level: int) -> tuple:
    table = {
        "base": {
            "маса":       {1:(3,"10-12"), 2:(4,"8-10"), 3:(5,"6-8"),  4:(5,"5-8")},
            "сила":       {1:(3,"6-8"),  2:(4,"5-6"),  3:(5,"4-6"),  4:(6,"3-5")},
            "рельєф":     {1:(3,"12-15"),2:(4,"10-12"),3:(4,"10-12"),4:(4,"10-12")},
            "схуднення":  {1:(3,"15-20"),2:(3,"15"),   3:(4,"12-15"),4:(4,"12-15")},
            "витривалість":{1:(3,"20"),  2:(3,"20"),   3:(4,"15-20"),4:(4,"15-20")},
        },
        "assist": {
            "маса":       {1:(3,"10-12"),2:(4,"10"),   3:(4,"8-10"), 4:(4,"8-10")},
            "сила":       {1:(3,"8-10"), 2:(3,"8"),    3:(4,"6-8"),  4:(4,"6-8")},
            "рельєф":     {1:(3,"12-15"),2:(3,"12"),   3:(4,"12"),   4:(4,"12-15")},
            "схуднення":  {1:(3,"15"),   2:(3,"15"),   3:(3,"15"),   4:(3,"15")},
            "витривалість":{1:(3,"20"),  2:(3,"15-20"),3:(3,"15-20"),4:(3,"15-20")},
        },
        "isolation": {
            "маса":       {1:(2,"12-15"),2:(3,"12"),   3:(3,"12-15"),4:(4,"12-15")},
            "сила":       {1:(2,"10-12"),2:(3,"10"),   3:(3,"10-12"),4:(3,"10-12")},
            "рельєф":     {1:(2,"15"),   2:(3,"15"),   3:(3,"15"),   4:(4,"15")},
            "схуднення":  {1:(2,"20"),   2:(3,"20"),   3:(3,"15-20"),4:(3,"15-20")},
            "витривалість":{1:(2,"20"),  2:(3,"20"),   3:(3,"20"),   4:(3,"20")},
        },
        "abs":    {g: {l:(3,"15-20") for l in [1,2,3,4]} for g in GOAL_MAP.values()},
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
) -> list:
    """
    Знаходить вправи для конкретної групи м'язів.
    Спочатку шукає з пріоритетного списку, потім з бази.
    """
    results = []

    # Список пріоритетних вправ
    if ex_type == "base":
        priority_list = BASE_EXERCISES.get(muscle_group, [])
    elif ex_type == "isolation":
        priority_list = ISOLATION_EXERCISES.get(muscle_group, [])
    else:  # assist — суміш базових і допоміжних
        priority_list = BASE_EXERCISES.get(muscle_group, []) + ISOLATION_EXERCISES.get(muscle_group, [])

    # Спочатку шукаємо з пріоритетного списку
    for name in random.sample(priority_list, min(len(priority_list), len(priority_list))):
        if name in used_names:
            continue
        # Перевіряємо чи є в базі з потрібним обладнанням
        found = get_exercises(
            muscles=MUSCLE_SEARCH.get(muscle_group, [muscle_group]),
            equipment=equipment,
            level=level,
        )
        # Фільтруємо по назві
        matched = [e for e in found if e["name"] == name]
        if matched:
            ex = matched[0].copy()
            results.append(ex)
            used_names.add(name)
            if len(results) >= count:
                return results

    # Якщо не вистачає — шукаємо з бази по м'язах
    if len(results) < count:
        muscle_list = MUSCLE_SEARCH.get(muscle_group, [muscle_group])
        for muscle in muscle_list:
            # З рівнем і ціллю
            found = get_exercises(
                muscles=[muscle],
                equipment=equipment,
                level=level,
                goal=goal,
                ex_type="сила",
            )
            # Без рівня
            if not found:
                found = get_exercises(muscles=[muscle], equipment=equipment, goal=goal)
            # Без цілі
            if not found:
                found = get_exercises(muscles=[muscle], equipment=equipment)

            random.shuffle(found)
            for ex in found:
                if ex["name"] not in used_names and len(results) < count:
                    results.append(ex.copy())
                    used_names.add(ex["name"])

            if len(results) >= count:
                break

    return results


# ══════════════════════════════════════════════════════
# ГЕНЕРАТОР ПРОГРАМИ
# ══════════════════════════════════════════════════════

def generate_program(location: str, equipment: list, goal: str, level: int, days: int) -> dict:
    split_key = SPLITS.get(location, SPLITS["зал"])
    level_splits = split_key.get(level, split_key[1])
    day_keys = level_splits.get(days, level_splits[min(days, max(level_splits.keys()))])

    program = {}
    used_names = set()  # захист від повторів між днями

    for day_num, day_key in enumerate(day_keys, 1):
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
                # Для прес і литок — не блокуємо повтори між днями
                local_used = set()
                found = find_exercises(
                    muscle_group=muscle_group,
                    ex_type=ex_type,
                    equipment=equipment,
                    level=level,
                    goal=goal,
                    used_names=local_used,
                    count=count,
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
                )

            # Додаємо підходи і повтори
            sets, reps = get_sets_reps(ex_type, goal, level)
            for ex in found:
                ex["sets"] = sets
                ex["reps"] = reps
                ex["ex_type"] = ex_type

            day_exercises.extend(found)

        program[day_num] = {
            "name": template["name"],
            "exercises": day_exercises,
            "note": template.get("note", ""),
        }

    return program


# ══════════════════════════════════════════════════════
# ФОРМАТУВАННЯ ТЕКСТУ ПРОГРАМИ
# ══════════════════════════════════════════════════════

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
            prev_type = None
            for ex in day_data["exercises"]:
                ex_type = ex.get("ex_type", "base")
                # Розділювач між секціями
                if prev_type in ("base", "assist") and ex_type == "abs":
                    day_text += "\n<i>— Прес —</i>\n"
                elif prev_type in ("base", "assist") and ex_type == "calves":
                    day_text += "\n<i>— Литки —</i>\n"
                prev_type = ex_type
                day_text += f"• {ex['name']} — {ex['sets']}×{ex['reps']}\n"

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

@router.callback_query(F.data == "open_generator")
async def generator_start(callback: CallbackQuery, state: FSMContext):
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
                    return
            except ValueError:
                pass

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
        await callback.answer(f"❌ {eq_name} прибрано")
    else:
        selected.append(eq_name)
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
    await state.clear()

    location = data["location"]
    equipment = data["selected_equipment"]
    goal = data["goal"]
    level = data["level"]

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

    parts = format_program(program, goal, level, days, equipment)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Згенерувати ще", callback_data="open_generator")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])

    for i, part in enumerate(parts):
        if i == 0:
            await callback.message.edit_text(part, reply_markup=kb if len(parts) == 1 else None)
        elif i == len(parts) - 1:
            await callback.message.answer(part, reply_markup=kb)
        else:
            await callback.message.answer(part)

    # Зберігаємо дату для free
    user = await get_user(callback.from_user.id)
    sub = user.get("subscription", "free") if user else "free"
    if sub == "free":
        await update_user_field(
            callback.from_user.id,
            "last_generation_date",
            datetime.now().strftime("%d.%m.%Y")
        )
