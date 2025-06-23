from aiogram import F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from math import ceil
from keyboards.menu import main_menu
from aiogram.fsm.state import StatesGroup, State
from db import db
import pytz
from datetime import datetime
close_router = Router()

class CloseTaskSG(StatesGroup):
    waiting_for_amount = State()
    waiting_for_confirmation = State()

# ——— 1. Данные —————————————————————————————
REASONS = [
    "Антенно-фидерное уст-во Объекта",
    "Оборудование Объекта",
    "Работы по ант.-фидерному устройству РРЛ",
    "Работы по оборудованию РРЛ и трансмиссии",
    "Работы по энергопринимающему устройству",
    "Общестроительные работы",
    "Помещения Объекта",
    "Охранно-пожарная сигнализация",
    "Драйв-тесты (радиоизмерения)",
    "Иные Работы",
    "Тех. обслуживание",
    "Иное",
    "Работы по моб. базовой станции",
]

# Подпункты для каждой причины
SUBREASONS = {
    0: [  # Антенно-фидерное устройство Объекта
        ".1.1. Диагностика оптической линии (длина, повреждения, затухание)",
        "1.2. Проверка/ремонт АФУ сектора (Net Monitor, разъёмы, КСВ)",
        "1.3. Замена RF-кабеля БС 1/2 (крепления, заземление)",
        "1.4. Замена RF-кабеля БС 7/8 (крепления, заземление)",
        "1.5. Замена RF-кабеля GPS-антенны",
        "1.6. Ремонт/замена RF-разъёмов N-type на АМС",
        "1.7. Ремонт/замена RF-разъёмов N-type в аппаратной",
        "1.8. Замена outdoor-джамперов 1/2\"",
        "1.9. Замена indoor-джамперов 1/2\"",
        "1.10. Замена кабеля управления RET",
        "1.11. Ремонт/замена устройств RET (угол наклона)",
        "1.12. Установка/юстировка антенн БС (джамперы, заземление)",
        "1.13. Механический угол наклона одной антенны",
        "1.14. Электрический угол наклона одной антенны",
        "1.15. Замена GPS-антенны",
        "1.16. Сверка АФУ с RDB + фотоотчёт",
        "1.17. Коррекция АФУ по RDB + фотоотчёт",
        "1.18. Прокладка ОВ-кабеля до 48 волокон",
        "1.19. Сварка оптоволокна + измерения",
        "1.20. Замена оптической муфты (до 16 волокон)",
        "1.21. Замена оптического кросса (до 16 волокон)",
        "1.22. Установка/замена аттенюатора",
        "1.23. Измерение мощности опт. сигнала"
    ],
    1: [  # Оборудование Объекта
        "2.1. Замена передатчика БС в аппаратной",
        "2.2. Замена передатчика БС на АМС",
        "2.3. Замена системного модуля БС (<10 м)",
        "2.4. Замена системного модуля БС (>10 м на АМС)",
        "2.5. Замена модуля в корзине БС (аппаратная)",
        "2.6. Замена модуля в корзине БС (АМС >10 м)",
        "2.7. Замена питания DUW/DUS/TCU",
        "2.8. Замена SFP-модуля (аппаратная)",
        "2.9. Замена SFP-модуля (на АМС)",
        "2.10. Прокладка DC 48 В кабеля питания",
        "2.11. Замена FAN-модуля (вентиляторы)",
        "2.12. Замена силовых кабелей на АМС",
        "2.13. Замена опт./UTP-кабеля аппаратная→АМС",
        "2.14. Замена аттенюатора/делителя/комбайнера indoor",
        "2.15. Замена DC кабеля (СИП 4×35,4×50)",
        "2.16. Замена ПВЗ-кабеля (1×25/1×35/1×10)",
        "2.17. Замена прокалывающего зажима",
        "2.18. Замена эл. коробки питания АМС",
        "2.19. Замена репитера indoor",
        "2.20. Замена датчика темп. + прокладка кабеля",
        "2.21. Замена indoor-стойки 19\"",
        "2.22. Настройка темп. режимов",
        "2.23. Монтаж монит. системы в шкафу",
        "2.24. Расшивка аварийных сигналов",
        "2.25. Обновление ПО без замены блоков",
        "2.26. Чистка опт. коннекторов (SC/FC/LC)",
        "2.27. Чистка вентиляторов и модулей"
    ],
    2: [  # Работы по АФУ РРЛ
        "3.1. Замена антенны РРЛ 0.3 м",
        "3.2. Замена антенны РРЛ 0.6–0.9 м",
        "3.3. Замена антенны РРЛ 1.2–1.8 м",
        "3.4. Юстировка РРЛ (0.3–0.9 м)",
        "3.5. Юстировка РРЛ (1.0–1.8 м)",
        "3.6. Юстировка полупролёта (0.3–0.9 м)",
        "3.7. Юстировка полупролёта (1.0–1.8 м)",
        "3.8. Ремонт заземления РРЛ-фидера",
        "3.9. Восстановление креплений кабелей",
        "3.10. Герметизация опт. соединения",
        "3.11. Диагностика АФУ РРЛ (разъёмы, Ground Kit)",
        "3.12. Замена ODU-блока РРЛ + настройка"
    ],
    3: [  # Оборудование РРЛ/трансмиссия
        "4.1. Интеграция трансмиссионного оборудования",
        "4.2. Замена корзины РРЛ и узлов агрегации",
        "4.3. Настройка параметров трансм. оборудования",
        "4.4. Замена indoor-плат на трансм. оборудовании",
        "4.5. Замена опт./медного патч-корда",
        "4.6. Кроссировка и проверка потоков"
    ],
    4: [  # Энергопринимающее устройство
        "5.1. Замена блока питания стойки",
        "5.2. Замена выпрямительного модуля",
        "5.3. Тест ИБП (разряд до 2 ч)",
        "5.4. Замена 1-а батареи ИБП",
        "5.5. Замена группы батарей ИБП",
        "5.6. Ремонт кабеля ГЗШ",
        "5.7. Ремонт вводного кабеля питания",
        "5.8. Замена/ремонт эл. щита",
        "5.9. Замена контактора/пускателя АВР",
        "5.10. Замена АСКУЭ",
        "5.11. Замена электросчётчика",
        "5.12. Замена АВВ/УЗИП/УЗО",
        "5.13. Замена вводного АВ/рубильника",
        "5.14. Снятие показаний счётчика",
        "5.15. Замена стойки питания БС",
        "5.16. Замена ИБП в шкафу",
        "5.17. Настройка и тест ИБП",
        "5.18. Ремонт узла отключения нагрузки",
        "5.19. Замена магазина автоматических выключателей"
    ],
    5: [  # Общестроительные работы
        "6.1. Замена розеток/выключателей",
        "6.2. Ремонт внутр. кабель-роста",
        "6.3. Ремонт нар. кабель-роста",
        "6.4. Устранение протечек (кровля)",
        "6.5. Изготовление ключа",
        "6.6. Устранение антиванд. нарушений",
        "6.7. Ремонт несущих конструкций",
        "6.8. Изготовление несущих конструкций",
        "6.9. Ремонт/замена двери",
        "6.10. Ремонт стен/пола/потолка",
        "6.11. Покраска металлоконструкций",
        "6.12. Ремонт антистат. линолеума",
        "6.13. Замена замка контейнера/шкафа",
        "6.14. Герметизация контейнера",
        "6.15. Ремонт светильника СОМ",
        "6.16. Перенос трубостойки (1 сайт)",
        "6.17. Перенос пригруж. трубостойки",
        "6.18. Замена антиванд. защиты",
        "6.19. Замена стеллажа АКБ",
        "6.20. Замена шкафа АКБ",
        "6.21. База КШ АКБ на грунт",
        "6.22. База КШ АКБ на стену",
        "6.23. База КШ АКБ (готовое основание)"
    ],
    6: [  # Помещения Объекта
        "7.1. Замена ламп и светильников в помещениях"
    ],
    7: [  # Охранно-пожарная сигнализация
        "8.1. Замена ОПС (комплект, извещатели, кабели, пуско-наладка)",
        "8.2. Замена аккумулятора ОПС",
        "8.3. Замена прибора приёмо-контрольного",
        "8.4. Монтаж кабеля КСПВ (шлейф сигн.)",
        "8.5. Замена дым/ИК/магнитного извещателя"
    ],
    8: [  # Драйв-тесты
        "9.1. Драйв-тест Indoor до 5 ч",
        "9.2. Драйв-тест Indoor свыше 5 ч",
        "9.3. Драйв-тест Outdoor (любое время)"
    ],
    9: [  # Иные Работы
        "10.1. Покос травы и уборка территории",
        "10.2. Содействие при проверках Объекта",
        "10.3. Иные услуги по одному обращению",
        "10.4. Осмотр нового Объекта (драйв-тест отдельно)",
        "10.5. Обследование схемы монтажа",
        "10.6. Минполоса до 1.5 м",
        "10.7. Маркировка РЭС (таблички)"
    ],
    10: [  # Техническое обслуживание
        "1.1. Тех. обслуживание БС"
    ],
    11: [  # Иное
        "4.5 Инвентаризация Объекта",
        "4.6. Компенсация проживания >24 ч (сутки)"
    ],
    12: [  # Мобильная базовая станция
        "5.1 Развёртывание/свёртывание МБС",
        "5.2. Замена оборудования в МБС",
        "5.3. Сопровождение работы МБС + топливо"
    ]
}

