# ══════════════════════════════════════════════════════
# auto_tag_patterns.py
# Автоматично визначає руховий патерн для кожної вправи в базі
# на основі назви + м'язових тегів. Не змінює exercises_db.py —
# лише генерує AUTO_PATTERN_MAP, яку ти вставиш в generator.py.
#
# Запуск: поклади цей файл в корінь проєкту gymNote (поруч з
# exercises_db.py) і запусти через PyCharm (Run).
# ══════════════════════════════════════════════════════

from exercises_db import exercises

# Патерни, які вже задані вручну в PATTERN_MAP generator.py —
# для них скрипт НЕ пропонує заміну, щоб не затерти ручну роботу.
# Встав сюди актуальний список назв, які вже є в PATTERN_MAP.
ALREADY_TAGGED = set()  # заповниться нижче автоматично, якщо встромиш свій PATTERN_MAP


def classify_pattern(ex):
    name = ex["name"].lower()
    muscles = [m.lower() for m in ex.get("muscles", [])]

    def has_muscle(*keys):
        return any(any(k in m for k in keys) for m in muscles)

    def has_word(*words):
        return any(w in name for w in words)

    # ── Олімпійські рухи (ривок/поштовх/кліп) — перевіряємо ПЕРШИМИ,
    # бо вони full-body і можуть хибно зматчитись під інші правила ──
    if has_word("ривок", "ривкова", "снеч", "snatch") and has_muscle("все тіло"):
        return "olympic_pull"
    if has_word("поштовх") and has_muscle("все тіло"):
        return "olympic_press"
    if has_word("тяга в стрибок", "clean pull"):
        return "olympic_pull"

    # ── Мускул-ап / вихід силою (перевіряємо перед звичайними тягами) ──
    if has_word("вихід силою", "мускул-ап", "muscle-up", "лучник", "archer"):
        return "vertical_pull_explosive"

    # ── Присідання / squat ──
    if has_word("присід") or has_word("гак-присідання") or has_word("гоблет"):
        if has_word("пістолетик") or has_word("одній нозі") or has_word("skater"):
            return "squat_unilateral"
        if has_word("стрибк") or has_word("jump"):
            return "squat_explosive"
        if has_word("тренажер") or has_word("жим ногами") or has_word("гакк"):
            return "squat_machine"
        return "squat_bilateral"
    if has_word("жим ногами"):
        return "squat_machine"

    # ── Випади / lunge ──
    if has_word("випад", "зашагування"):
        return "lunge_unilateral"

    # ── Відведення/зведення ніг (абдукція/аддукція стегна) ──
    if has_word("відведення ноги", "кроки крабом") and has_muscle("сідниці", "відвідні"):
        return "hip_abduction"
    if has_word("зведення ніг") and has_muscle("внутрішня поверхня стегна"):
        return "hip_adduction"

    # ── Міст / Hip Thrust (ловимо і "міст", і "місток") ──
    if has_word("міст", "hip thrust", "ягідний", "підйом таза") and not has_word("кістьовий"):
        return "hip_thrust_unilateral" if has_word("одній нозі") else "hip_thrust"

    # ── Активація сідниць / глют-ізоляція без явного слова ──
    if has_word("активація") and has_muscle("сідниці"):
        return "hip_thrust"

    # ── Hip hinge (станова, румунська, гіперекстензія, розгинання спини, супермен, махи) ──
    if has_word("станова тяга", "румунська тяга", "мертва тяга", "гіперекстензія",
                "гарне ранок", "good morning", "розгинання спини", "супермен", "махи"):
        return "hip_hinge_deadlift" if has_word("станова", "мертва") else "hip_hinge"

    # ── Згинання ніг (leg curl) — розширено на "однієї ноги" ──
    if has_word("згинання ніг", "згинання гомілки", "нордичне", "згинання однієї ноги"):
        return "leg_curl"

    # ── Розгинання ніг ──
    if has_word("розгинання ніг"):
        return "leg_extension"

    # ── Литки — розширено: не тільки "носк", а й "литок/литки" в назві ──
    if (has_word("носк") or has_word("литок", "литки")) and has_muscle("литк", "камбалоподібн", "гомілк"):
        return "calf_raise"
    if has_word("ходьба на п'ятках", "ходьба на носках"):
        return "calf_raise"

    # ── Груди — жими (розрізняємо кут), розширено crossover ──
    if (has_word("жим", "віджим", "відмив", "пек-дек", "розводк", "зведенн", "пуловер", "перехрещенн", "crossover") and has_muscle("груди")):
        if has_word("вниз голов", "нижні груди", "decline"):
            return "decline_press"
        if has_word("похил", "верхні груди", "incline", "підвищенням ніг"):
            return "incline_press"
        if has_word("розводк", "зведенн", "пек-дек", "кросовер", "метелик", "перехрещенн", "crossover"):
            return "chest_fly"
        if has_word("пуловер"):
            return "pullover"
        return "horizontal_press"

    # ── Плечі — вертикальний жим (розширено: "дельти" загалом, не тільки передні/середні) ──
    if has_word("жим", "стійка на руках") and (has_muscle("передні дельти", "середні дельти", "плечі", "дельти")):
        return "vertical_press"

    # ── Тяга до підборіддя (upright row) ──
    if has_word("до підборіддя"):
        return "upright_row"

    # ── Дельти — підйоми/розведення (ізоляція), розширено ──
    if has_muscle("середні дельти") and has_word("підйом", "розведенн", "протяжка", "halo"):
        return "lateral_raise"
    if has_muscle("задні дельти") and has_word("розведенн", "зведенн", "пек-дек", "face pull",
                                                 "тяга до обличчя", "підйом", "розтягування"):
        return "rear_delt_fly"
    if has_muscle("передні дельти") and has_word("підйом"):
        return "front_raise"

    # ── Спина — вертикальні тяги ──
    if has_word("підтягування", "тяга верхнього блоку", "тяга блоку", "lat pulldown"):
        return "vertical_pull"

    # ── Спина — горизонтальні тяги ──
    if has_word("тяга") and has_muscle("широчайні", "спина") and not has_word("верхнього блоку", "підтягування"):
        return "horizontal_pull"
    if has_word("row", "рядок") and has_muscle("широчайні", "спина"):
        return "horizontal_pull"

    if has_word("пуловер", "тяга прямими руками") and has_muscle("широчайні"):
        return "lat_pullover"

    if has_word("шраги") or (has_muscle("трапеція") and has_word("фермерська")):
        return "shrug"

    if has_muscle("біцепс") and not has_muscle("біцепс стегна") and has_word("підйом", "згинання", "молотк", "curl"):
        return "bicep_curl_isolated" if has_word("скотта", "концентрован") else "bicep_curl"

    if has_muscle("трицепс") and has_word("розгинання", "французьк", "кікбек", "extension"):
        return "tricep_extension"
    if has_muscle("трицепс") and has_word("відмив", "жим вузьким", "алмазн", "dip"):
        return "tricep_dip"

    # ── Прес / кор — розширено "нахили" + "косі" ──
    if has_muscle("прес", "нижній прес", "кор", "косі") or has_word("скручування", "планка", "ножиці",
                                                              "велосипед", "v-підйом", "dead bug",
                                                              "hollow", "підйом ніг", "нахили"):
        if has_word("ротація", "поворот", "косі", "russian", "нахили"):
            return "core_rotation"
        if has_word("планка") and not has_word("з підйомом"):
            return "core_stability"
        return "core_flexion"

    if has_word("ротація", "поворот тулуба"):
        return "rotation"

    if has_word("прогулянка", "carry", "тяга саней", "штовхання саней", "man maker", "комплексна вправа"):
        return "carry"

    if has_muscle("шия", "м'язи шиї"):
        return "neck"

    if has_muscle("передпліччя", "хват", "зап'яст") and not has_muscle("біцепс"):
        return "forearm"

    if ex.get("type") == "кардіо":
        return "conditioning"
    if ex.get("type") == "розтяжка":
        return "mobility"

    return None


