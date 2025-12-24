import asyncio, datetime, os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from config import TOKEN, SERVER_NAME, ADMIN_IDS, MAX_ADS_PER_DAY
from db import init_db, add_ad, get_ads, count_today_ads
from anti_scam import is_scam
from ocr import read_text

bot = Bot(TOKEN)
dp = Dispatcher()

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Продать")],
        [KeyboardButton(text="🚗 Авто"), KeyboardButton(text="🎒 Вещи")],
        [KeyboardButton(text="🏢 Бизнесы"), KeyboardButton(text="🏠 Недвижимость")]
    ],
    resize_keyboard=True
)

class AddAd(StatesGroup):
    category = State()
    title = State()
    description = State()
    price = State()
    photo = State()

@dp.message(F.text == "/start")
async def start(msg: Message):
    await msg.answer(f"🏪 {SERVER_NAME}\nРынок объявлений", reply_markup=menu)

@dp.message(F.text == "➕ Продать")
async def sell(msg: Message, state: FSMContext):
    if await count_today_ads(msg.from_user.id) >= MAX_ADS_PER_DAY:
        await msg.answer("❌ Лимит объявлений на сегодня")
        return
    await msg.answer("Выбери категорию:
Авто / Вещи / Бизнесы / Недвижимость")
    await state.set_state(AddAd.category)

@dp.message(AddAd.category)
async def set_category(msg: Message, state: FSMContext):
    await state.update_data(category=msg.text.replace("🚗 ","").replace("🎒 ","").replace("🏢 ","").replace("🏠 ",""))
    await msg.answer("Отправь СКРИНШОТ товара/бизнеса/дома")
    await state.set_state(AddAd.photo)

@dp.message(AddAd.photo, F.photo)
async def photo_handler(msg: Message, state: FSMContext):
    file = await bot.get_file(msg.photo[-1].file_id)
    path = f"temp_{msg.from_user.id}.jpg"
    await bot.download_file(file.file_path, path)
    text = read_text(path)
    os.remove(path)

    if is_scam(text):
        await msg.answer("🚫 Обнаружен скам. Объявление отклонено.")
        await state.clear()
        return

    await state.update_data(description=text, photo=msg.photo[-1].file_id)
    await msg.answer(f"Распознан текст:\n{text}\n\nВведите название:")
    await state.set_state(AddAd.title)

@dp.message(AddAd.title)
async def set_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await msg.answer("Цена:")
    await state.set_state(AddAd.price)

@dp.message(AddAd.price)
async def set_price(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.answer("Цена должна быть числом")
        return
    data = await state.get_data()
    username = msg.from_user.username or "Без_ника"
    await add_ad((
        msg.from_user.id,
        username,
        data["category"],
        data["title"],
        data["description"],
        int(msg.text),
        data["photo"],
        datetime.date.today().isoformat()
    ))
    for admin in ADMIN_IDS:
        await bot.send_message(admin, "🆕 Новое объявление на модерации")
    await msg.answer("✅ Объявление отправлено на модерацию")
    await state.clear()

@dp.message(F.text.in_(["🚗 Авто","🎒 Вещи","🏢 Бизнесы","🏠 Недвижимость"]))
async def show_ads(msg: Message):
    category = msg.text.replace("🚗 ","").replace("🎒 ","").replace("🏢 ","").replace("🏠 ","")
    ads = await get_ads(category)
    if not ads:
        await msg.answer("❌ Нет объявлений")
        return
    for title, desc, price, photo, username in ads:
        await msg.answer_photo(photo, caption=f"📦 {title}\n💬 {desc}\n💰 {price}\n📞 @{username}")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