REQUIRES_AMOUNT = {
    (0, 0): True,   # 1.1 Диагностика, измерение потерь оптической линии — шт.
    (0, 2): True,   # 1.3 Замена RF-кабеля БС 1/2, РРЛ — м.п.
    (0, 3): True,   # 1.4 Замена RF-кабеля БС 7/8 — м.п.
    (0, 4): True,   # 1.5 Замена RF-кабеля GPS-антенны — м.п.
    (0, 5): True,   # 1.6 Ремонт/замена RF-разъёмов N-type на АМС — шт.
    (0, 6): True,   # 1.7 Ремонт/замена RF-разъёмов N-type в аппаратной — шт.
    (0, 7): True,   # 1.8 Замена outdoor-джамперов 1/2" — шт.
    (0, 8): True,   # 1.9 Замена indoor-джамперов 1/2" — шт.
    (0, 9): True,   # 1.10 Замена кабеля управления RET — шт.
    (0, 10): True,  # 1.11 Ремонт/замена устройств RET — шт.
    (0, 11): True,  # 1.12 Юстировка антенн БС — шт.
    (0, 12): True,  # 1.13 Изменение механического угла наклона — шт.
    (0, 13): True,  # 1.14 Изменение электр. угла наклона — шт.
    (0, 14): True,  # 1.15 Замена антенны GPS — шт.
    (0, 15): True,  # 1.16 Сверка АФУ с RDB + фотоотчёт — сектор
    (0, 16): True,  # 1.17 Приведение АФУ к RDB + фотоотчёт — сектор
    (0, 17): True,  # 1.18 Прокладка ОВ-кабеля до 48 волокон — м.п.
    (0, 18): True,  # 1.19 Сварка оптоволокна + измерения — волокно
    (0, 19): True,  # 1.20 Замена оптической муфты (до 16 ОВ) — шт.
    (0, 20): True,  # 1.21 Замена оптического кросса (до 16 ОВ) — шт.
    (0, 21): True,  # 1.22 Замена аттенюатора — шт.
    (0, 22): True,
    (1, 0): True, 
    (1, 1): True,   
    (1, 2): True,   
    (1, 3): True,  
    (1, 4): True,  
    (1, 5): True,  
    (1, 6): True,   
    (1, 7): True,   
    (1, 8): True,   
    (1, 9): True,   
    (1, 10): True, 
    (1, 11): True, 
    (1, 12): True, 
    (1, 13): True, 
    (1, 14): True,  
    (1, 15): True,  
    (1, 16): True,  
    (1, 17): True,  
    (1, 18): True, 
    (1, 19): True,  
    (1, 20): True, 
    (1, 24): True,  
    (1, 25): True,  
    (2, 0): True,
    (2, 1): True,
    (2, 2): True,
    (2, 8): True,
    (2, 9): True,
    (2, 11): True,
    (3, 0): True,
    (3, 1): True,
    (3, 2): True,
    (3, 3): True,
    (3, 4): True,
    (9, 5): True,
    (9, 2): True,
    (9, 1): True,
    (9, 0): True,
    (8, 2): True,
    (8, 1): True,
    (7, 4): True,
    (7, 3): True,
    (7, 2): True,
    (7, 1): True,
    (6, 0): True,
    (5, 22): True,
    (5, 21): True,
    (5, 20): True,
    (5, 17): True,
    (5, 16): True,
    (5, 15): True,
    (5, 14): True,
    (5, 12): True,
    (5, 11): True,
    (5, 10): True,
    (5, 9): True,
    (5, 8): True,
    (5, 7): True,
    (5, 6): True,
    (5, 5): True,
    (5, 4): True,
    (5, 3): True,
    (5, 2): True,
    (5, 1): True,
    (5, 0): True,
    (4, 0): True,
    (4, 1): True,
    (4, 3): True,
    (4, 4): True,
    (4, 5): True,
    (4, 6): True,
    (4, 7): True,
    (4, 8): True,
    (4, 9): True,
    (4, 10): True,
    (4, 11): True,
    (4, 12): True,
    (4, 14): True,
    (4, 15): True,
    (4, 16): True,
    (4, 18): True,

}

