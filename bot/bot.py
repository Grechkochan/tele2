import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import token
from mail.checker import check_mail
from bot.handlers import router

async def _on_startup(bot: Bot) -> None:
    # запускаем вашу проверку почты в фоне
    asyncio.create_task(check_mail(bot))

def main():
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # регистрируем хук запуска
    dp.startup.register(_on_startup)  # :contentReference[oaicite:0]{index=0}

    # стартуем polling
    dp.run_polling(bot, skip_updates=True)
