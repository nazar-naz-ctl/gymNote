"""
Exercise Database 2.0 + 2.1
════════════════════════════
Збагачує кожен запис вправи (з exercises_db.py) дев'ятьма новими
полями метаданих, похідними від уже наявних даних (руховий патерн,
складність, обладнання, ціль):

    movement_pattern — руховий патерн
    fatigue          — Fatigue Score 1-5
    compound         — чи багатосуглобовий рух (True/False)
    unilateral       — чи однобічна вправа (True/False)
    spine_load       — навантаження на хребет, 1-5
    stability        — вимога до стабілізації/балансу, 1-5
    skill            — технічна складність виконання, 1-5
    stimulus         — числова шкала 1-10 (1-3 витривалість,
                       4-6 гіпертрофія, 7-8 сила, 9-10 потужність)
    recovery_days    — скільки днів відновлюється м'яз після цієї
                       вправи (похідне від fatigue)

АРХІТЕКТУРА (після прибирання дублювання словників):
Ручний PATTERN_MAP/AUTO_PATTERN_MAP і FATIGUE_BY_PATTERN нижче —
це "насіннєві" дані. Вони потрібні РІВНО ОДИН РАЗ: щоб уперше
заповнити movement_pattern/fatigue на кожній вправі при старті
бота (курка-яйце — без них нема чим заповнити базу вперше).

Після цього моменту ВЕСЬ ІНШИЙ код генератора (find_exercises,
Compatibility Engine, Weekly Fatigue Manager) читає patterns/fatigue
НАПРЯМУ З ОБ'ЄКТА вправи (ex.get("movement_pattern"),
ex.get("spine_load")) — а не через повторний пошук за іменем у цих
словниках. Це і є "база вправ як єдине джерело істини" з roadmap.

Публічні get_pattern(name)/get_fatigue_score(name) (в
exercise_selector.py/recovery.py) лишились як тонкі "по імені"
обгортки на випадок, коли під рукою немає самого об'єкта вправи —
але вони більше не тримають власних копій словників, а шукають
по вже збагаченій базі.
"""

# ══════════════════════════════════════════════════════
# НАСІННЄВІ ДАНІ (використовуються лише для первинного заповнення)
# ══════════════════════════════════════════════════════

# покриває решту бази (592/593 вправ).

PATTERN_MAP = {
    # Груди
    "Жим штанги лежачи": "horizontal_press",
    "Похилий жим штанги": "incline_press",
    "Жим гантелей лежачи": "horizontal_press",
    "Похилий жим гантелей": "incline_press",
    "Жим штанги вниз головою": "decline_press",
    "Жим гантелей вниз головою": "decline_press",
    "Віджимання класичні": "horizontal_press",
    "Віджимання з підвищенням ніг": "incline_press",
    "Відмивання на брусах з нахилом вперед": "decline_press",
    "Відмивання на брусах": "decline_press",
    "TRX Віджимання": "horizontal_press",
    "Жим гирі лежачи": "horizontal_press",

    # Спина ширина (вертикальні тяги)
    "Підтягування широким хватом": "vertical_pull",
    "Підтягування зворотним хватом": "vertical_pull",
    "Підтягування вузьким хватом": "vertical_pull",
    "Тяга верхнього блоку широким хватом": "vertical_pull",
    "Тяга верхнього блоку вузьким хватом": "vertical_pull",
    "Тяга верхнього блоку зворотним хватом": "vertical_pull",
    "Австралійські підтягування": "horizontal_pull",
    "Тяга на петлях TRX (TRX Row)": "horizontal_pull",
    "Підтягування з вагою": "vertical_pull",
    "Вихід силою на турніку (Мускул-ап)": "vertical_pull_explosive",

    # Спина товщина (горизонтальні тяги + станова)
    "Станова тяга класична": "hip_hinge_deadlift",
    "Станова тяга сумо": "hip_hinge_deadlift",
    "Тяга штанги в нахилі прямим хватом": "horizontal_pull",
    "Тяга штанги в нахилі зворотним хватом": "horizontal_pull",
    "Тяга Т-грифа": "horizontal_pull",
    "Тяга гантелі однією рукою": "horizontal_pull",
    "Тяга нижнього блоку сидячи вузьким хватом": "horizontal_pull",
    "Тяга нижнього блоку широким хватом": "horizontal_pull",
    "Гарне ранок зі штангою": "hip_hinge",
    "Румунська тяга зі штангою": "hip_hinge",
    "Тяга гирі до поясу": "horizontal_pull",

    # Квадрицепс
    "Присідання зі штангою на спині": "squat_bilateral",
    "Фронтальні присідання": "squat_bilateral",
    "Присідання у Смітті": "squat_bilateral",
    "Жим ногами": "squat_machine",
    "Гак-машина присідання": "squat_machine",
    "Присідання з гантелями": "squat_bilateral",
    "Гоблет-присідання з гантеллю": "squat_bilateral",
    "Присідання з власною вагою": "squat_bilateral",
    "Присідання пістолетик": "squat_unilateral",
    "Гоблет-присідання з гирею": "squat_bilateral",
    "Стрибки в присіді": "squat_explosive",

    # Біцепс стегна
    "Румунська тяга з гантелями": "hip_hinge",
    "Мертва тяга на прямих ногах зі штангою": "hip_hinge",
    "Згинання ніг лежачи": "leg_curl",
    "Згинання ніг стоячи": "leg_curl",

    # Сідниці
    "Ягідний місток зі штангою": "hip_thrust",
    "Ягідний місток з гантеллю": "hip_thrust",
    "Міст на плечах": "hip_thrust",
    "Болгарські випади зі штангою": "lunge_unilateral",
    "Болгарські випади з гантелями": "lunge_unilateral",
    "Болгарські випади": "lunge_unilateral",
    "Випади зі штангою": "lunge_unilateral",
    "Випади з гантелями": "lunge_unilateral",
    "Міст з резинкою на стегнах": "hip_thrust",
    "Міст на одній нозі": "hip_thrust_unilateral",

    # Плечі (вертикальний жим)
    "Армійський жим стоячи": "vertical_press",
    "Армійський жим сидячи": "vertical_press",
    "Жим гантелей сидячи": "vertical_press",
    "Жим гантелей стоячи": "vertical_press",
    "Жим Арнольда": "vertical_press",
    "Жим за голову": "vertical_press",
    "Стійка на руках біля стіни": "vertical_press_bodyweight",
    "Віджимання в упорі стоячи": "vertical_press_bodyweight",
    "TRX Жим плечей": "vertical_press",
    "Жим двох гирей стоячи": "vertical_press",

    # Біцепс
    "Підйом штанги на біцепс стоячи": "bicep_curl",
    "Підйом EZ-штанги на біцепс": "bicep_curl",
    "Підйом гантелей на біцепс стоячи": "bicep_curl",
    "Підйом штанги на лаві Скотта": "bicep_curl_isolated",
    "TRX Підйом на біцепс": "bicep_curl",

    # Трицепс
    "Жим штанги вузьким хватом": "horizontal_press",
    "Французький жим лежачи зі штангою": "tricep_extension",
    "Французький жим з гантеллю лежачи": "tricep_extension",
    "Відмивання від лавки або стільця": "tricep_dip",
    "TRX Розгинання трицепса": "tricep_extension",
    "Алмазні віджимання": "horizontal_press",
}


