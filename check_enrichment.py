import backend.generator  # тригерить збагачення бази
from exercises_db import exercises

ex = exercises[0]
print(ex['name'])
print('pattern:', ex.get('movement_pattern'))
print('fatigue:', ex.get('fatigue'))
print('compound:', ex.get('compound'))
print('unilateral:', ex.get('unilateral'))
print('spine_load:', ex.get('spine_load'))
print('stability:', ex.get('stability'))
print('skill:', ex.get('skill'))
print('stimulus:', ex.get('stimulus'))