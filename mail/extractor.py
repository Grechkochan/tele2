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

    # создаём словарь со всеми полями сразу, по умолчанию — пустые строки
    extracted_info = {v: "" for v in KEYWORDS.values()}

    # приводим в единый вид « / » и « :»
    text = re.sub(r"\s*/\s*", "/", text)
    text = re.sub(r"\s*:\s*", ":", text)

    for line in text.splitlines():
        line = line.strip()
        if ":" not in line:
            continue

        raw_key, raw_value = line.split(":", 1)
        raw_key = raw_key.strip()
        raw_value = raw_value.strip()

        # пропускаем, если после ':' нет никакого значения
        if not raw_value:
            continue

        for keyword, key in KEYWORDS.items():
            if raw_key == keyword:
                value = raw_value

                # «None» → пустая строка
                if value.lower() == "none":
                    value = ""

                # склеиваем «WO 1234» → «WO1234»
                if key == "task_number":
                    value = re.sub(r"(\w+)\s+(\d+)", r"\1\2", value)

                # унифицируем формат даты «YYYY-MM-DD HH:MM:SS»
                value = re.sub(
                    r"(\d{2,4}-\d{2}-\d{2})\s+(\d{2}):(\d{2}):(\d{2})",
                    r"\1 \2:\3:\4",
                    value,
                )

                extracted_info[key] = value
                break

    return extracted_info