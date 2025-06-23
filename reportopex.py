import warnings
# подавляем предупреждение openpyxl об «Unknown extension»
warnings.filterwarnings("ignore", "Unknown extension.*", UserWarning)

import sqlite3
import re
from datetime import datetime
from openpyxl import load_workbook
from typing import List, Tuple

# --- Параметры ---
TEMPLATE_PATH = "отчет.xlsx"       # ваш исходный шаблон
OUTPUT_PATH   = "OPEX_filled.xlsx" # куда сохранить
SHEET_NAME    = "Opex"             # лист с динамической частью
START_ROW     = 11                 # строка-шаблон с формулами
DB_PATH       = "db.db"            # путь к SQLite

SUMMARY_ROW = 14   # изначально формула стояла в AL14
SUMMARY_COL = 38   # AL


def fetch_tasks():
    """
    Берём из Tasks сразу ФИО исполнителя из Workers по JOIN по tgId.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT
            T.basestation,
            T.tasknum,
            T.status,
            COALESCE(W.workerFIO, '') AS workerFIO,
            T.datetime,
            T.datetimeacc,
            T.datetimeclose,
            T.responsible_person,
            T.close_code,
            T.work_type,
            T.quantity
        FROM Tasks AS T
        LEFT JOIN Workers AS W
          ON T.worker = W.tgId
        ORDER BY T.datetime
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_tasks_for_worker(worker_id: str, start_date: str, end_date: str):
    """
    Забираем задачи по конкретному работнику (worker_id = tgId) с ФИО.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT
            T.basestation,
            T.tasknum,
            T.status,
            COALESCE(W.workerFIO, '') AS workerFIO,
            T.datetime,
            T.datetimeacc,
            T.datetimeclose,
            T.responsible_person,
            T.close_code,
            T.work_type,
            T.quantity
        FROM Tasks AS T
        LEFT JOIN Workers AS W
          ON T.worker = W.tgId
        WHERE T.worker = ?
          AND date(T.datetimeclose) BETWEEN ? AND ?
        ORDER BY T.datetime
    """, (worker_id, start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_tasks_for_all(start_date: str, end_date: str) -> List[Tuple]:
    """
    Берём все задачи за период, сразу подтягивая ФИО исполнителя.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT
            T.basestation,
            T.tasknum,
            T.status,
            COALESCE(W.workerFIO, '') AS workerFIO,
            T.datetime,
            T.datetimeacc,
            T.datetimeclose,
            T.responsible_person,
            T.close_code,
            T.work_type,
            T.quantity
        FROM Tasks AS T
        LEFT JOIN Workers AS W
          ON T.worker = W.tgId
        WHERE date(T.datetimeclose) BETWEEN ? AND ?
        ORDER BY T.datetime
    """, (start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return rows

def collect_formulas(ws, row):
    formulas = {}
    for cell in ws[row]:
        if isinstance(cell.value, str) and cell.value.startswith("="):
            formulas[cell.column] = cell.value
    return formulas

def shift_formula(formula: str, offset: int) -> str:
    """
    Сдвигает все относительные ссылки вида A10, $B10, C$10
    на offset строк вниз, но НЕ трогает ссылки с закреплённой
    строкой, например $D$169.
    """
    def repl(m):
        col = m.group("col")   # захватывает и $ перед, и $ после буквы
        row = int(m.group("row"))
        # если после буквы есть $, значит строка фиксирована — не трогаем
        if col.endswith("$"):
            return f"{col}{row}"
        # иначе прибавляем смещение
        return f"{col}{row + offset}"

    pattern = re.compile(r"(?P<col>\$?[A-Z]+\$?)(?P<row>\d+)")
    return pattern.sub(repl, formula)

def parse_dt(val, default=None):
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(val, fmt)
            except:
                pass
        try:
            return datetime.fromisoformat(val)
        except:
            return default
    return default

def expand_task(rec):
    bs, num, status, worker, open_s, acc_s, close_s, resp, code, wtype, db_qty = rec

    # нормализуем статус
    status_l = (status or "").strip().lower()
    closed   = status_l.startswith("закр")     # «закрыто», «закрытие» и т.п.
    canceled = "отмен" in status_l 

    # если ни закрыто, ни отменено — пропускаем
    if not (closed or canceled):
        return []

    # парсим даты
    opened    = parse_dt(open_s)
    arrived   = parse_dt(acc_s, default=opened)
    closed_dt = parse_dt(close_s)
    if not opened or not closed_dt:
        return []

    def before_17(dt): return dt.hour < 17
    wtype_l = (wtype or "").strip().lower()

    out = []

    # ППР — только закрытые
    if wtype_l == "ппр":
        if closed:
            out.append((bs, num, opened, arrived, closed_dt,
                        worker, resp, code, None, db_qty))
        return out

    # АВР + генерация
    if wtype_l == "авр" and (code or "").strip().lower() == "генерация":
        if closed:
            total_h = (closed_dt - opened).total_seconds() / 3600
            n72 = int(total_h // 72)
            rem = total_h - n72 * 72
            n24 = int(rem // 24)
            h   = int(rem - n24 * 24)
            for part_code, qty in [("3.3.3.", n72), ("3.3.2.", n24), ("3.3.1.", h)]:
                if qty:
                    out.append((bs, num, opened, arrived, closed_dt,
                                worker, resp, part_code, qty, db_qty))
                    return out
    elif canceled:
        part_code = "3.4.1." if before_17(opened) else "3.4.2."
        out.append((bs, num, opened, arrived, closed_dt,
                worker, resp, part_code, None, db_qty))
    
        return out

    # Другое (и все прочие типы) — только закрытые
    if closed:
        diff_h = (closed_dt - arrived).total_seconds() / 3600
        b17    = before_17(arrived)
        if diff_h <= 5:
            part_code = "3.1.1." if b17 else "3.1.2."
            out.append((bs, num, opened, arrived, closed_dt,
                        worker, resp, part_code, None, db_qty))
            return out
        else:
            c1 = "3.1.1." if b17 else "3.1.2."
            c2 = "3.2.1." if b17 else "3.2.2."
            out.append((bs, num, opened, arrived, closed_dt,
                        worker, resp, c1, None, db_qty))
            out.append((bs, num, opened, arrived, closed_dt,
                        worker, resp, c2, None, db_qty))
        return out


    # 3) Другое (или любой тип, не ППР и не АВР)
    if wtype_l != "ппр" and not (wtype_l == "авр" and (code or "").lower() == "генерация"):
        # считаем по времени выполнения
        diff_h = (closed_dt - arrived).total_seconds() / 3600
        b17 = before_17(arrived)
        if diff_h <= 5:
            part_code = "3.1.1." if b17 else "3.1.2."
            out.append((bs, num, opened, arrived, closed_dt, worker, resp, part_code, None, db_qty))
            return out
        else:
            code1 = "3.1.1." if b17 else "3.1.2."
            code2 = "3.2.1." if b17 else "3.2.2."
            out.append((bs, num, opened, arrived, closed_dt, worker, resp, code1, None, db_qty))
            out.append((bs, num, opened, arrived, closed_dt, worker, resp, code2, None, db_qty))
        return out

    return out

def fill_report():
    wb = load_workbook(filename=TEMPLATE_PATH)
    ws = wb[SHEET_NAME]

    raw = fetch_tasks()
    tasks = []
    for rec in raw:
        tasks.extend(expand_task(rec))

    if not tasks:
        print("Нет задач для вставки.")
        return

    formulas = collect_formulas(ws, START_ROW)
    n = len(tasks)
    # вставляем новые строки
    ws.insert_rows(START_ROW + 1, amount=n)

    # заполняем
    for idx, (bs, num, opened, arrived, closed_dt, worker, resp, code, qty, db_qty) in enumerate(tasks, start=1):
        row = START_ROW + idx
        for col, f in formulas.items():
            ws.cell(row=row, column=col, value=shift_formula(f, idx))
        ws.cell(row=row, column=2,  value=bs)
        ws.cell(row=row, column=6,  value=num)
        ws.cell(row=row, column=7,  value=opened)
        ws.cell(row=row, column=8,  value=arrived)
        ws.cell(row=row, column=9,  value=closed_dt)
        ws.cell(row=row, column=10, value=worker)
        ws.cell(row=row, column=11, value=resp)
        ws.cell(row=row, column=12, value=code)
        ws.cell(row=row, column=15, value=db_qty)
        if code == "3.3.1." and qty is not None:
            ws.cell(row=row, column=17, value=qty)
        elif code == "3.3.2." and qty is not None:
            ws.cell(row=row, column=18, value=qty)
        elif code == "3.3.3." and qty is not None:
            ws.cell(row=row, column=19, value=qty)

    # --- обновляем итоговую формулу ---
    data_start   = START_ROW + 1        # первая строка с данными
    data_end     = START_ROW + n        # последняя вставленная
    new_sum_row  = SUMMARY_ROW + n      # куда сдвинулась формула
    ws.cell(row=new_sum_row, column=SUMMARY_COL).value = (
        f"=SUM(AL{data_start}:AL{data_end})"
    )

    wb.save(OUTPUT_PATH)
    print(f"Готово! Отчёт сохранён в {OUTPUT_PATH}")

def fill_report_for(worker_id: str, start_date: str, end_date: str, 
                    template: str = TEMPLATE_PATH, output: str = OUTPUT_PATH):
    """
    Генерирует report для одного рабочего и указанного интервала.
    Сохраняет в файл `output`.
    """
    wb = load_workbook(filename=template)
    ws = wb[SHEET_NAME]

    raw = fetch_tasks_for_worker(worker_id, start_date, end_date)
    tasks = []
    for rec in raw:
        tasks.extend(expand_task(rec))

    if not tasks:
        print("Нет задач для вставки.")
        return False

    # та же логика вставки строк и формул, что в fill_report()
    formulas = collect_formulas(ws, START_ROW)
    n = len(tasks)
    ws.insert_rows(START_ROW + 1, amount=n)
    for idx, (bs, num, opened, arrived, closed_dt, worker, resp,
              code, qty, db_qty) in enumerate(tasks, start=1):
        row = START_ROW + idx
        for col, f in formulas.items():
            ws.cell(row=row, column=col, value=shift_formula(f, idx))
        ws.cell(row=row, column=2,  value=bs)
        ws.cell(row=row, column=6,  value=num)
        ws.cell(row=row, column=7,  value=opened)
        ws.cell(row=row, column=8,  value=arrived)
        ws.cell(row=row, column=9,  value=closed_dt)
        ws.cell(row=row, column=10, value=worker)
        ws.cell(row=row, column=11, value=resp)
        ws.cell(row=row, column=12, value=code)
        ws.cell(row=row, column=15, value=db_qty)
        if code == "3.3.1." and qty is not None:
            ws.cell(row=row, column=17, value=qty)
        elif code == "3.3.2." and qty is not None:
            ws.cell(row=row, column=18, value=qty)
        elif code == "3.3.3." and qty is not None:
            ws.cell(row=row, column=19, value=qty)

    # обновляем итоговую формулу
    data_start  = START_ROW + 1
    data_end    = START_ROW + n
    sum_cell    = ws.cell(row=SUMMARY_ROW + n, column=SUMMARY_COL)
    sum_cell.value = f"=SUM(AL{data_start}:AL{data_end})"

    wb.save(output)
    print(f"Готово! Отчёт для {worker_id} сохранён в {output}")
    return True

def fill_report_for_all(start_date: str,
                        end_date:   str,
                        template:   str = TEMPLATE_PATH,
                        output:     str = OUTPUT_PATH) -> bool:
    """
    Генерирует Excel-отчёт по всем сотрудникам за заданный интервал.
    Возвращает True, если вставлено хотя бы одна запись, иначе False.
    """
    wb = load_workbook(filename=template)
    ws = wb[SHEET_NAME]

    raw = fetch_tasks_for_all(start_date, end_date)
    if not raw:
        # Нет записей за период
        return False
    
    # Развёртываем каждый кортеж в список строк отчёта
    tasks = []
    for rec in raw:
        tasks.extend(expand_task(rec))

    # Собираем формулы из шаблона
    formulas = collect_formulas(ws, START_ROW)

    # Вставляем нужное число строк под данные
    n = len(tasks)
    ws.insert_rows(START_ROW + 1, amount=n)

    # Заполняем каждую новую строку
    for idx, (bs, num, opened, arrived, closed_dt,
              worker, resp, code, qty, db_qty) in enumerate(tasks, start=1):
        row = START_ROW + idx
        # Сдвигаем и ставим формулы
        for col, f in formulas.items():
            ws.cell(row=row, column=col, value=shift_formula(f, idx))

        # Данные по колонкам (примерные индексы — подкорректируйте под ваш шаблон)
        ws.cell(row=row, column=2,  value=bs)
        ws.cell(row=row, column=6,  value=num)
        ws.cell(row=row, column=7,  value=opened)
        ws.cell(row=row, column=8,  value=arrived)
        ws.cell(row=row, column=9,  value=closed_dt)
        ws.cell(row=row, column=10, value=worker)
        ws.cell(row=row, column=11, value=resp)
        ws.cell(row=row, column=12, value=code)
        ws.cell(row=row, column=15, value=db_qty)
        if code == "3.3.1." and qty is not None:
            ws.cell(row=row, column=17, value=qty)
        elif code == "3.3.2." and qty is not None:
            ws.cell(row=row, column=18, value=qty)
        elif code == "3.3.3." and qty is not None:
            ws.cell(row=row, column=19, value=qty)

    # Обновляем итоговую формулу суммирования
    data_start = START_ROW + 1
    data_end   = START_ROW + n
    ws.cell(
        row=SUMMARY_ROW + n,
        column=SUMMARY_COL,
        value=f"=SUM(AL{data_start}:AL{data_end})"
    )

    # Сохраняем готовый отчёт
    wb.save(output)
    return True

if __name__ == "__main__":
    fill_report()