PAGE_SIZE = 5

# ——— 2. Клавиатуры ——————————————————————————

def create_reasons_keyboard(task_number: str, page: int) -> InlineKeyboardMarkup:
    total = len(REASONS)
    pages = ceil(total / PAGE_SIZE)
    start = page * PAGE_SIZE
    items = REASONS[start : start + PAGE_SIZE]

    rows = []
    # строки с причинами
    for idx, reason in enumerate(items, start=start):
        rows.append([
            InlineKeyboardButton(
                text=reason,
                callback_data=f"select_reason:{task_number}:{idx}"
            )
        ])

    # навигация
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text = "⬅️", callback_data=f"reason_prev:{task_number}:{page-1}"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text = "➡️", callback_data=f"reason_next:{task_number}:{page+1}"))
    if nav:
        rows.append(nav)

    # кнопка отмены
    rows.append([
        InlineKeyboardButton(text = "Отменить", callback_data="cancel_close_task")
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)

@close_router.callback_query(F.data.startswith("reason_prev:") | F.data.startswith("reason_next:"))
async def _reason_change_page(query: CallbackQuery):
    # callback_data: "reason_prev:{task_number}:{new_page}"
    _, task_number, page_str = query.data.split(":")
    page = int(page_str)

    kb = create_reasons_keyboard(task_number, page)
    # Если у вас текст в сообщении не меняется, редактируем только разметку:
    await query.message.edit_reply_markup(reply_markup=kb)
    await query.answer()

def create_subreasons_keyboard(task_number: str, reason_idx: int, page: int) -> InlineKeyboardMarkup:
    items = SUBREASONS.get(reason_idx, [])
    total = len(items)
    pages = ceil(total / PAGE_SIZE)
    start = page * PAGE_SIZE
    chunk = items[start : start + PAGE_SIZE]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{chunk[i]}",
                callback_data=f"select_subreason:{task_number}:{reason_idx}:{start + i}"
            )
        ] for i in range(len(chunk))
    ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text = "⬅️", callback_data=f"subreason_prev:{task_number}:{reason_idx}:{page-1}"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text = "➡️", callback_data=f"subreason_next:{task_number}:{reason_idx}:{page+1}"))
    if nav:
        kb.inline_keyboard.append(nav)

    kb.inline_keyboard.append([
        InlineKeyboardButton(text = "Назад к причинам", callback_data=f"back_to_reasons:{task_number}:0")
    ])
    return kb

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

