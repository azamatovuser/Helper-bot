from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class SendMessage(StatesGroup):
    waiting_for_data = State()


main_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_button.add("Написать сообщение в канал", "О проекте")

approve_button = types.InlineKeyboardButton(text="Подтвердить ✅", callback_data="approve")
delete_button = types.InlineKeyboardButton(text="Удалить 🚫", callback_data="delete")
inline_keyboard = types.InlineKeyboardMarkup().row(approve_button, delete_button)

class SendMessage(StatesGroup):
    waiting_for_data = State()

@dp.message_handler(text='Отмена', state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено", reply_markup=main_button)

@dp.message_handler(commands='start')
async def start_function(message: types.Message):
    await message.answer("Привет!", reply_markup=main_button)


@dp.message_handler(text='Написать сообщение в канал')
async def request_function(message: types.Message):
    await SendMessage.waiting_for_data.set()
    await message.answer("У вас есть фото или видео?")


@dp.message_handler(lambda message: message.text.lower() == 'да', state=SendMessage.waiting_for_data)
async def have_media(message: types.Message, state: FSMContext):
    await state.update_data(media=True)
    await message.answer("Пожалуйста, отправьте фото или видео.")


@dp.message_handler(lambda message: message.text.lower() == 'нет', state=SendMessage.waiting_for_data)
async def no_media(message: types.Message, state: FSMContext):
    await state.update_data(media=False)
    await message.answer("Введите текст сообщения:")


@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.VIDEO], state=SendMessage.waiting_for_data)
async def get_media(message: types.Message, state: FSMContext):
    media_type = message.content_type
    await state.update_data(media_type=media_type)
    
    # Получаем информацию о медиафайле
    media_info = None
    if message.photo:
        media_info = "Фото"
    elif message.video:
        media_info = "Видео"
    await state.update_data(media_info=media_info)
    
    await message.answer("Теперь введите текст сообщения:")


@dp.message_handler(state=SendMessage.waiting_for_data)
async def get_text_message(message: types.Message, state: FSMContext):
    text_message = message.text
    user_data = await state.get_data()
    has_media = user_data.get('media_type') is not None
    
    if has_media:
        media_info = user_data.get('media_info')
        await message.answer(f"Текст сообщения: {text_message}, тип медиа: {media_info}")
    else:
        await message.answer(f"Текст сообщения: {text_message}")

    await state.finish()



if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
