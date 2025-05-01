from aiogram.types import CallbackQuery
from aiogram import F, Router
from db import db
from aiogram import Bot
import pytz
from datetime import datetime
from config import token

accept_router = Router()
async def get_bot():
    return Bot(token)

@accept_router.callback_query(lambda c: c.data.startswith("Accept_Task"))
async def accept_task_callback(callback_query: CallbackQuery, bot: Bot):
    task_number = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id
    bs = db.get_sitename(task_number)
    current_time = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M")
    db.update_task("В работе",user_id, current_time,task_number)
    fio = db.get_fio_worker(user_id)
    supervisors = db.get_all_supervisors()
    message_text = (
        f"<b>Задача №</b> <code>{task_number}</code>\n"
        f"<b>Б/C - {bs[0]}</b>\n"
        f"<b>Принята</b> {fio} в : {current_time}"
    )
    for supervisor in supervisors:
        await bot.send_message(supervisor[0], message_text, parse_mode="HTML")
    await callback_query.message.edit_text(message_text)