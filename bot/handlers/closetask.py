from aiogram import F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from keyboards.menu import main_menu
from states.states import CloseTaskSG
from db import db
import pytz
from datetime import datetime
from aiogram.filters.state import StateFilter
from keyboards.closetaskkb import create_reasons_keyboard, create_subreasons_keyboard, create_avr_keyboard, REASONS, REQUIRES_AMOUNT, SUBREASONS
close_router = Router()

@close_router.callback_query(F.data.startswith("reason_prev:") | F.data.startswith("reason_next:"))
async def _reason_change_page(query: CallbackQuery):
    # callback_data: "reason_prev:{task_number}:{new_page}"
    _, task_number, page_str = query.data.split(":")
    page = int(page_str)

    kb = create_reasons_keyboard(task_number, page)
    await query.message.edit_reply_markup(reply_markup=kb)
    await query.answer()


@close_router.callback_query(F.data.startswith("subreason_prev:") | F.data.startswith("subreason_next:"))
async def _subreason_change_page(query: CallbackQuery):
    # callback_data: "subreason_prev:{task_number}:{reason_idx}:{new_page}"
    _, task_number, reason_idx, page_str = query.data.split(":")
    page = int(page_str)
    reason_idx = int(reason_idx)

    kb = create_subreasons_keyboard(task_number, reason_idx, page)
    await query.message.edit_reply_markup(reply_markup=kb)
    await query.answer()

@close_router.callback_query(F.data.startswith("back_to_reasons:"))
async def _back_to_reasons(query: CallbackQuery):
    # callback_data: "back_to_reasons:{task_number}:0"
    _, task_number, _ = query.data.split(":")
    kb = create_reasons_keyboard(task_number, page=0)
    await query.message.edit_reply_markup(reply_markup=kb)
    await query.answer()


@close_router.callback_query(F.data.startswith("close_task:"))
async def start_close_task(cb: CallbackQuery, state: FSMContext):
    task_number = cb.data.split(":", 1)[1]
    task = db.get_task_by_number(task_number)
    _, task_number, base_station, status, assigned_to, issue_time, timereq, acceptance_time, close_time, work_type, description, short_description, comments, address, responsible_person, _, _, _ = task
    fio = db.get_fio_worker(assigned_to)

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
        f"<b>Ответственный:</b> {responsible_person if responsible_person else '—'}"
    )
    work_type = task[9]
    if work_type == "ППР":
        await state.update_data(
            task_number   = task_number,
            ppr_codes     = [],
            ppr_quantities= []
        )
        await state.set_state(CloseTaskSG.choosing_ppr)
        await cb.message.edit_text(
            message_text + "\n\nВыберите раздел:",
            reply_markup=create_reasons_keyboard(task_number, 0)
        )
        return

    elif work_type == "АВР":
        await cb.message.edit_text(
            message_text,
            reply_markup=create_avr_keyboard(task_number)
        )
    await cb.answer()

@close_router.callback_query(F.data.startswith("select_reason:"), StateFilter(CloseTaskSG.choosing_ppr))
async def select_reason(cb: CallbackQuery, state: FSMContext):
    _, task_number, reason_idx = cb.data.split(":")
    reason_idx = int(reason_idx)
    await state.update_data(reason_idx=reason_idx)
    await cb.message.edit_text(
        f"Раздел: <b>{REASONS[reason_idx]}</b>\nВыберите подпункт:",
        parse_mode="HTML",
        reply_markup=create_subreasons_keyboard(task_number, reason_idx, 0)
    )

@close_router.callback_query(F.data.startswith("avr_generation:"))
async def avr_generation(cb: CallbackQuery):
    task_number = cb.data.split(":",1)[1]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # При генерации нет количества, передаём 0
    db.close_task_by_worker(task_number, now_str, ["Генерация"], [0] )
    await cb.message.edit_text(
        f"Заявка №{task_number} закрыта (код: Генерация)",
        reply_markup=main_menu()
    )
    await cb.answer("Заявка закрыта с кодом «Генерация»")

@close_router.callback_query(F.data.startswith("avr_other:"))
async def avr_other(cb: CallbackQuery):
    task_number = cb.data.split(":",1)[1]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.close_task_by_worker(task_number, now_str, ["Другое"], [0])
    await cb.message.edit_text(
        f"Заявка №{task_number} закрыта (код: Другое)",
        reply_markup=main_menu()
    )
    await cb.answer("Заявка закрыта с кодом «Другое»")