# Згенеровано автоматично — auto_tag_patterns.py
# Об'єднується з PATTERN_MAP через get_pattern() нижче.
AUTO_PATTERN_MAP = {
    'TRX Болгарські випади': 'lunge_unilateral',
    'TRX Випади': 'lunge_unilateral',
    'TRX Віджимання': 'horizontal_press',
    'TRX Гірський альпініст': 'core_flexion',
    'TRX Жим від грудей стоячи': 'horizontal_press',
    'TRX Жим плечей': 'vertical_press',
    'TRX Зворотнє розведення': 'rear_delt_fly',
    'TRX Міст': 'hip_thrust',
    'TRX Планка': 'core_stability',
    'TRX Похилі віджимання': 'incline_press',
    'TRX Присідання': 'squat_bilateral',
    'TRX Присідання на одній нозі': 'squat_unilateral',
    'TRX Підйом на біцепс': 'bicep_curl',
    'TRX Підтягування': 'vertical_pull',
    'TRX Розгинання трицепса': 'tricep_extension',
    'TRX Ротація тулуба': 'core_rotation',
    'V-підйом': 'core_flexion',
    'Y-розведення з гантелями': 'rear_delt_fly',
    'Ізометричний опір шиї вперед': 'neck',
    'Ізометричний опір шиї назад': 'neck',
    'Інтервальне тренування щохвилини (EMOM)': 'conditioning',
    'Інтервальний біг': 'conditioning',
    'Їзда на велосипеді': 'core_flexion',
    'Австралійські підтягування': 'vertical_pull',
    'Аквааеробіка': 'conditioning',
    'Активація сідниць лежачи': 'hip_thrust',
    'Алмазні віджимання': 'horizontal_press',
    'Апперкоти по мішку': 'core_flexion',
    'Армійський жим зі штовханням': 'vertical_press',
    'Армійський жим сидячи': 'vertical_press',
    'Армійський жим стоячи': 'vertical_press',
    'Батерфляй (плавання)': 'core_flexion',
    'Батут (стрибки)': 'core_flexion',
    'Берпі': 'conditioning',
    'Берпі з підтягуванням': 'vertical_pull',
    'Берпі з підтягуванням та вибухом': 'vertical_pull',
    'Бойові мотузки (Battle ropes)': 'core_flexion',
    'Боковий кидок медбола': 'core_flexion',
    'Бокові перекати з грифом': 'core_flexion',
    'Болгарські випади': 'lunge_unilateral',
    'Болгарські випади з гантелями': 'lunge_unilateral',
    'Болгарські випади зі штангою': 'lunge_unilateral',
    'Брас (плавання)': 'core_flexion',
    'Бігова доріжка': 'conditioning',
    'Бігова розминка на місці': 'conditioning',
    'Бічна планка': 'core_stability',
    'Бічна планка з підйомом ноги': 'core_flexion',
    'Бічна планка на фітболі': 'core_stability',
    'Бічна розтяжка стоячи': 'core_flexion',
    'Бічні випади': 'lunge_unilateral',
    'Вакуум живота': 'core_flexion',
    'Ведмежа прогулянка': 'core_flexion',
    'Велосипед': 'core_flexion',
    'Велотренажер': 'conditioning',
    'Велотренажер інтервалами': 'conditioning',
    'Верблюд (Camel pose)': 'mobility',
    'Вибухові віджимання': 'horizontal_press',
    'Випади з гантелями': 'lunge_unilateral',
    'Випади з гирею над головою': 'lunge_unilateral',
    'Випади зі штангою': 'lunge_unilateral',
    'Випади крокові': 'lunge_unilateral',
    'Випади на місці': 'lunge_unilateral',
    'Випади назад з гантелями на місці': 'lunge_unilateral',
    'Вис в упорі (L-вис підготовка)': 'core_flexion',
    'Вис на одній руці (підготовка)': 'forearm',
    'Вис на турніку': 'forearm',
    'Високе піднімання колін': 'core_flexion',
    'Вихід силою на кільцях (Мускул-ап)': 'vertical_pull_explosive',
    'Вихід силою на турнику (Muscle-up transition)': 'vertical_pull_explosive',
    'Вихід силою на турніку (Мускул-ап)': 'vertical_pull_explosive',
    'Внутрішня ротація плеча з резинкою': 'rotation',
    'Воїн 1 (Warrior I)': 'core_flexion',
    'Воїн 2 (Warrior II)': 'core_flexion',
    'Воїн 3 (Warrior III)': 'core_flexion',
    'Вправи з булавами (Indian clubs)': 'core_flexion',
    'Вправи з гімнастичною палицею': 'core_flexion',
    'Вухо-вухо (бокс в парі)': 'core_flexion',
    'Відведення ноги з резинкою стоячи': 'hip_abduction',
    'Відведення ноги назад з резинкою': 'hip_abduction',
    'Відведення ноги назад у тренажері': 'hip_abduction',
    'Відведення ноги у тренажері': 'hip_abduction',
    'Віджимання в упорі стоячи': 'vertical_press',
    'Віджимання вузьким хватом': 'horizontal_press',
    'Віджимання від дивана на трицепс': 'horizontal_press',
    'Віджимання з оплеском': 'horizontal_press',
    'Віджимання з підвищенням ніг': 'incline_press',
    'Віджимання з підвищенням рук': 'horizontal_press',
    'Віджимання з резинкою на спині': 'horizontal_press',
    'Віджимання класичні': 'horizontal_press',
    'Віджимання на брусах з піднятими ногами': 'horizontal_press',
    'Віджимання на кулаках': 'horizontal_press',
    "Віджимання на кулаках з підтримкою зап'ястя": 'horizontal_press',
    'Віджимання на кільцях в упорі': 'horizontal_press',
    'Віджимання на нестабільній платформі (BOSU)': 'horizontal_press',
    'Віджимання на паралетах': 'horizontal_press',
    'Віджимання широким хватом': 'horizontal_press',
    'Відмивання від лавки або стільця': 'horizontal_press',
    'Відмивання на брусах': 'horizontal_press',
    'Відмивання на брусах з вагою': 'horizontal_press',
    'Відмивання на брусах з джгутом (полегшені)': 'horizontal_press',
    'Відмивання на брусах з нахилом вперед': 'horizontal_press',
    'Відмивання на кільцях': 'horizontal_press',
    'Гарне ранок зі штангою': 'hip_hinge',
    'Глибокий випад з поворотом': 'lunge_unilateral',
    'Голуб (Pigeon pose повний)': 'mobility',
    'Голубець (pigeon pose)': 'mobility',
    'Горизонтальна тяга в тренажері': 'horizontal_pull',
    'Горизонтальний вис — підготовка до планша (Planche)': 'core_flexion',
    'Гребля на тренажері інтервалами': 'core_flexion',
    'Гребний тренажер': 'core_flexion',
    'Гіперекстензія': 'hip_hinge',
    'Гіперекстензія в неповну амплітуду': 'hip_hinge',
    'Гірський альпініст': 'core_flexion',
    'Гірський альпініст хрест': 'core_flexion',
    'Дерево (Tree pose)': 'core_flexion',
    'Джеб-крос комбінація': 'core_flexion',
    'Динамічне розкриття грудного відділу': 'mobility',
    'Динамічні випади в русі (розминка)': 'lunge_unilateral',
    'Дихальні скручування (діафрагмальні)': 'core_flexion',
    'Дракон флаг (підготовка)': 'core_flexion',
    'Дракон флаг з зігнутими колінами (легка версія)': 'core_flexion',
    'Еліпсоїд': 'conditioning',
    'Жим Арнольда': 'vertical_press',
    'Жим від грудей без закидання голови': 'horizontal_press',
    'Жим від грудей в тренажері (низький кут)': 'horizontal_press',
    'Жим від грудей сидячи в тренажері': 'horizontal_press',
    'Жим гантелей вниз головою': 'decline_press',
    'Жим гантелей лежачи': 'horizontal_press',
    'Жим гантелей на похилій лаві вниз головою': 'decline_press',
    'Жим гантелей сидячи': 'vertical_press',
    'Жим гантелей сидячи під кутом': 'vertical_press',
    'Жим гантелей стоячи': 'vertical_press',
    'Жим гантелей стоячи на одній нозі': 'vertical_press',
    'Жим гантелей у нейтральному хваті лежачи': 'horizontal_press',
    'Жим гирі з коліна (Windmill)': 'vertical_press',
    'Жим гирі лежачи': 'horizontal_press',
    'Жим гирі однією рукою стоячи': 'vertical_press',
    'Жим двох гирей стоячи': 'vertical_press',
    'Жим з резинкою лежачи': 'horizontal_press',
    'Жим за голову': 'vertical_press',
    'Жим лежачи з важким джгутом': 'horizontal_press',
    'Жим лежачи з ланцюгами': 'horizontal_press',
    'Жим лежачи з паузою': 'horizontal_press',
    'Жим медбола лежачи': 'horizontal_press',
    'Жим ногами': 'squat_machine',
    'Жим ногами в неповну амплітуду': 'squat_machine',
    'Жим ногами вузькою постановкою': 'squat_machine',
    'Жим ногами однією ногою': 'squat_machine',
    'Жим ногами під кутом 45': 'squat_machine',
    'Жим ногами широкою постановкою': 'squat_machine',
    'Жим плечей у тренажері': 'vertical_press',
    'Жим пляшками з водою лежачи': 'horizontal_press',
    'Жим резинки стоячи': 'vertical_press',
    'Жим рюкзака лежачи': 'horizontal_press',
    'Жим у тренажері Сміта (груди)': 'horizontal_press',
    'Жим у тренажері Сміта (плечі)': 'vertical_press',
    'Жим штанги вниз головою': 'decline_press',
    'Жим штанги вузьким хватом': 'horizontal_press',
    'Жим штанги з паузою на стійках (Pin Press)': 'horizontal_press',
    'Жим штанги лежачи': 'horizontal_press',
    'Жим штовхаючи вгору з присіду (Squat Push Press)': 'squat_bilateral',
    'Жим із зігнутим тілом на брусах (Pike Press)': 'vertical_press',
    'Забіг по сходах': 'conditioning',
    'Закочування фітболу': 'core_flexion',
    'Закручування штанги на передпліччя': 'forearm',
    'Заминка — глибоке дихання лежачи': 'mobility',
    'Захльости гомілкою назад': 'conditioning',
    'Зашагування на лаву з гантелями': 'lunge_unilateral',
    'Зашагування на лаву зі штангою': 'lunge_unilateral',
    'Зашагування на степ з гирею': 'lunge_unilateral',
    'Зашагування на стілець': 'lunge_unilateral',
    'Зведення в кросовері верхній блок': 'chest_fly',
    'Зведення в кросовері нижній блок': 'chest_fly',
    'Зведення ніг з резинкою лежачи': 'hip_adduction',
    'Зведення ніг у тренажері': 'hip_adduction',
    'Зведення рук лежачи на підлозі (без лави)': 'chest_fly',
    'Зворотна гіперекстензія': 'hip_hinge',
    'Зворотна гіперекстензія лежачи': 'hip_hinge',
    'Зворотне розведення з резинкою': 'rear_delt_fly',
    'Зворотні випади з власною вагою': 'lunge_unilateral',
    'Зворотні випади з гантелями': 'lunge_unilateral',
    'Зворотні випади зі штангою': 'lunge_unilateral',
    'Зворотні зведення на блоці': 'rear_delt_fly',
    "Зворотні згинання зап'ясть": 'forearm',
    'Зворотні скручування': 'core_flexion',
    'Зворотні скручування з підйомом таза': 'core_flexion',
    'Зворотній випад з підйомом руки': 'lunge_unilateral',
    'Зворотній пек-дек': 'rear_delt_fly',
    "Згинання зап'ясть з гантелями": 'forearm',
    "Згинання зап'ясть зі штангою": 'forearm',
    'Згинання ніг лежачи': 'leg_curl',
    'Згинання ніг стоячи': 'leg_curl',
    'Згинання ніг у тренажері сидячи (памп)': 'leg_curl',
    'Згинання однієї ноги лежачи': 'leg_curl',
    'Згинання рук на біцепс на похилій лаві': 'bicep_curl',
    'Згинання шиї вперед з опором': 'neck',
    'Зміна рук з гирею у висі': 'core_flexion',
    'Зовнішня ротація плеча з резинкою': 'rotation',
    'Кабельні перехрещення (crossover)': 'chest_fly',
    'Кидок медбола над головою': 'core_flexion',
    'Кидок медбола об стіну': 'core_flexion',
    "Кидок набивного м'яча об підлогу": 'core_flexion',
    'Кистьовий еспандер': 'forearm',
    'Кистьовий ролик (Wrist Roller)': 'forearm',
    'Кобра': 'core_flexion',
    'Колесо для преса': 'core_flexion',
    'Колесо для преса з колін': 'core_flexion',
    'Колесо для преса стоячи': 'core_flexion',
    'Комплекс присід-віджимання-стрибок (Burpee Box)': 'squat_bilateral',
    'Комплексна вправа з гантелями (Man Maker)': 'carry',
    "Комплексна розтяжка всього тіла (World's Greatest Stretch)": 'mobility',
    'Концентровані підйоми': 'bicep_curl_isolated',
    'Кроки з обтяженням (weighted walking)': 'core_flexion',
    'Кроки крабом з резинкою': 'hip_abduction',
    'Крокуючі випади з гантелями': 'lunge_unilateral',
    'Кроль (плавання)': 'core_flexion',
    'Кругові махи гирею': 'hip_hinge',
    'Кругові оберти плечима': 'mobility',
    'Кругові оберти тазом': 'core_flexion',
    'Кут (Angle pose)': 'core_flexion',
    'Кут у висі': 'core_flexion',
    'Кікбек з гантеллю': 'tricep_extension',
    'Лебідь на підлозі (Swan)': 'mobility',
    'Легкий біг підтюпцем': 'conditioning',
    'Лучник (Archer pull-up)': 'vertical_pull_explosive',
    'Максимум кіл за відведений час (AMRAP)': 'conditioning',
    'Махи гирею двома руками (Swing)': 'hip_hinge',
    'Махи гирею однією рукою': 'hip_hinge',
    'Мертва тяга з гантелями': 'hip_hinge_deadlift',
    'Мертва тяга з гирею': 'hip_hinge_deadlift',
    'Мертва тяга на прямих ногах зі штангою': 'hip_hinge_deadlift',
    'Мертвий жук — почергові рухи рук і ніг лежачи (Dead Bug)': 'core_flexion',
    'Метелик (розтяжка паху)': 'mobility',
    'Мобілізація гомілковостопного суглоба': 'mobility',
    'Молотки з гантелями': 'bicep_curl',
    'Молотки з резинкою': 'bicep_curl',
    'Міст (Bridge pose)': 'hip_thrust',
    'Міст з резинкою на стегнах': 'hip_thrust',
    'Міст на одній нозі': 'hip_thrust_unilateral',
    'Міст на плечах': 'hip_thrust',
    'Місяць (Half Moon pose)': 'core_flexion',
    'Нахил в тазостегновому суглобі (Хіп-хінж)': 'mobility',
    'Нахил шиї в сторону з опором': 'neck',
    'Нахили з гантеллю в сторону': 'core_rotation',
    'Нахили зі штангою в сторони': 'core_rotation',
    "Нахили стоячи на косі м'язи": 'core_rotation',
    'Негативні відмивання на брусах': 'horizontal_press',
    'Негативні підтягування': 'vertical_pull',
    'Ножиці': 'core_flexion',
    'Ножиці пілатес': 'core_flexion',
    'Нордичне згинання гомілки': 'leg_curl',
    'Носки до перекладини (Toes to Bar)': 'core_flexion',
    'Обертання гирі навколо голови (Хало)': 'core_flexion',
    "Обертання зап'ястків": 'forearm',
    'Обертання шиї': 'neck',
    'Одна нога кола (Single leg circle)': 'core_flexion',
    'Одноруке віджимання': 'horizontal_press',
    'Пайк на підлозі': 'core_flexion',
    'Пек-дек (метелик)': 'chest_fly',
    'Перекати штанги по підлозі': 'core_flexion',
    'Перекочування на спині (Rolling like a ball)': 'core_flexion',
    'Плавання з дошкою (ноги)': 'conditioning',
    'Плавання на спині': 'conditioning',
    'Плавання на швидкість': 'conditioning',
    'Планка "супермен"': 'hip_hinge',
    'Планка з дотиком плеча': 'core_stability',
    'Планка з опорою на лаву (полегшена)': 'core_stability',
    'Планка з переступанням (Plank Jacks)': 'core_stability',
    'Планка з підйомом ноги': 'core_flexion',
    'Планка з підйомом ноги та руки (Bird-Dog)': 'core_flexion',
    'Планка з підйомом руки': 'core_flexion',
    'Планка з підйомом руки і ноги': 'core_flexion',
    'Планка на ліктях': 'core_stability',
    'Планка на нестабільній платформі (BOSU)': 'core_stability',
    'Планка на руках': 'core_stability',
    'Планка на фітболі': 'core_stability',
    'Планш на брусах (підготовка)': 'core_flexion',
    'Планш на кільцях (підготовка)': 'core_flexion',
    'Планш на паралетах (підготовка)': 'core_flexion',
    'Подвійні прокрути скакалки за стрибок (Double Under)': 'conditioning',
    'Подвійні стрибки зі скакалкою': 'conditioning',
    'Поза дитини': 'mobility',
    'Поза орла (Eagle Pose)': 'core_flexion',
    'Поза саранчі (Locust Pose)': 'mobility',
    'Похила розводка гантелей': 'incline_press',
    'Похилий жим гантелей': 'incline_press',
    'Похилий жим штанги': 'incline_press',
    'Поштовх гирі': 'olympic_press',
    'Поштовх двох гирей': 'olympic_press',
    'Поштовх штанги над головою (Поштовх)': 'olympic_press',
    'Привітання сонцю (Surya Namaskar)': 'mobility',
    'Присід гирі на плечі (Front Rack Squat)': 'squat_bilateral',
    'Присід з жимом гантелей (Squat to Press)': 'squat_bilateral',
    'Присід з жимом гантелей над головою (Трастер)': 'squat_bilateral',
    'Присід з жимом штанги над головою (Трастер)': 'squat_bilateral',
    'Присід зі стрибком (Squat Jump)': 'squat_explosive',
    'Присід у машині Сміта сумо': 'squat_bilateral',
    'Присідання в неповну амплітуду': 'squat_bilateral',
    'Присідання в тренажері Смітта вузько': 'squat_machine',
    'Присідання з важким джгутом': 'squat_bilateral',
    'Присідання з власною вагою': 'squat_bilateral',
    'Присідання з вузькою постановкою ніг': 'squat_bilateral',
    'Присідання з гантеллю перед грудьми (Гоблет-присідання)': 'squat_bilateral',
    'Присідання з гантелями': 'squat_bilateral',
    'Присідання з гирею над головою': 'squat_bilateral',
    'Присідання з гирею перед грудьми (Гоблет-присідання)': 'squat_bilateral',
    'Присідання з кидком медбола': 'squat_bilateral',
    'Присідання з ланцюгами': 'squat_bilateral',
    'Присідання з медболом над головою': 'squat_bilateral',
    'Присідання з паузою': 'squat_bilateral',
    'Присідання з поясом (Belt Squat)': 'squat_bilateral',
    'Присідання з поясом без навантаження на спину (Belt Squat)': 'squat_bilateral',
    'Присідання з резинкою': 'squat_bilateral',
    'Присідання з рюкзаком': 'squat_bilateral',
    'Присідання з стрибком і гантелями': 'squat_explosive',
    'Присідання зі стрибком і жимом гантелей': 'squat_explosive',
    'Присідання зі штангою на спині': 'squat_bilateral',
    'Присідання зі штангою над головою (Overhead Squat)': 'squat_bilateral',
    'Присідання на балансувальній дошці': 'squat_bilateral',
    'Присідання на нестабільній платформі (BOSU)': 'squat_bilateral',
    'Присідання на одній нозі з опорою (Skater Squat)': 'squat_unilateral',
    'Присідання на одній нозі на нестабільній платформі (BOSU)': 'squat_unilateral',
    'Присідання пістолетик': 'squat_unilateral',
    'Присідання сумо з власною вагою': 'squat_bilateral',
    'Присідання сумо з гантеллю': 'squat_bilateral',
    'Присідання сумо з гирею': 'squat_bilateral',
    'Присідання сумо з резинкою': 'squat_bilateral',
    'Присідання у Смітті': 'squat_bilateral',
    'Присідання у Смітті вузьким хватом': 'squat_bilateral',
    'Присідання у тренажері Гакк (Гак-машина)': 'squat_machine',
    'Присідання у тренажері Гакк (Гак-присідання)': 'squat_machine',
    'Прогин спини кішка-корова (Кіт-корова)': 'core_flexion',
    'Прогулянка на руках': 'core_flexion',
    'Пронація та супінація з гантеллю': 'forearm',
    'Проніс гирі між ніг назад (Hike Pass)': 'core_flexion',
    'Протяжка штанги широким хватом': 'lateral_raise',
    'Пуловер з гантеллю': 'pullover',
    'Пуловер зі штангою': 'pullover',
    'Пуловер на верхньому блоці': 'lat_pullover',
    'Пульсуючі присідання': 'squat_bilateral',
    'Підйом EZ-штанги зворотним хватом': 'bicep_curl',
    'Підйом EZ-штанги на біцепс': 'bicep_curl',
    'Підйом гантелей в сторони': 'lateral_raise',
    'Підйом гантелей в сторони в нахилі': 'rear_delt_fly',
    'Підйом гантелей в сторони до рівня плеча': 'lateral_raise',
    'Підйом гантелей в сторони сидячи': 'lateral_raise',
    'Підйом гантелей вперед': 'front_raise',
    'Підйом гантелей зворотним хватом': 'bicep_curl',
    'Підйом гантелей на біцепс стоячи': 'bicep_curl',
    'Підйом гантелей на лаві Скотта': 'bicep_curl_isolated',
    'Підйом гантелей почергово': 'bicep_curl',
    'Підйом гантелі в сторону лежачи на боці': 'lateral_raise',
    'Підйом гантелі лежачи на похилій лаві': 'bicep_curl',
    'Підйом каната': 'bicep_curl',
    'Підйом колін стоячи': 'core_flexion',
    'Підйом колін у висі': 'core_flexion',
    'Підйом литок у тренажері для преса': 'calf_raise',
    'Підйом на блоці в сторону однією рукою': 'lateral_raise',
    'Підйом на біцепс в кросовері': 'bicep_curl',
    'Підйом на біцепс в тренажері': 'bicep_curl',
    'Підйом на біцепс з гирею': 'bicep_curl',
    'Підйом на біцепс з резинкою': 'bicep_curl',
    'Підйом на біцепс мотузкою': 'bicep_curl',
    'Підйом на біцепс на нижньому блоці': 'bicep_curl',
    'Підйом на носки в тренажері жим ногами': 'squat_machine',
    'Підйом на носки з гантелями': 'calf_raise',
    'Підйом на носки з резинкою': 'calf_raise',
    'Підйом на носки зі штангою': 'calf_raise',
    'Підйом на носки зі штангою сидячи': 'calf_raise',
    'Підйом на носки на одній нозі': 'calf_raise',
    'Підйом на носки на одній нозі з гантеллю': 'calf_raise',
    'Підйом на носки сидячи з гантелями': 'calf_raise',
    'Підйом на носки сидячи у тренажері': 'calf_raise',
    'Підйом на носки стоячи': 'calf_raise',
    'Підйом на носки стоячи у тренажері': 'calf_raise',
    'Підйом ніг лежачи': 'core_flexion',
    'Підйом ніг на брусах': 'core_flexion',
    'Підйом ніг на похилій лаві': 'core_flexion',
    'Підйом ніг у висі з поворотом': 'core_rotation',
    'Підйом ніг у висі прямих': 'core_flexion',
    'Підйом ніг у тренажері': 'core_flexion',
    'Підйом резинки в сторони': 'lateral_raise',
    'Підйом резинки вперед': 'front_raise',
    'Підйом таза з гантеллю з опорою на лаву': 'hip_thrust',
    'Підйом таза лежачи з опорою на лаву (Hip Thrust)': 'hip_thrust',
    'Підйом штанги зворотним хватом': 'bicep_curl',
    'Підйом штанги на біцепс стоячи': 'bicep_curl',
    'Підйом штанги на лаві Скотта': 'bicep_curl_isolated',
    'Підтягування вузьким нейтральним хватом': 'vertical_pull',
    'Підтягування вузьким хватом': 'vertical_pull',
    'Підтягування до грудей': 'vertical_pull',
    'Підтягування з вагою': 'vertical_pull',
    'Підтягування з джгутом (полегшені)': 'vertical_pull',
    'Підтягування з затримкою вгорі': 'vertical_pull',
    'Підтягування зворотним хватом': 'vertical_pull',
    'Підтягування на кільцях': 'vertical_pull',
    'Підтягування нейтральним хватом': 'vertical_pull',
    'Підтягування хвилею': 'vertical_pull',
    'Підтягування широким хватом': 'vertical_pull',
    'Підтягування широким хватом до грудей (акцент на широчайші)': 'vertical_pull',
    'Ривкова тяга від стегна (Кліп)': 'olympic_pull',
    'Ривкова тяга зі штангою до плечей (Кліп)': 'olympic_pull',
    'Ривок гирі': 'olympic_pull',
    'Ривок штанги над головою (Снеч)': 'olympic_pull',
    'Розведення в сторони в тренажері (Lateral Raise Machine)': 'lateral_raise',
    'Розведення в сторони на блоці стоячи': 'lateral_raise',
    'Розведення гантелей в нахилі': 'rear_delt_fly',
    'Розведення гантелей на похилій лаві вниз головою': 'decline_press',
    'Розведення на задні дельти в кросовері': 'rear_delt_fly',
    'Розведення на задні дельти в тренажері': 'rear_delt_fly',
    'Розводка гантелей лежачи': 'chest_fly',
    'Розводка з резинкою': 'chest_fly',
    'Розводка на кільцях': 'chest_fly',
    'Розгинання гантелі з-за голови стоячи': 'tricep_extension',
    'Розгинання двох гантелей з-за голови': 'tricep_extension',
    "Розгинання зап'ясть з гантелями": 'forearm',
    "Розгинання зап'ясть зі штангою": 'forearm',
    'Розгинання на блоці зворотним хватом': 'tricep_extension',
    'Розгинання на блоці мотузкою': 'tricep_extension',
    'Розгинання на блоці прямою рукояткою': 'tricep_extension',
    'Розгинання ніг у неповну амплітуду': 'leg_curl',
    'Розгинання ніг у тренажері': 'leg_curl',
    'Розгинання рук в кросовері з мотузкою над головою': 'tricep_extension',
    'Розгинання рук у тренажері на трицепс': 'tricep_extension',
    'Розгинання спини на римському стільці': 'hip_hinge',
    'Розгинання спини на фітболі': 'hip_hinge',
    'Розгинання трицепса з гирею': 'tricep_extension',
    'Розгинання трицепса з резинкою над головою': 'tricep_extension',
    'Розгинання трицепса з резинкою стоячи': 'tricep_extension',
    'Розгинання шиї назад з опором': 'neck',
    'Розгойдування в позі складеного тіла (Hollow Rock)': 'core_flexion',
    'Розтягування резинки за спиною': 'rear_delt_fly',
    'Розтяжка IT-стрічки': 'mobility',
    'Розтяжка ахілового сухожилля': 'mobility',
    'Розтяжка біцепса стегна лежачи': 'mobility',
    'Розтяжка грудей біля стіни': 'mobility',
    'Розтяжка грудей у дверному проході': 'mobility',
    'Розтяжка грудної клітки на ролику': 'mobility',
    'Розтяжка задньої поверхні стегна стоячи': 'mobility',
    'Розтяжка квадрицепса стоячи': 'mobility',
    "Розтяжка косих м'язів стоячи": 'core_flexion',
    'Розтяжка литок стоячи': 'calf_raise',
    'Розтяжка передпліччя': 'forearm',
    'Розтяжка плеча поперек тіла': 'mobility',
    'Розтяжка спини сидячи (нахил вперед)': 'mobility',
    'Розтяжка стегна 90/90': 'mobility',
    'Розтяжка стегна лежачи на спині (коліно до грудей)': 'mobility',
    'Розтяжка сідниць лежачи': 'mobility',
    'Розтяжка трапеції нахилом голови': 'neck',
    'Розтяжка трицепса над головою': 'mobility',
    'Розтяжка широчайніх стоячи': 'mobility',
    'Розтяжка шиї бічна': 'neck',
    'Ролик для мобілізації хребта': 'core_flexion',
    'Ролик для спини (пінний)': 'mobility',
    'Російські скручування': 'core_flexion',
    'Ротаційна планка': 'core_stability',
    'Ротація з медболом стоячи': 'core_rotation',
    'Ротація плечей': 'rotation',
    'Ротація тулуба на блоці': 'core_rotation',
    'Румунська тяга в тренажері Сміта': 'hip_hinge',
    'Румунська тяга з гантелями': 'hip_hinge',
    'Румунська тяга з опорою на лаву однією ногою': 'hip_hinge',
    'Румунська тяга зі штангою': 'hip_hinge',
    'Румунська тяга на одній нозі з гантелею': 'hip_hinge',
    'Рядок на кільцях': 'horizontal_pull',
    'Скандинавська ходьба': 'conditioning',
    'Скапулярні підтягування': 'vertical_pull',
    'Складання тіла (Teaser)': 'core_flexion',
    'Складання тіла на петлях TRX (TRX Pike)': 'core_flexion',
    'Скручування': 'core_flexion',
    'Скручування з диском': 'core_flexion',
    'Скручування з медболом': 'core_flexion',
    'Скручування з поворотом': 'core_rotation',
    'Скручування з піднятими ногами': 'core_flexion',
    'Скручування з резинкою': 'core_flexion',
    "Скручування зап'ястя зі штангою": 'core_flexion',
    'Скручування лежачи (Supine twist)': 'core_flexion',
    "Скручування на м'ячі з опорою на ноги": 'core_flexion',
    'Скручування на похилій лаві': 'core_flexion',
    'Скручування на фітболі': 'core_flexion',
    'Скручування на фітболі з поворотом': 'core_rotation',
    'Скручування у тренажері': 'core_flexion',
    'Собака мордою вгору': 'mobility',
    'Собака мордою вниз': 'mobility',
    'Сотня (Pilates Hundred)': 'core_flexion',
    'Спринт 30м': 'conditioning',
    'Спринт в гору': 'conditioning',
    'Спринт на місці': 'conditioning',
    'Станова тяга з дефіцитом (стоячи на підвищенні)': 'hip_hinge_deadlift',
    'Станова тяга з паузою': 'hip_hinge_deadlift',
    'Станова тяга класична': 'hip_hinge_deadlift',
    'Станова тяга сумо': 'hip_hinge_deadlift',
    'Стояння на одній нозі': 'core_flexion',
    'Стояння на одній нозі на нестабільній платформі (BOSU)': 'core_flexion',
    'Стрибки Джека': 'conditioning',
    'Стрибки в глибину': 'conditioning',
    'Стрибки в присіді': 'squat_explosive',
    'Стрибки зі зміною ніг': 'conditioning',
    'Стрибки зі скакалкою': 'conditioning',
    'Стрибки на лавку': 'conditioning',
    'Стрибки на носках': 'calf_raise',
    'Стрибки на скакалці в повільному темпі': 'conditioning',
    'Стрибки на тумбу': 'conditioning',
    'Стрибки по сходах через одну': 'conditioning',
    'Стрибки через уявну лінію': 'core_flexion',
    'Стрибок у довжину з місця': 'conditioning',
    'Стійка на руках біля стіни': 'vertical_press',
    'Стійка на руках на кільцях': 'vertical_press',
    'Стійка на руках на паралетах': 'vertical_press',
    'Стілець (Chair pose)': 'core_flexion',
    'Стінне присідання': 'squat_bilateral',
    'Супермен': 'hip_hinge',
    'Супермен по черзі': 'hip_hinge',
    'Сходинковий тренажер (степер)': 'conditioning',
    'Трикутник (Triangle pose)': 'core_flexion',
    'Турецький підйом': 'core_flexion',
    'Тяга Т-грифа': 'horizontal_pull',
    'Тяга в стрибок': 'olympic_pull',
    'Тяга в тренажері сидячи широким хватом': 'horizontal_pull',
    'Тяга верхнього блоку вузьким хватом': 'vertical_pull',
    'Тяга верхнього блоку за голову': 'vertical_pull',
    'Тяга верхнього блоку зворотним хватом': 'vertical_pull',
    'Тяга верхнього блоку однією рукою': 'vertical_pull',
    'Тяга верхнього блоку однією рукою вузьким хватом': 'vertical_pull',
    'Тяга верхнього блоку широким хватом': 'vertical_pull',
    'Тяга гантелей до підборіддя': 'upright_row',
    'Тяга гантелей до підборіддя нахилившись': 'upright_row',
    'Тяга гантелі в нахилі з опорою на одну ногу (Single-leg Row)': 'horizontal_pull',
    'Тяга гантелі в упорі грудьми на похилу лаву': 'horizontal_pull',
    'Тяга гантелі в упорі на лаву': 'horizontal_pull',
    'Тяга гантелі однією рукою': 'horizontal_pull',
    'Тяга гирі в стилі сумо': 'horizontal_pull',
    'Тяга гирі до поясу': 'horizontal_pull',
    'Тяга двох гантелей в нахилі': 'horizontal_pull',
    'Тяга до обличчя на блоці (Face Pull)': 'rear_delt_fly',
    'Тяга до обличчя резинкою (Face Pull)': 'rear_delt_fly',
    'Тяга жгута стоячи в нахилі': 'horizontal_pull',
    'Тяга з паралельними рукоятками (нейтральний хват)': 'horizontal_pull',
    'Тяга на петлях TRX (TRX Row)': 'horizontal_pull',
    'Тяга на петлях TRX з поворотом (TRX Row)': 'horizontal_pull',
    'Тяга нижнього блоку сидячи вузьким хватом': 'horizontal_pull',
    'Тяга нижнього блоку сидячи з підтримкою спини': 'horizontal_pull',
    'Тяга нижнього блоку широким хватом': 'horizontal_pull',
    'Тяга однією рукою в тренажері': 'horizontal_pull',
    'Тяга однієї гантелі в упорі на коліно': 'horizontal_pull',
    'Тяга прямими руками на блоці (Straight-Arm Pulldown)': 'horizontal_pull',
    'Тяга резинки до поясу стоячи': 'horizontal_pull',
    'Тяга резинки до підборіддя': 'upright_row',
    'Тяга резинки з-за голови': 'horizontal_pull',
    'Тяга рушника до себе': 'horizontal_pull',
    'Тяга рюкзака в нахилі': 'horizontal_pull',
    'Тяга саней': 'horizontal_pull',
    'Тяга саней назад': 'carry',
    'Тяга сумо з підтягуванням до підборіддя (Sumo Deadlift High Pull)': 'upright_row',
    'Тяга у нахилі з двома пляшками води': 'horizontal_pull',
    'Тяга штанги в нахилі зворотним хватом': 'horizontal_pull',
    'Тяга штанги в нахилі прямим хватом': 'horizontal_pull',
    'Тяга штанги до підборіддя': 'upright_row',
    'Тіньовий бокс': 'core_flexion',
    'Удари по лапах': 'core_flexion',
    'Удари по мішку': 'core_flexion',
    'Утримання гантелі пальцями': 'forearm',
    'Утримання диска пальцями (Plate Pinch)': 'forearm',
    'Утримання ніг вперед на брусах (L-сит)': 'core_flexion',
    'Утримання ніг вперед на кільцях (L-сит)': 'core_flexion',
    'Утримання ніг вперед на паралетах (L-сит)': 'core_flexion',
    'Утримання ніг вперед на петлях TRX (L-сит)': 'core_flexion',
    'Утримання порожньої постави (Hollow Hold)': 'core_flexion',
    'Фермерська прогулянка з гантелями': 'shrug',
    'Фермерська прогулянка з гирями': 'shrug',
    'Фермерська прогулянка на пальцях': 'shrug',
    'Французький жим EZ-штангою': 'tricep_extension',
    'Французький жим з гантеллю лежачи': 'tricep_extension',
    'Французький жим лежачи зі штангою': 'tricep_extension',
    'Французький жим однією рукою': 'tricep_extension',
    'Французький жим сидячи зі штангою': 'tricep_extension',
    'Фронтальні присідання': 'squat_bilateral',
    'Хвилі важким канатом (Battle Ropes)': 'core_flexion',
    'Ходьба на носках': 'calf_raise',
    "Ходьба на п'ятках": 'calf_raise',
    'Ходьба у швидкому темпі (Power Walk)': 'conditioning',
    'Човник (Boat pose)': 'core_flexion',
    'Шраги в тренажері Сміта': 'shrug',
    'Шраги для трапеції та шиї': 'shrug',
    'Шраги з гантелями': 'shrug',
    'Шраги з гирею': 'shrug',
    'Шраги зі штангою': 'shrug',
    'Шраги на верхньому блоці': 'shrug',
    'Штовхання саней': 'carry',
    'Ягідний місток з гантеллю': 'hip_thrust',
    'Ягідний місток зі штангою': 'hip_thrust',
    'Ягідний місток у тренажері': 'hip_thrust',
}


