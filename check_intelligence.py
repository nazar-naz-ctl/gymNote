from backend.generator import generate_optimized_program

program, report = generate_optimized_program(
    'зал', ['штанга', 'гантелі', 'тренажер', 'блок'], 'маса', 3, 5
)

print("Штрафна оцінка (score):", report['score'])
print("Intelligence Score:", report['intelligence_score'])
print("\nРозбивка:")
for k, v in report['intelligence_breakdown'].items():
    print(f"  {k}: {v}")