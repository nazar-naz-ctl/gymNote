"""
GymNote — діагностика бота
Запуск: python check_bot.py
"""

import json
import os
import sys
import importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))
ERRORS = []
WARNINGS = []
OK = []

def ok(msg): OK.append(msg); print(f"  ✅ {msg}")
def warn(msg): WARNINGS.append(msg); print(f"  ⚠️  {msg}")
def err(msg): ERRORS.append(msg); print(f"  ❌ {msg}")


# ─── 1. Файли та папки ───────────────────────────────────────────────────────

print("\n📁 Перевірка файлів і папок")

required_files = [
    "bot.py", "config.py", ".env", "requirements.txt",
    "data/users.json",
    "database/__init__.py", "database/db.py",
    "handlers/__init__.py", "handlers/start.py", "handlers/registration.py",
    "handlers/profile.py", "handlers/progress.py", "handlers/programs.py",
    "handlers/workout.py", "handlers/referral.py", "handlers/contact.py",
    "handlers/trainer.py", "handlers/tips.py",
    "keyboards/__init__.py", "keyboards/main_kb.py", "keyboards/registration_kb.py",
]

for f in required_files:
    path = os.path.join(ROOT, f)
    if os.path.exists(path):
        ok(f)
    else:
        err(f"Файл не знайдено: {f}")


# ─── 2. .env змінні ──────────────────────────────────────────────────────────

print("\n🔑 Перевірка .env")

