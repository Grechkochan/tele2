from aiogram.types import CallbackQuery
from aiogram import F, Router
from keyboards.menu import main_menu

mainmenuer = Router()

@mainmenuer.callback_query(F.data == "Main_Menu")
async def mainmenu(callback_query: CallbackQuery):
    await callback_query.message.edit_text("Главное меню:", reply_markup=main_menu())