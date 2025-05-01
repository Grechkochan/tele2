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

    extracted_info = {}
    text = re.sub(r":\s*\n*\s*", ": ", text)

    for line in text.split("\n"):
        line = line.strip()
        if ":" in line:
            for keyword, key in KEYWORDS.items():
                if keyword in line:
                    key_value = line.split(":", 1)
                    value = key_value[1].strip() if len(key_value) > 1 else " "

                    if key == "task_number":
                        value = re.sub(r"(\w+)\s+(\d+)", r"\1\2", value)

                    value = re.sub(r"(\d{2,4}-\d{2}-\d{2})\s+(\d{2})\s*:\s*(\d{2})\s*:\s*(\d{2})", r"\1 \2:\3:\4", value)

                    extracted_info[key] = value

    return extracted_info