env_path = os.path.join(ROOT, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        env_content = f.read()
    if "BOT_TOKEN" in env_content:
        token_line = [l for l in env_content.splitlines() if "BOT_TOKEN" in l]
        token_val = token_line[0].split("=", 1)[-1].strip() if token_line else ""
        if len(token_val) > 10:
            ok("BOT_TOKEN заповнений")
        else:
            err("BOT_TOKEN порожній!")
    else:
        err("BOT_TOKEN відсутній в .env")

    if "TRAINER_ID" in env_content:
        tid_line = [l for l in env_content.splitlines() if "TRAINER_ID" in l]
        tid_val = tid_line[0].split("=", 1)[-1].strip() if tid_line else ""
        if tid_val.isdigit():
            ok(f"TRAINER_ID = {tid_val}")
        else:
            err("TRAINER_ID не є числом!")
    else:
        err("TRAINER_ID відсутній в .env")
else:
    err(".env файл не знайдено!")


# ─── 3. База даних users.json ─────────────────────────────────────────────────

print("\n🗄️  Перевірка бази даних (users.json)")

db_path = os.path.join(ROOT, "data/users.json")
if os.path.exists(db_path):
    try:
        with open(db_path, encoding="utf-8") as f:
            db = json.load(f)

        if isinstance(db, dict):
            ok("Формат бази правильний (словник {})")
        elif isinstance(db, list):
            err("База даних — список []! Має бути словник {}. Виправ командою: python -c \"open('data/users.json','w').write('{}')\"")
        else:
            err(f"Невідомий формат бази: {type(db)}")

        # Рахуємо клієнтів
        clients = 0
        broken_users = []
        non_numeric_keys = []

        for key, val in db.items():
            try:
                int(key)
                if not isinstance(val, dict):
                    broken_users.append(key)
                else:
                    clients += 1
            except ValueError:
                non_numeric_keys.append(key)
                # Перевіряємо що нечислові значення не є списком словників з .get()
                if not isinstance(val, list):
                    warn(f"Нечисловий ключ '{key}' має незвичний тип: {type(val)}")

        ok(f"Клієнтів у базі: {clients}")

        if broken_users:
            err(f"Зламані записи (не словники): {broken_users}")

        if non_numeric_keys:
            ok(f"Службові ключі в базі: {non_numeric_keys}")

        # Перевірка підписок
        subs = {"free": 0, "standard": 0, "premium": 0}
        for key, val in db.items():
            try:
                int(key)
            except ValueError:
                continue
            if isinstance(val, dict):
                s = val.get("subscription", "free")
                subs[s] = subs.get(s, 0) + 1
        ok(f"Підписки: free={subs['free']}, standard={subs['standard']}, premium={subs['premium']}")

    except json.JSONDecodeError as e:
        err(f"users.json зламаний (не валідний JSON): {e}")
else:
    err("data/users.json не знайдено!")


# ─── 4. Конфліктні callback назви ────────────────────────────────────────────

print("\n🔍 Перевірка конфліктів callback")

handlers_dir = os.path.join(ROOT, "handlers")
callback_map = {}  # callback_data -> [файли]

known_conflicts = {
    "progress_records": "правильно (замість records_personal)",
    "referral": "КОНФЛІКТ — має бути referral_menu",
    "subscription": "КОНФЛІКТ — має бути my_subscription",
    "t_create_workout": "КОНФЛІКТ — має бути t_create_workout2",
}

if os.path.exists(handlers_dir):
    for fname in os.listdir(handlers_dir):
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(handlers_dir, fname)
        with open(fpath, encoding="utf-8") as f:
            content = f.read()

        # Шукаємо всі F.data == "..."
        import re
        matches = re.findall(r'F\.data\s*==\s*["\']([^"\']+)["\']', content)
        for m in matches:
            if m not in callback_map:
                callback_map[m] = []
            callback_map[m].append(fname)

    # Знаходимо дублікати
    duplicates = {k: v for k, v in callback_map.items() if len(v) > 1}
    if duplicates:
        for cb, files in duplicates.items():
            err(f"Конфлікт callback '{cb}' в файлах: {', '.join(files)}")
    else:
        ok("Конфліктів callback не знайдено")

    # Перевіряємо відомі проблемні назви
    for bad_cb, note in known_conflicts.items():
        if bad_cb in callback_map:
            warn(f"Callback '{bad_cb}' присутній — {note} (файли: {callback_map[bad_cb]})")


# ─── 5. Порядок роутерів ─────────────────────────────────────────────────────

print("\n📋 Перевірка порядку роутерів (handlers/__init__.py)")

init_path = os.path.join(ROOT, "handlers/__init__.py")
if os.path.exists(init_path):
    with open(init_path, encoding="utf-8") as f:
        init_content = f.read()

    expected_order = [
        "start_router", "registration_router", "profile_router",
        "progress_router", "referral_router", "trainer_router",
        "programs_router", "workout_router", "contact_router", "tips_router"
    ]

    positions = {}
    for r in expected_order:
        idx = init_content.find(r)
        if idx == -1:
            warn(f"Роутер '{r}' не знайдено в init.py")
        else:
            positions[r] = idx

    # Перевіряємо чи trainer_router перед programs_router
    if "trainer_router" in positions and "programs_router" in positions:
        if positions["trainer_router"] < positions["programs_router"]:
            ok("trainer_router стоїть перед programs_router ✓")
        else:
            warn("trainer_router має стояти ПЕРЕД programs_router!")

    ok(f"Знайдено роутерів: {len(positions)}/{len(expected_order)}")


# ─── 6. Імпорти в referral.py ────────────────────────────────────────────────

print("\n📦 Перевірка referral.py")

ref_path = os.path.join(ROOT, "handlers/referral.py")
if os.path.exists(ref_path):
    with open(ref_path, encoding="utf-8") as f:
        ref_content = f.read()

    checks = [
        ("main_menu_kb", "імпорт main_menu_kb"),
        ("referral_menu", "callback referral_menu (не referral)"),
        ("get_referral_stats", "функція get_referral_stats"),
        ("get_new_referrals", "функція get_new_referrals"),
        ("isinstance(data, dict)", "захист від списків у get_referral_stats"),
        ("main_menu", "хендлер кнопки Назад"),
    ]

    for keyword, label in checks:
        if keyword in ref_content:
            ok(label)
        else:
            err(f"Відсутнє: {label}")


# ─── 7. Перевірка start.py ───────────────────────────────────────────────────

print("\n🚀 Перевірка start.py")

start_path = os.path.join(ROOT, "handlers/start.py")
if os.path.exists(start_path):
    with open(start_path, encoding="utf-8") as f:
        start_content = f.read()

    checks = [("ref_", "обробка реферального посилання"),
        ("referrer_id", "збереження referrer_id в state"),
        ("update_user_field", "імпорт update_user_field"),
    ]
    for keyword, label in checks:
        if keyword in start_content:
            ok(label)
        else:
            err(f"Відсутнє в start.py: {label}")


# ─── 8. Перевірка registration.py ────────────────────────────────────────────

print("\n📝 Перевірка registration.py")

reg_path = os.path.join(ROOT, "handlers/registration.py")
if os.path.exists(reg_path):
    with open(reg_path, encoding="utf-8") as f:
        reg_content = f.read()

    checks = [
        ("referred_by", "збереження referred_by при реєстрації"),
        ("joined_giveaway", "збереження joined_giveaway"),
        ("referrer_id", "зчитування referrer_id зі state"),
    ]
    for keyword, label in checks:
        if keyword in reg_content:
            ok(label)
        else:
            warn(f"Відсутнє в registration.py: {label}")


# ─── Підсумок ─────────────────────────────────────────────────────────────────

print("\n" + "="*50)
print("📊 ПІДСУМОК ДІАГНОСТИКИ")
print("="*50)
print(f"  ✅ Ок:        {len(OK)}")
print(f"  ⚠️  Попередження: {len(WARNINGS)}")
print(f"  ❌ Помилки:   {len(ERRORS)}")

if ERRORS:
    print("\n❌ КРИТИЧНІ ПОМИЛКИ (треба виправити):")
    for e in ERRORS:
        print(f"   • {e}")

if WARNINGS:
    print("\n⚠️  ПОПЕРЕДЖЕННЯ (варто перевірити):")
    for w in WARNINGS:
        print(f"   • {w}")

if not ERRORS and not WARNINGS:
    print("\n🎉 Все гаразд! Бот готовий до роботи.")
elif not ERRORS:
    print("\n✅ Критичних помилок немає. Бот має працювати.")
else:
    print("\n🔧 Виправ помилки вище і запусти перевірку знову.")
