import re

def extract_important_info(text):
    # Алиасы ключей → поля
    FIELD_ALIASES = {
        "Номер задания": "task_number",
        "Номер БС": "bs_number",
        "Статус": "status",
        "Дата выдачи": "issue_datetime",
        "Дата/Время выдачи задания": "issue_datetime",
        "Время прибытия": "arrival_datetime",
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
