from backend.generator import generate_optimized_program

program, report = generate_optimized_program(
    'зал', ['штанга', 'гантелі', 'тренажер', 'блок'], 'маса', 3, 4,
    priority_muscle='груди', priority_pattern='incline_press'
)

print('Оцінка:', report['score'])
for day_num, day in program.items():
    print(f"\nДень {day_num}: {day['name']}")
    for ex in day['exercises']:
        marker = ' 🎯 PRIMARY' if ex.get('is_primary') else ''
        print(f"  {ex['name']:<40} pattern={ex.get('movement_pattern')}{marker}")