import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor
from config import TOKEN, CHANNEL_ID, USER_ID

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class SendMessage(StatesGroup):
    waiting_for_data = State()

main_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_button.add("Send Message to Channel", "About Project")

cancel_button = types.KeyboardButton("Cancel")
cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(cancel_button)

@dp.message_handler(commands='start')
async def start_function(message: types.Message):
    await message.answer("Hello!", reply_markup=main_button)

@dp.message_handler(text='Send Message to Channel')
async def request_function(message: types.Message):
    await SendMessage.waiting_for_data.set()
    await message.answer("Send me a photo, video, or text in one message", reply_markup=cancel_markup)

@dp.message_handler(text='Cancel', state=SendMessage.waiting_for_data)
async def cancel_sending(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Message sending cancelled", reply_markup=main_button)

async def forward_message(message: types.Message):
    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(
        types.InlineKeyboardButton(text="Approve", callback_data=f"approve:{message.message_id}"),
        types.InlineKeyboardButton(text="Delete", callback_data=f"delete:{message.message_id}")
    )
    author_info = f"\n\nAuthor: @{message.from_user.username}" if message.from_user.username else "\n\nAuthor: @empty"
    await bot.send_message(chat_id=USER_ID, text=message.text + author_info, reply_markup=inline_kb, disable_notification=True)
    await bot.send_message(chat_id=message.chat.id, text="Your message has been delivered", reply_markup=main_button)

async def forward_media_with_caption(message: types.Message):
    author_info = f"\n\nAuthor: @{message.from_user.username}" if message.from_user.username else "\n\nAuthor: @empty"
    caption = message.caption if message.caption else ""
    if message.content_type == types.ContentType.PHOTO:
        media_content = message.photo[-1].file_id
        inline_kb = types.InlineKeyboardMarkup()
        inline_kb.add(
            types.InlineKeyboardButton(text="Approve", callback_data=f"approve:{message.message_id}"),
            types.InlineKeyboardButton(text="Delete", callback_data=f"delete:{message.message_id}")
        )
        await bot.send_photo(chat_id=USER_ID, photo=media_content, caption=caption + author_info, reply_markup=inline_kb, disable_notification=True)
        await bot.send_message(chat_id=message.chat.id, text="Your message has been delivered", reply_markup=main_button)
    elif message.content_type == types.ContentType.VIDEO:
        media_content = message.video.file_id
        inline_kb = types.InlineKeyboardMarkup()
        inline_kb.add(
            types.InlineKeyboardButton(text="Approve", callback_data=f"approve:{message.message_id}"),
            types.InlineKeyboardButton(text="Delete", callback_data=f"delete:{message.message_id}")
        )
        await bot.send_video(chat_id=USER_ID, video=media_content, caption=caption + author_info, reply_markup=inline_kb, disable_notification=True)
        await bot.send_message(chat_id=message.chat.id, text="Your message has been delivered", reply_markup=main_button)
    elif message.content_type == types.ContentType.TEXT:
        # Send the text message directly to the target channel without forwarding
        inline_kb = types.InlineKeyboardMarkup()
        inline_kb.add(
            types.InlineKeyboardButton(text="Approve", callback_data=f"approve:{message.message_id}"),
            types.InlineKeyboardButton(text="Delete", callback_data=f"delete:{message.message_id}")
        )
        await bot.copy_message(chat_id=CHANNEL_ID, from_chat_id=message.chat.id, message_id=message.message_id, reply_markup=inline_kb, disable_notification=True)
        await bot.send_message(chat_id=message.chat.id, text="Your message has been delivered", reply_markup=main_button)

@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.VIDEO, types.ContentType.TEXT], state=SendMessage.waiting_for_data)
async def handle_media_with_caption(message: types.Message, state: FSMContext):
    await state.finish()

    if message.content_type == types.ContentType.PHOTO or message.content_type == types.ContentType.VIDEO:
        await handle_multiple_media(message, state)
    elif message.content_type == types.ContentType.TEXT:
        await forward_message(message)

async def handle_multiple_media(message: types.Message, state: FSMContext):
    # Get the current state data
    data = await state.get_data()
    media_count = data.get('media_count', 0)

    # Increment the media count
    media_count += 1

    if media_count > 1:
        await state.finish()
        await message.answer("Bro, only one photo or video is allowed", reply_markup=main_button)
        return

    # Update the state data
    await state.update_data(media_count=media_count)

    # Proceed to handle the media
    if message.content_type == types.ContentType.PHOTO or message.content_type == types.ContentType.VIDEO:
        await forward_media_with_caption(message)
    else:
        await handle_unsupported_files(message, state)

@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.VIDEO, types.ContentType.TEXT], state=SendMessage.waiting_for_data)
async def handle_unsupported_files(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Only photo or video file type is allowed, please do not send unsupported files", reply_markup=main_button)

@dp.callback_query_handler(lambda callback_query: True)
async def handle_inline_button(callback_query: types.CallbackQuery):
    data = callback_query.data.split(":")
    action = data[0]
    message_id = int(data[1])
    user_id = callback_query.from_user.id  # User who approved or deleted the message
    
    if action == "approve":
        message = callback_query.message
        await bot.answer_callback_query(callback_query.id)
        
        if message.caption:
            cleaned_text = re.sub(r"Author: @\w+", "", message.caption)
            # Send media with caption
            if message.photo:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=message.photo[-1].file_id, caption=cleaned_text)
            elif message.video:
                await bot.send_video(chat_id=CHANNEL_ID, video=message.video.file_id, caption=cleaned_text)
            elif message.text:
                cleaned_only_text1 = re.sub(r"Author: @\w+", "", message.text)
                await bot.send_message(chat_id=CHANNEL_ID, text=cleaned_only_text1)
        else:
            # Send media without caption
            if message.photo:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=message.photo[-1].file_id)
            elif message.video:
                await bot.send_video(chat_id=CHANNEL_ID, video=message.video.file_id)
            elif message.text:
                cleaned_only_text2 = re.sub(r"\n\nAuthor: @\w+", "", message.text)
                await bot.send_message(chat_id=CHANNEL_ID, text=cleaned_only_text2)
        
        # Notify user and delete messages
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.send_message(chat_id=message.chat.id, text="Message sent")
    
    elif action == "delete":
        message = callback_query.message
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        
        # Notify both users about message deletion
        await bot.send_message(chat_id=message.chat.id, text="Message was deleted and will not be uploaded to the channel")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
