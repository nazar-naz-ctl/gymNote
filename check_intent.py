from backend.generator import generate_program

program = generate_program('зал', ['штанга', 'гантелі', 'тренажер'], 'маса', 3, 1)

for day_num, day in program.items():
    print(f"День {day_num}: {day['name']}")
    for ex in day['exercises']:
        primary_marker = " 🎯" if ex.get('is_primary') else ""
        print(f"  {ex['name']:<40} {ex['sets']}×{ex['reps']:<8} intent={ex.get('intent')}{primary_marker}")