def _seed_get_pattern(name: str) -> str | None:
    """Ручний PATTERN_MAP має пріоритет над автоматичним AUTO_PATTERN_MAP.
    Використовується ЛИШЕ для первинного заповнення бази — деінде в
    генераторі паттерн читається напряму з ex["movement_pattern"]."""
    return PATTERN_MAP.get(name) or AUTO_PATTERN_MAP.get(name)


FATIGUE_BY_PATTERN = {
    "hip_hinge_deadlift": 5,
    "squat_bilateral": 5,
    "olympic_pull": 5,
    "olympic_press": 5,
    "vertical_pull_explosive": 5,

    "squat_machine": 4,
    "squat_explosive": 4,
    "squat_unilateral": 4,
    "lunge_unilateral": 4,
    "horizontal_press": 4,
    "vertical_press": 4,
    "horizontal_pull": 4,
    "vertical_pull": 4,
    "hip_thrust": 4,
    "carry": 4,

    "incline_press": 3,
    "decline_press": 3,
    "hip_hinge": 3,
    "leg_curl": 3,
    "leg_extension": 3,
    "hip_thrust_unilateral": 3,
    "upright_row": 3,
    "shrug": 3,
    "chest_fly": 3,
    "pullover": 3,
    "lat_pullover": 3,
    "core_stability": 3,
    "conditioning": 3,

    "lateral_raise": 2,
    "front_raise": 2,
    "rear_delt_fly": 2,
    "bicep_curl": 2,
    "bicep_curl_isolated": 2,
    "tricep_extension": 2,
    "tricep_dip": 2,
    "core_flexion": 2,
    "core_rotation": 2,
    "hip_abduction": 2,
    "hip_adduction": 2,
    "rotation": 2,
    "forearm": 2,

    "calf_raise": 1,
    "neck": 1,
    "mobility": 1,
}

