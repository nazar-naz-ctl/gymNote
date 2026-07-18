import backend.generator
from exercises_db import exercises

# Знайди кілька відомих вправ і подивись на нові поля
names_to_check = ["Станова тяга класична", "Жим над головою стоячи", "Підйом штанги на біцепс стоячи"]

for ex in exercises:
    if ex["name"] in names_to_check:
        print(f"{ex['name']:<40} fatigue={ex.get('fatigue')} cns_cost={ex.get('cns_cost')} "
              f"local={ex.get('local_fatigue')} systemic={ex.get('systemic_fatigue')} joint={ex.get('joint_fatigue')}")