def create_avr_keyboard(task_number: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Генерация",
                callback_data=f"avr_generation:{task_number}"
            ),
            InlineKeyboardButton(
                text="Другое",
                callback_data=f"avr_other:{task_number}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отменить",
                callback_data="cancel_close_task"
            )
        ],
    ])

# ——— 3. Роутеры ————————————————————————————

# Старт: нажали «Закрыть заявку»
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
        # оригинальная логика
        await cb.message.edit_text(
            message_text,
            reply_markup=create_reasons_keyboard(task_number, 0)
        )

    elif work_type == "АВР":
        # специальная AVR-логика
        await cb.message.edit_text(
            message_text,
            reply_markup=create_avr_keyboard(task_number)
        )
    await cb.answer()

@close_router.callback_query(F.data.startswith("select_reason:"))
async def select_reason(cb: CallbackQuery, state: FSMContext):
    _, task_number, reason_idx = cb.data.split(":")
    await state.update_data(task_number=task_number, reason_idx=int(reason_idx))
    await cb.message.edit_text(
        f"Категория: <b>{REASONS[int(reason_idx)]}</b>\nВыберите подпункт:",
        parse_mode="HTML",
        reply_markup=create_subreasons_keyboard(task_number, int(reason_idx), 0)
    )
    await cb.answer()

