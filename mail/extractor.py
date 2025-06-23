import re

def extract_important_info(text):
    KEYWORDS = {
        "Номер задания": "task_number",
        "Номер БС": "bs_number",
        "Статус": "status",
        "Дата/Время выдачи задания": "issue_datetime",
        "Дата/Время прибытия на объект необходимое": "arrival_datetime",
        "Дата/Время завершения работ": "finish_datetime",
        "Тип работ": "work_type",
        "Краткое описание работ": "short_description",
        "Описание работ": "description",
        "Примечание/Комментарии": "comments",
        "Адрес": "address",
        "Ответственный Tele2": "responsible_person",
    }

    # создаём результирующий словарь со всеми полями по умолчанию пустыми
    extracted = {v: "" for v in KEYWORDS.values()}

    # для каждого ключа ищем блок текста до следующего ключа или до конца
    for key, field in KEYWORDS.items():
        # (?ms) — re.MULTILINE + re.DOTALL: ^ и $ работают на линию, а . ловит переводы строк
        pattern = rf"(?ms)^{re.escape(key)}\s*:\s*(.*?)(?=^\S.*?:|\Z)"
        m = re.search(pattern, text)
        if not m:
            continue
        value = m.group(1).strip()  # убираем лишние пробелы и переносы

        # если значение «None» или пусто — считаем его пустым
        if not value or value.lower() == "none":
            value = ""
        # нормализуем WO номер
        elif field == "task_number":
            value = re.sub(r"(\w+)\s+(\d+)", r"\1\2", value)
        # нормализуем даты в формате «YYYY-MM-DD HH:MM:SS»
        value = re.sub(
            r"(\d{2,4}-\d{2}-\d{2})\s+(\d{2}):(\d{2}):(\d{2})",
            r"\1 \2:\3:\4",
            value,
        )

        extracted[field] = value

    return extracted
