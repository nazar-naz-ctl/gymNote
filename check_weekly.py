from backend.generator import generate_optimized_program

program, report = generate_optimized_program(
    'зал', ['штанга', 'гантелі', 'тренажер', 'блок'], 'маса', 3, 5
)

print("Weekly Balance Score:", report['weekly_balance_score'])
print("\nVolume Balance:")
for group, data in report['volume_balance'].items():
    print(f"  {group}: {data['sets']} сетів (MEV={data['mev']}, MAV={data['mav']}, MRV={data['mrv']}) -> {data['status']}, score={data['score']}")

print("\nFatigue Distribution:")
print("  daily_load:", report['fatigue_distribution']['daily_load'])
print("  score:", report['fatigue_distribution']['score'])
print("  overloaded_pairs:", report['fatigue_distribution']['overloaded_pairs'])