@close_router.callback_query(F.data.startswith("avr_generation:"))
async def avr_generation(cb: CallbackQuery):
    task_number = cb.data.split(":",1)[1]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # При генерации нет количества, передаём 0
    db.close_task_by_worker(task_number, now_str, 0, "Генерация")
    await cb.message.edit_text(
        f"Заявка №{task_number} закрыта (код: Генерация)",
        reply_markup=main_menu()
    )
    await cb.answer("Заявка закрыта с кодом «Генерация»")

@close_router.callback_query(F.data.startswith("avr_other:"))
async def avr_other(cb: CallbackQuery):
    task_number = cb.data.split(":",1)[1]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.close_task_by_worker(task_number, now_str, 0, "Другое")
    await cb.message.edit_text(
        f"Заявка №{task_number} закрыта (код: Другое)",
        reply_markup=main_menu()
    )
    await cb.answer("Заявка закрыта с кодом «Другое»")

@close_router.callback_query(F.data.startswith("select_subreason:"))
async def select_subreason(cb: CallbackQuery, state: FSMContext):
    _, task_number, reason_idx, sub_idx = cb.data.split(":")
    reason_idx, sub_idx = int(reason_idx), int(sub_idx)
    sub = SUBREASONS[reason_idx][sub_idx]
    close_code = sub.split(maxsplit=1)[0]
    await state.update_data(
        task_number=task_number,
        subreason=sub,
        close_code=close_code,
        sub_idx=sub_idx,
        reason_idx=reason_idx,
    )
    if REQUIRES_AMOUNT.get((reason_idx, sub_idx), False):
        await state.set_state(CloseTaskSG.waiting_for_amount)
        await cb.message.edit_text(
            f"<b>{sub}</b>\n\nВведите количество (числом):",
            parse_mode="HTML"
        )
    else:
        await state.set_state(CloseTaskSG.waiting_for_confirmation)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_close")],
            [InlineKeyboardButton(text="Отменить",  callback_data="cancel_close_task")]
        ])
        await cb.message.edit_text(
            f"Подпункт: <b>{sub}</b>\nКод закрытия: <code>{close_code}</code>",
            parse_mode="HTML",
            reply_markup=kb
        )
    await cb.answer()

# обработка ввода количества
@close_router.message(CloseTaskSG.waiting_for_amount)
async def process_amount(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        return await msg.reply("Пожалуйста, введите целое число.")
    amount = int(msg.text)
    data = await state.update_data(amount=amount)
    # переходим к подтверждению
    await state.set_state(CloseTaskSG.waiting_for_confirmation)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_close")],
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_close_task")]
    ])
    await msg.answer(
        f"Подпункт: <b>{data['subreason']}</b>\n"
        f"Количество: {amount}",
        parse_mode="HTML",
        reply_markup=kb
    )

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

    # передаём в БД только цифро-точечный код
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