DEFAULT_FATIGUE = 3

AXIAL_PATTERNS = {
    "hip_hinge_deadlift",
    "squat_bilateral",
    "squat_machine",
    "olympic_pull",
    "olympic_press",
}



def _seed_get_fatigue(pattern: str) -> int:
    """Fatigue Score за патерном — так само лише для первинного
    заповнення бази."""
    return FATIGUE_BY_PATTERN.get(pattern, DEFAULT_FATIGUE)



COMPOUND_PATTERNS = {
    "hip_hinge_deadlift", "hip_hinge", "squat_bilateral", "squat_unilateral",
    "squat_machine", "squat_explosive", "lunge_unilateral",
    "horizontal_press", "incline_press", "decline_press", "vertical_press",
    "horizontal_pull", "vertical_pull", "vertical_pull_explosive",
    "hip_thrust", "hip_thrust_unilateral", "olympic_pull", "olympic_press", "carry",
}

SPINE_LOAD_BY_PATTERN = {
    # Максимальне — ті самі, що вже AXIAL_PATTERNS в recovery.py
    "hip_hinge_deadlift": 5, "squat_bilateral": 5, "squat_machine": 5,
    "olympic_pull": 5, "olympic_press": 5,
    # Високе
    "hip_hinge": 4, "squat_unilateral": 4, "squat_explosive": 4,
    "lunge_unilateral": 4, "carry": 4,
    # Середнє
    "horizontal_press": 3, "vertical_press": 3, "horizontal_pull": 3,
    "vertical_pull": 3, "hip_thrust": 3, "upright_row": 3,
    # Низьке
    "incline_press": 2, "decline_press": 2, "hip_thrust_unilateral": 2,
    "chest_fly": 2, "shrug": 2,
}
DEFAULT_SPINE_LOAD = 1

