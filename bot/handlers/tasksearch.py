from aiogram.types import CallbackQuery
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from db import db
from keyboards.menu import main_menu
from states.states import SearchState
from aiogram.types import Message

search_router = Router()

@search_router.callback_query(F.data == "Find_Task")
async def find_task_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(text="Введите номер заявки:")
    await state.set_state(SearchState.waiting_for_task_number)

@search_router.message(SearchState.waiting_for_task_number)
async def search_task_callback(message: Message, state: FSMContext):
    task_number = message.text.strip()
    if not task_number.startswith("T2WO"):
        await message.answer("Неверный формат номера. Попробуйте снова.")
        return

    task = db.get_task_by_number(task_number)
    if not task:
        await message.answer("Заявка с таким номером не найдена.")
        return

    _, task_number, base_station, status, assigned_to, issue_time, timereq,acceptance_time, close_time, work_type, description, short_description, comments, address, responsible_person, exited_by_worker, _, _, = task
    fio = db.get_fio_worker(assigned_to) if assigned_to else "—"
    message_text = (
        f"<b>Номер задачи:</b> {task_number}\n"
        f"<b>Базовая станция:</b> {base_station}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Исполнитель:</b> {fio}\n"
        f"<b>Выдана:</b> {issue_time}\n"
        f"<b>Время прибытия:</b> {timereq}\n"
        f"<b>Принята:</b> {acceptance_time if acceptance_time else '—'}\n"
        f"<b>Закрыта:</b> {close_time if close_time else '—'}\n"
        f"<b>Тип работ:</b> {work_type if work_type else '—'}\n"
        f"<b>Краткое описание:</b> {short_description if short_description else '—'}\n"
        f"<b>Описание:</b> {description if description else '—'}\n"
        f"<b>Комментарии:</b> {comments if comments else '—'}\n"
        f"<b>Адрес:</b> {address if address else '—'}\n"
        f"<b>Ответственный:</b> {responsible_person if responsible_person else '—'}\n"
        f"<b>Закрыта работником:</b> {exited_by_worker if exited_by_worker else '—'}"
    )

    await message.answer(message_text, parse_mode="HTML", reply_markup=main_menu())
    await state.clear()