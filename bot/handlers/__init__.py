from aiogram import Router
from .start import register_router as start_router
from .accepttask import accept_router as accept_router
from .acceptedtasks import menu_router as menu_router
from .newtasks import new_tasks_router 
from .statistics import statistics_router
from .mainmenu import mainmenuer
from .tasksearch import search_router
from .sendtask import send_router
from .closetask import close_router
from .createreport import report_router
from .denytask import deny_router

router = Router()
router.include_router(start_router)
router.include_router(accept_router)
router.include_router(menu_router)
router.include_router(new_tasks_router)
router.include_router(statistics_router)
router.include_router(mainmenuer)
router.include_router(search_router)
router.include_router(send_router)
router.include_router(close_router)
router.include_router(report_router)
router.include_router(deny_router)