# Патерни, що вимагають вищої техніки незалежно від робочої ваги
HIGH_SKILL_PATTERNS = {"olympic_pull", "olympic_press", "vertical_pull_explosive"}

# Патерни вибухового/потужнісного характеру
POWER_PATTERNS = {"olympic_pull", "olympic_press", "squat_explosive", "vertical_pull_explosive"}

STABLE_EQUIPMENT = {"тренажер", "блок", "тренажер Сміта"}
UNSTABLE_EQUIPMENT = {"TRX", "кільця"}


def compute_compound(pattern: str) -> bool:
    return pattern in COMPOUND_PATTERNS


def compute_unilateral(pattern: str) -> bool:
    return bool(pattern) and "unilateral" in pattern


def compute_spine_load(pattern: str) -> int:
    return SPINE_LOAD_BY_PATTERN.get(pattern, DEFAULT_SPINE_LOAD)


def compute_stability(ex: dict, pattern: str) -> int:
    equipment = set(ex.get("equipment", []))
    is_uni = compute_unilateral(pattern)

    if is_uni:
        return 5
    if equipment & UNSTABLE_EQUIPMENT:
        return 4
    if equipment & STABLE_EQUIPMENT:
        return 1
    return 3


def compute_skill(ex: dict, pattern: str) -> int:
    base = ex.get("difficulty", 3)
    if pattern in HIGH_SKILL_PATTERNS:
        base += 1
    return max(1, min(5, base))


