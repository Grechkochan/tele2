from aiogram.types import CallbackQuery
from aiogram import F, Router
from db import db
from aiogram import Bot
from keyboards.menu import accept_task
from config import group_id
from urllib.parse import quote_plus

deny_router = Router()


@deny_router.callback_query(F.data.startswith("deny_task:"))
async def process_send_to_topic(callback_query: CallbackQuery, bot: Bot):
    task_number = callback_query.data.split(":")[1]
    task_data = db.get_task_by_number(task_number)
    if task_data[3] == "В работе":
        db.deny_task(task_data[1])
    else:
        await callback_query.answer("Вы не можете отказаться от закрытой задачи")
        return
    if not task_data:
        await callback_query.answer("Ошибка: заявка не найдена.")
        return
    encode = quote_plus(task_data[13])
    url = f"https://yandex.ru/maps/?text={encode}"
    message_text = (
        f"<b>ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤНовое задание!</b>\n\n"
        f"<b>Номер задания:</b> <code>{task_data[1]}</code>\n"
        f"<b>Номер БС:</b> {task_data[2]}\n"
        f"<b>Статус:</b> {task_data[3]}\n"
        f"<b>Дата выдачи:</b> {task_data[5]}\n"
        f"<b>Время прибытия:</b> {task_data[6]}\n"
        f"<b>Тип работ:</b> {task_data[9]}\n"
        f"<b>Краткое описание работ:</b> {task_data[10]}\n"
        f"<b>Описание работ:</b> {task_data[11]}\n"
        f"<b>Примечание / Комментарии:</b> {task_data[12]}\n"
        f'<b>Адрес:</b> <a href="{url}">{task_data[13]}</a>\n'
        f"<b>Ответственный:</b> {task_data[14]}\n"
    )
    topicid = db.get_topic_id_by_sitename(task_data[2])
    try:
        topicid = int(topicid[0])
    except (TypeError, ValueError, IndexError):
        topicid = 2
    await bot.send_message(
        group_id, message_text, parse_mode="HTML",
        reply_markup=accept_task(task_number), message_thread_id=topicid
    )
    supervisors = db.get_all_supervisors()
    for supervisor in supervisors:
        await bot.send_message(supervisor[0], f"<b>Исполнитель отказался от задачи № </b><code>{task_data[1]}</code>\n<b>Б/C - {task_data[2]}</b>", parse_mode="HTML")