def main():
    matched = {}
    unmatched = []

    for ex in exercises:
        pattern = classify_pattern(ex)
        if pattern:
            matched[ex["name"]] = pattern
        else:
            unmatched.append(ex["name"])

    print(f"Всього вправ: {len(exercises)}")
    print(f"Автоматично визначено патерн: {len(matched)} ({len(matched)*100//len(exercises)}%)")
    print(f"НЕ визначено (потребує ручного тегування): {len(unmatched)}\n")

    # Статистика по патернах
    from collections import Counter
    counts = Counter(matched.values())
    print("── Розподіл по патернах ──")
    for pattern, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {pattern:<25} {cnt}")

    # Записуємо результат у файл, готовий для вставки в generator.py
    with open("auto_pattern_map_output.py", "w", encoding="utf-8") as f:
        f.write("# Згенеровано автоматично — auto_tag_patterns.py\n")
        f.write("# Об'єднай з ручним PATTERN_MAP: PATTERN_MAP.get(name) or AUTO_PATTERN_MAP.get(name)\n\n")
        f.write("AUTO_PATTERN_MAP = {\n")
        for name, pattern in sorted(matched.items()):
            f.write(f"    {name!r}: {pattern!r},\n")
        f.write("}\n")

    with open("unmatched_exercises.txt", "w", encoding="utf-8") as f:
        f.write("Вправи без автоматично визначеного патерну — протегуй вручну:\n\n")
        for name in sorted(unmatched):
            f.write(f"{name}\n")

    print(f"\n✅ Записано: auto_pattern_map_output.py ({len(matched)} вправ)")
    print(f"✅ Записано: unmatched_exercises.txt ({len(unmatched)} вправ для ручної роботи)")


if __name__ == "__main__":
    main()