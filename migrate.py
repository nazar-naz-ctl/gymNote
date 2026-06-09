import asyncio
import json
from database.mongo import users_col


async def migrate():
    with open('data/users.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    count = 0
    for uid, user in data.items():
        try:
            user_id = int(uid)
            user['_id'] = user_id
            await users_col.update_one(
                {'_id': user_id},
                {'$set': user},
                upsert=True
            )
            count += 1
        except ValueError:
            pass
    print(f'Перенесено {count} користувачів')


asyncio.run(migrate())