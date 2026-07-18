from backend.generator import generate_optimized_program

program, report = generate_optimized_program(
    'зал', ['штанга', 'гантелі', 'тренажер', 'блок'], 'маса', 3, 5
)

print("Оцінка:", report['score'])
print("Diversity за днями:", report['diversity_by_day'])
print("Joint totals (навантаження на суглоби за тиждень):", report['joint_totals'])
print("Compound ratio:", report['compound_ratio'])
print("\nПроблеми:")
for issue in report['issues']:
    print(" -", issue)