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

@dp.message_handler(commands='start')
async def start_function(message: types.Message):
    await message.answer("Привет!", reply_markup=main_button)

@dp.message_handler(text='Написать сообщение в канал')
async def request_function(message: types.Message):
    await SendMessage.waiting_for_data.set()
    await message.answer("Отправьте мне фото, видео или текст в одном сообщении.")

@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.VIDEO, types.ContentType.TEXT], state=SendMessage.waiting_for_data)
async def handle_media_with_caption(message: types.Message, state: FSMContext):
    await state.finish()
    if message.content_type == types.ContentType.TEXT:
        await forward_message(message)
    else:
        await forward_media_with_caption(message)

async def forward_message(message: types.Message):
    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(
        types.InlineKeyboardButton(text="Approve", callback_data=f"approve:{message.message_id}"),
        types.InlineKeyboardButton(text="Delete", callback_data=f"delete:{message.message_id}")
    )
    await bot.send_message(chat_id=538905701, text=message.text, reply_markup=inline_kb, disable_notification=True)

async def forward_media_with_caption(message: types.Message):
    if message.content_type == types.ContentType.PHOTO:
        media_content = message.photo[-1].file_id
        inline_kb = types.InlineKeyboardMarkup()
        inline_kb.add(
            types.InlineKeyboardButton(text="Approve", callback_data=f"approve:{message.message_id}"),
            types.InlineKeyboardButton(text="Delete", callback_data=f"delete:{message.message_id}")
        )
        await bot.send_photo(chat_id=538905701, photo=media_content, caption=message.caption, reply_markup=inline_kb, disable_notification=True)
    elif message.content_type == types.ContentType.VIDEO:
        media_content = message.video.file_id
        inline_kb = types.InlineKeyboardMarkup()
        inline_kb.add(
            types.InlineKeyboardButton(text="Approve", callback_data=f"approve:{message.message_id}"),
            types.InlineKeyboardButton(text="Delete", callback_data=f"delete:{message.message_id}")
        )
        await bot.send_video(chat_id=538905701, video=media_content, caption=message.caption, reply_markup=inline_kb, disable_notification=True)
    elif message.content_type == types.ContentType.TEXT:
        # Send the text message directly to the target channel without forwarding
        inline_kb = types.InlineKeyboardMarkup()
        inline_kb.add(
            types.InlineKeyboardButton(text="Approve", callback_data=f"approve:{message.message_id}"),
            types.InlineKeyboardButton(text="Delete", callback_data=f"delete:{message.message_id}")
        )
        await bot.copy_message(chat_id=-1002078750067, from_chat_id=message.chat.id, message_id=message.message_id, reply_markup=inline_kb, disable_notification=True)


@dp.callback_query_handler(lambda callback_query: True)
async def handle_inline_button(callback_query: types.CallbackQuery):
    data = callback_query.data.split(":")
    action = data[0]
    message_id = int(data[1])
    if action == "approve":
        await bot.answer_callback_query(callback_query.id)
        await bot.forward_message(chat_id=-1002078750067, from_chat_id=callback_query.message.chat.id, message_id=message_id, disable_notification=True)
    elif action == "delete":
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=message_id)
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
