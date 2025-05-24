from aiogram.types import CallbackQuery
from aiogram import F, Router
from db import db
from aiogram import Bot
import pytz
from datetime import datetime
from config import token
from urllib.parse import quote_plus
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
accept_router = Router()
async def get_bot():
    return Bot(token)

@accept_router.callback_query(F.data.startswith("Accept_Task:"))
async def accept_task_callback(callback_query: CallbackQuery, bot: Bot):
    task_number = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id
    current_time = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")
    db.update_task("В работе", user_id, current_time, task_number)
    task_data = db.get_task_by_number(task_number)
    fio = db.get_fio_worker(user_id)
    encode = quote_plus(task_data[12])
    url = f"https://yandex.ru/maps/?text={encode}"
    message_text = (
                        f"<b>ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤНовое задание!</b>\n\n"
                        f"<b>Номер задания:</b> <code>{task_data[1]}</code>\n"
                        f"<b>Номер БС:</b> {task_data[2]}\n"
                        f"<b>Статус:</b> {task_data[3]}\n"
                        f"<b>Дата выдачи:</b> {task_data[5]}\n"
                        f"<b>Время прибытия:</b> {task_data[6]}\n"
                        f"<b>Тип работ:</b> {task_data[8]}\n"
                        f"<b>Краткое описание работ:</b> {task_data[9]}\n"
                        f"<b>Описание работ:</b> {task_data[10]}\n"
                        f"<b>Примечание / Комментарии:</b> {task_data[11]}\n"
                        f'<b>Адрес:</b> <a href="{url}">{task_data[12]}</a>\n'
                        f"<b>Ответственный:</b> {task_data[13]}\n"
                        f"<b>Для подтверждения принятия WO в работу отправьте на номер 359 СМС с текстом:</b> "
                        f"<code>#107*{task_data[1].replace('T2','')}#</code>\n"
                    )
    accepted_keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text=f"✅ Принята: {fio}", callback_data="noop")]
        ]
    )
    await callback_query.message.edit_text(
        message_text,
        parse_mode="HTML",
        reply_markup=accepted_keyboard
    )
    supervisors = db.get_all_supervisors()
    for supervisor in supervisors:
        await bot.send_message(supervisor[0], f"<b>Задача № </b><code>{task_data[1]}</code>\n <b>Б/C - {task_data[2]}</b>\n <b>Принята : {fio} в {current_time} </b>", parse_mode="HTML")
    await callback_query.answer("Заявка принята.")