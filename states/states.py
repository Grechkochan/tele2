from aiogram.fsm.state import StatesGroup, State

class Registration(StatesGroup):
    waiting_for_password = State()
    full_name = State()
    phone = State()
    city = State()
    
class TaskPagination(StatesGroup):
    page = State()

class PaginationState(StatesGroup):
    current_page = State()
    tasks = State()
    role = State()

class DatePicker(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()

class SearchState(StatesGroup):
    waiting_for_task_number = State()

class CloseTaskSG(StatesGroup):
    choosing_ppr       = State()  
    waiting_for_amount = State()  
    confirming_ppr     = State()