def compute_stimulus(ex: dict, pattern: str) -> int:
    """
    Database 2.1: числова шкала 1-10 замість категорії.
    1-3 — витривалість, 4-6 — гіпертрофія, 7-8 — сила, 9-10 — потужність.
    Континуум, а не жорсткі категорії — дозволяє Score Engine рахувати
    "наскільки близько" вправа до цілі, а не лише "збігається/ні".
    """
    if pattern in POWER_PATTERNS:
        return 10

    score = 5.0  # база — середина шкали (гіпертрофія)
    goal = ex.get("goal", [])

    if "сила" in goal:
        score += 2.0
    if "витривалість" in goal or "схуднення" in goal or ex.get("type") == "кардіо":
        score -= 2.0

    # Складніші/важчі вправи тяжіють до силового краю шкали
    score += (ex.get("difficulty", 3) - 3) * 0.5

    return max(1, min(10, round(score)))


def compute_recovery_days(fatigue: int) -> int:
    """Скільки днів потрібно м'язу на відновлення після цієї вправи —
    похідне від Fatigue Score (чим важча системно вправа, тим довше
    відновлення)."""
    if fatigue >= 5:
        return 3
    if fatigue >= 4:
        return 2
    return 1

# ══════════════════════════════════════════════════════
# CNS COST — окрема від Fatigue величина нервового навантаження
# ══════════════════════════════════════════════════════
# Fatigue Score змішує м'язову і нервову втому в одне число. Але
# важкий жим лежачи (Fatigue=4, м'язово важкий) насправді набагато
# менш нервово-виснажливий, ніж важке присідання чи станова тяга
# (теж може мати Fatigue=4-5) — тому CNS Cost рахується окремо.
#
# Найвище — важкі осьові/тазостегнові рухи (станова, присідання,
# олімпійські рухи), а не будь-яка "важка" вправа взагалі.
CNS_COST_BY_PATTERN = {
    # Максимальне — важка вага на багатосуглобові осьові рухи
    "hip_hinge_deadlift": 5,
    "squat_bilateral": 5,
    "olympic_pull": 5,
    "olympic_press": 5,

    # Високе — вибухові/асиметричні варіації тих самих рухів
    "squat_explosive": 4,
    "vertical_pull_explosive": 4,
    "squat_unilateral": 4,
    "lunge_unilateral": 4,
    "hip_hinge": 3,

    # Середнє — важкі, але не осьові багатосуглобові рухи
    "squat_machine": 3,
    "vertical_press": 3,
    "hip_thrust": 3,
    "carry": 3,

    # Низьке — верхньотілесні жими/тяги (м'язово важкі, нервово ні)
    "horizontal_press": 2,
    "incline_press": 2,
    "decline_press": 2,
    "horizontal_pull": 2,
    "vertical_pull": 2,

    # Мінімальне — ізоляція, стабілізація
    "bicep_curl": 1,
    "bicep_curl_isolated": 1,
    "tricep_extension": 1,
    "lateral_raise": 1,
    "front_raise": 1,
    "rear_delt_fly": 1,
    "chest_fly": 1,
    "leg_curl": 1,
    "leg_extension": 1,
    "calf_raise": 1,
    "core_flexion": 1,
    "core_stability": 1,
    "core_rotation": 1,
    "mobility": 1,
}
DEFAULT_CNS_COST = 2


