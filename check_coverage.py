from backend.generator import generate_optimized_program

program, report = generate_optimized_program(
    'зал', ['штанга', 'гантелі', 'тренажер', 'блок'], 'маса', 3, 5
)

print("Оцінка:", report['score'])
print("\nMuscle Coverage:")
for group, data in report['muscle_coverage'].items():
    status = "✅" if data['score'] >= 0.5 else "⚠️"
    print(f"  {status} {group}: {int(data['score']*100)}% | покрито: {data['covered']} | бракує: {data['missing']}")

print("\nПроблеми:")
for issue in report['issues']:
    print(" -", issue)