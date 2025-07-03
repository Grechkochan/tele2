import re
from datetime import datetime
from typing import Dict, Optional

def extract_important_info(text):
    # Алиасы ключей → поля
    FIELD_ALIASES = {
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
        "Примечание / Комментарии": "comments",
        "Адрес": "address",
        "Координаты": "coordinates",
        "Подрядная организация": "contractor",
        # НЕ добавляем сюда "Ответственный"!
    }

    # Инициализируем результат
    extracted = {field: "" for field in set(FIELD_ALIASES.values()) | {"responsible_person"}}

    # Собираем общий паттерн по всем алиасам
    aliases = "|".join(re.escape(k) for k in FIELD_ALIASES)
    main_re = re.compile(
        rf"(?P<key>{aliases})\s*:\s*(?P<value>.*?)(?=(?:\n\S)|\Z)",
        re.DOTALL
    )

    # 1. Проходим по всему тексту и вытаскиваем значения по алиасам
    for m in main_re.finditer(text):
        key = m.group("key")
        field = FIELD_ALIASES[key]
        val = m.group("value").strip()
        if not val or val.lower() == "none":
            continue
        # Нормализация номера
        if field == "task_number":
            val = re.sub(r"(\w+)\s+(\d+)", r"\1\2", val)
        # Нормализация дат
        val = re.sub(
            r"(\d{2,4}-\d{2}-\d{2})\s+(\d{2}):(\d{2}):(\d{2})",
            r"\1 \2:\3:\4",
            val
        )
        extracted[field] = val

    # 2. Убираем из comments чистую подстроку "Ответственный Tele2:" если она там есть
    if extracted["comments"]:
        extracted["comments"] = re.sub(
            r"(?m)^\s*Ответственный(?: Tele2)?:\s*$",
            "",
            extracted["comments"]
        ).strip()

    # 3. Вытаскиваем responsible_person отдельно
    m2 = re.search(
        r"^Ответственный(?: Tele2)?\s*:\s*(?P<resp>.+?)\s*(?=\n\S|\Z)",
        text,
        flags=re.MULTILINE
    )
    if m2:
        extracted["responsible_person"] = m2.group("resp").strip()

    return extracted

def extract_important_info_resp(text: str) -> Dict[str, Optional[datetime]]:
    result = {}

    mapping = {
        'Номер задания': 'task_number',
        'Номер БС': 'bs_number',
        'Статус': 'status',
        'Адрес': 'address',
        'Координаты': 'coordinates',
        'Дата / Время выдачи задания': 'issue_datetime',
        'Дата / Время прибытия на объект необходимое': 'arrival_datetime',
        'Дата / Время прибытия на объект фактическое': 'arrival_datetime_fact',
        'Дата / Время начала выполнения работ': 'start_datetime',
        'Дата / Время завершения работ': 'finish_datetime',
        'Тип работ': 'work_type',
        'Краткое описание работ': 'short_description',
        'Описание работ': 'description',
        'Подрядная организация': 'contractor_company',
        'Примечание / Комментарии': 'comments',
        'Проведенные работы': 'performed_work',
        'Ответственный Tele2': 'responsible_person',
        'Ответственный сотрудник подрядной организации': 'contractor',
        'Для подтверждения принятия WO в работу отправьте на номер 359 СМС с текстом': 'confirmation_sms'
    }

    datetime_keys = {
        'issue_datetime',
        'arrival_datetime',
        'arrival_datetime_fact',
        'start_datetime',
        'finish_datetime',
    }

    # Регулярка для даты в формате YYYY-MM-DD HH:MM:SS с возможными пробелами
    date_re = re.compile(r'(\d{4})\s*-\s*(\d{2})\s*-\s*(\d{2})\s+(\d{2})\s*:\s*(\d{2})\s*:\s*(\d{2})')

    for line in text.splitlines():
        line = line.strip()
        for raw_key, dict_key in mapping.items():
            if line.startswith(raw_key + " :") or line.startswith(raw_key + ":"):
                value = line[len(raw_key):].lstrip(" :").strip()

                if dict_key in datetime_keys and value:
                    # Ищем дату с помощью regex
                    match = date_re.search(value)
                    if match:
                        # Собираем чистую строку даты без пробелов внутри
                        date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:{match.group(5)}:{match.group(6)}"
                        try:
                            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                            result[dict_key] = dt
                        except Exception:
                            # если не распарсилось - просто сохраняем строку
                            result[dict_key] = value
                    else:
                        # если regex не нашёл дату, просто сохраняем
                        result[dict_key] = value if value else ""
                else:
                    result[dict_key] = value if value else ""
                break

    return result