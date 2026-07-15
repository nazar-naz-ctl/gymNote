"""
Split Engine
════════════
Шаблони тренувальних днів (DAY_STRUCTURES) та розподіл
цих шаблонів по днях тижня залежно від локації/рівня/кількості
днів (SPLITS).
"""

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
