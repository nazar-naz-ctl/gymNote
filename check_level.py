from backend.generator import generate_focus_workout, format_focus_workout

print("=== НОВАЧОК (рівень 1) ===")
day = generate_focus_workout(['квадрицепс'], ['штанга', 'гантелі', 'тренажер'], level=1, hardcore=3, goal='маса')
print(format_focus_workout(day, ['квадрицепс'], 3, ['штанга', 'гантелі', 'тренажер']))

print("\n=== ПРОФІ (рівень 4) ===")
day = generate_focus_workout(['квадрицепс'], ['штанга', 'гантелі', 'тренажер'], level=4, hardcore=3, goal='маса')
print(format_focus_workout(day, ['квадрицепс'], 3, ['штанга', 'гантелі', 'тренажер']))