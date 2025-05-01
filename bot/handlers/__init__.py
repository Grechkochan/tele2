from aiogram import Router
from .start import register_router as start_router
from .accepttask import accept_router as accept_router
from .acceptedtasks import menu_router as menu_router
from .newtasks import new_tasks_router 
from .statistics import statistics_router
from .mainmenu import mainmenuer
from .tasksearch import search_router

router = Router()
router.include_router(start_router)
router.include_router(accept_router)
router.include_router(menu_router)
router.include_router(new_tasks_router)
router.include_router(statistics_router)
router.include_router(mainmenuer)
router.include_router(search_router)