def compute_cns_cost(pattern: str) -> int:
    return CNS_COST_BY_PATTERN.get(pattern, DEFAULT_CNS_COST)


def enrich_exercise(ex: dict) -> dict:
    """Мутує вправу на місці, додаючи 9 полів метаданих (Database 2.0 + 2.1).
    Повертає той самий dict."""
    pattern = _seed_get_pattern(ex["name"])
    fatigue = _seed_get_fatigue(pattern)

    ex["movement_pattern"] = pattern
    ex["fatigue"] = fatigue
    ex["compound"] = compute_compound(pattern)
    ex["unilateral"] = compute_unilateral(pattern)
    ex["spine_load"] = compute_spine_load(pattern)
    ex["stability"] = compute_stability(ex, pattern)
    ex["skill"] = compute_skill(ex, pattern)
    ex["stimulus"] = compute_stimulus(ex, pattern)          # 2.1: тепер число 1-10
    ex["recovery_days"] = compute_recovery_days(fatigue)     # 2.1: нове поле
    ex["cns_cost"] = compute_cns_cost(pattern)                # 2.2: нове поле
    return ex


def enrich_all(exercises_list: list) -> None:
    """Збагачує весь список вправ на місці (мутація, без копіювання списку)."""
    for ex in exercises_list:
        enrich_exercise(ex)
