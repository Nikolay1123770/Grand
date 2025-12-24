import aiosqlite, datetime

async def init_db():
    async with aiosqlite.connect("market.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            category TEXT,
            title TEXT,
            description TEXT,
            price INTEGER,
            photo TEXT,
            status TEXT DEFAULT 'pending',
            created DATE
        )
        """)
        await db.commit()

async def add_ad(data):
    async with aiosqlite.connect("market.db") as db:
        await db.execute("""
        INSERT INTO ads (user_id, username, category, title, description, price, photo, created)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        await db.commit()

async def get_ads(category):
    async with aiosqlite.connect("market.db") as db:
        cur = await db.execute("""
        SELECT title, description, price, photo, username
        FROM ads WHERE category=? AND status='approved'
        ORDER BY id DESC
        """, (category,))
        return await cur.fetchall()

async def count_today_ads(user_id):
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect("market.db") as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM ads WHERE user_id=? AND created=?",
            (user_id, today)
        )
        return (await cur.fetchone())[0]