@close_router.callback_query(F.data.startswith("select_subreason:"), StateFilter(CloseTaskSG.choosing_ppr))
async def select_subreason_ppr(cb: CallbackQuery, state: FSMContext):
    _, task_number, reason_idx, sub_idx = cb.data.split(":")
    reason_idx, sub_idx = int(reason_idx), int(sub_idx)
    sub = SUBREASONS[reason_idx][sub_idx]
    code = sub.split(maxsplit=1)[0]

    # Сохраняем текущий выбор во временных данных
    await state.update_data(current_code=code, current_sub=sub)

    if REQUIRES_AMOUNT.get((reason_idx, sub_idx), False):
        # переходим в ввод количества
        await state.set_state(CloseTaskSG.waiting_for_amount)
        await cb.message.edit_text(
            f"<b>{sub}</b>\n\nВведите количество:",
            parse_mode="HTML"
        )
    else:
        # сразу добавляем без количества и переходим к подтверждению
        data = await state.get_data()
        data["ppr_codes"].append(code)
        data["ppr_quantities"].append(1)
        await state.update_data(data)
        await state.set_state(CloseTaskSG.confirming_ppr)
        await _ask_more_or_finish(cb, state)

# обработка ввода количества
@close_router.message(CloseTaskSG.waiting_for_amount)
async def process_amount_ppr(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        return await msg.reply("Пожалуйста, введите целое число.")
    amount = str(msg.text)
    data = await state.get_data()
    # добавляем в массивы
    data["ppr_codes"].append(data["current_code"])
    data["ppr_quantities"].append(amount)
    await state.update_data(data)
    # спросим: добавить ещё или завершить
    await state.set_state(CloseTaskSG.confirming_ppr)
    await _ask_more_or_finish(msg, state)

async def _ask_more_or_finish(evt, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [ InlineKeyboardButton(text="➕ Добавить ещё", callback_data="ppr_more") ],
        [ InlineKeyboardButton(text="✅ Завершить",     callback_data="ppr_finish") ],
        [ InlineKeyboardButton(text="⛔ Отмена",         callback_data="cancel_close_task") ],
    ])
    text = "Добавить ещё подпункт или завершить закрытие?"
    if isinstance(evt, CallbackQuery):
        await evt.message.edit_text(text, reply_markup=kb)
        await evt.answer()
    else:
        await evt.answer(text, reply_markup=kb)

@close_router.callback_query(F.data=="ppr_more", StateFilter(CloseTaskSG.confirming_ppr))
async def ppr_more(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(CloseTaskSG.choosing_ppr)
    await cb.message.edit_text(
        "Выберите раздел:",
        reply_markup=create_reasons_keyboard(data["task_number"], 0)
    )
    await cb.answer()

@close_router.callback_query(F.data=="ppr_finish", StateFilter(CloseTaskSG.confirming_ppr))
async def ppr_finish(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    now = datetime.now(pytz.timezone("Europe/Moscow"))
    db.close_task_by_worker(
        data["task_number"],
        now,
        data["ppr_codes"],
        data["ppr_quantities"]
    )
    summary = "\n".join(
        f"{code} x{qty if qty is not None else '-'}"
        for code, qty in zip(data["ppr_codes"], data["ppr_quantities"])
    )
    await cb.message.edit_text(
        f"Заявка №{data['task_number']} закрыта с подпунктами:\n{summary}",
        reply_markup=main_menu()
    )
    await state.clear()
    await cb.answer()

@close_router.callback_query(F.data == "cancel_close_task")
async def cancel_close(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Закрытие заявки отменено.", reply_markup=main_menu())
    await cb.answer()

@close_router.callback_query(F.data == "confirm_close")
async def confirm_close(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_number = data['task_number']
    quantity    = data.get('amount') 
    close_code  = data['close_code']
    now = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")

    db.close_task_by_worker(task_number, now, quantity, close_code)

    await cb.message.edit_text(
        f"Заявка №{task_number} закрыта.\n"
        f"Код закрытия: {close_code}\n"
        f"Пункт: {data['subreason']}\n"
        + (f"Количество: {quantity}" if quantity is not None else "1"),
        reply_markup=main_menu()
    )
    await state.clear()
    await cb.answer()