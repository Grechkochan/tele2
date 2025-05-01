from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states.states import Registration
from db import db
from keyboards.menu import get_phone, main_menu, reply_main_menu
from aiogram.types import ReplyKeyboardRemove
register_router = Router()

@register_router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return

    if db.check_worker(message.from_user.id):
        await message.answer("Ты уже зарегистрировался!", reply_markup=reply_main_menu())
    else:
        await state.set_state(Registration.waiting_for_password)
        await state.update_data(telegram_id=message.from_user.id, password_attempts=0)
        await message.answer("Введите пароль для регистрации:")

@register_router.message(F.text == "Главное меню")
async def show_main_menu(message: Message):
    await message.answer("Главное меню", reply_markup=main_menu())

@register_router.message(Registration.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    data = await state.get_data()
    attempts = data.get("password_attempts", 0)

    if message.text.strip() == "1058":
        await state.set_state(Registration.full_name)
        await state.update_data(telegram_id=message.from_user.id)
        await message.answer("Пароль принят! Теперь напиши своё ФИО:")
    else:
        attempts += 1
        await state.update_data(password_attempts=attempts)

        if attempts >= 3:
            await state.clear()
            await message.answer("Превышено количество попыток. Попробуйте позже.")
        else:
            await message.answer(f"Неверный пароль.")


@register_router.message(Registration.full_name)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Теперь отправь свой номер телефона (или нажми кнопку ниже):", reply_markup=get_phone())
    await state.set_state(Registration.phone)


@register_router.message(F.Contact, Registration.phone)
async def get_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Введи город, в котором ты живёшь:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Registration.city)

@register_router.message(Registration.phone)
async def get_phone_manual(message: Message, state: FSMContext):
    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text:
        phone_number = message.text
    else:
        await message.answer("Пожалуйста, введите номер телефона.")
        return
    cleaned = phone_number.replace("+", "").replace(" ", "")
    if cleaned.isdigit() and 10 <= len(cleaned) <= 12:
        await state.update_data(phone=cleaned)
        await message.answer("Введи город, в котором ты живёшь:")
        await state.set_state(Registration.city)
    else:
        await message.answer("Пожалуйста, введи корректный номер телефона (только цифры, от 10 до 12 символов).")


@register_router.message(Registration.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()
    db.add_worker(
        data["telegram_id"],
        data["full_name"],
        data["phone"],
        data["city"],
        "Worker"
    )
    await message.answer(" Регистрация завершена! Спасибо!", reply_markup=main_menu())
    await state.clear()