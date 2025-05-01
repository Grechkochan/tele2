import imaplib
import email
import re
import asyncio
import pytz
from datetime import datetime, timedelta
from email.header import decode_header
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from config import mail_imap, mail_login, mail_password, check_mail_interval, group_id, noc
from mail.extractor import extract_important_info
from db import db
from keyboards.menu import accept_task

async def check_mail(bot):
    while True:
        try:
            mail = imaplib.IMAP4_SSL(mail_imap)
            mail.login(mail_login, mail_password)
            mail.select("inbox")

            tz = pytz.timezone("Europe/Moscow")
            now = datetime.now(tz)
            minutes_ago = now - timedelta(minutes=20)

            since_time = minutes_ago.strftime("%d-%b-%Y")
            
            print(f"Проверяем почту с {since_time}")
            
            status, messages = mail.search(None, "UNSEEN")
            mail_ids = messages[0].split()

            for mail_id in mail_ids:
                status, msg_data = mail.fetch(mail_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        date_str = msg["Date"]
                        msg_date = email.utils.parsedate_tz(date_str)
                        msg_date = datetime.fromtimestamp(email.utils.mktime_tz(msg_date), tz)

                        if msg_date >= minutes_ago:
                            sender = msg["From"]
                            subject_parts = decode_header(msg["Subject"])
                            subject = " ".join(
                                part.decode(encoding or "utf-8", errors="ignore") if isinstance(part, bytes) else part
                                for part, encoding in subject_parts
                            )

                            print(f"Получено письмо от: {sender}, Тема: {subject}")
                            if noc != sender:
                                print(f"Пропускаем письмо от: {sender}")
                                continue
                            status_match = re.search(r"\((.*?)\)", subject)
                            status_text = status_match.group(1) if status_match else "Неизвестно"

                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition"))

                                    if content_type == "text/plain" and "attachment" not in content_disposition:
                                        payload = part.get_payload(decode=True)
                                        charset = part.get_content_charset()
                                        body = payload.decode(charset or "utf-8", errors="ignore")
                                        break
                                    elif content_type == "text/html" and not body:
                                        payload = part.get_payload(decode=True)
                                        charset = part.get_content_charset()
                                        html_body = payload.decode(charset or "utf-8", errors="ignore")

                                        soup = BeautifulSoup(html_body, "html.parser")
                                        body = soup.get_text(separator="\n", strip=True)
                            else:
                                payload = msg.get_payload(decode=True)
                                charset = msg.get_content_charset()
                                body = payload.decode(charset or "utf-8", errors="ignore")

                            info = extract_important_info(body)
                            info["status"] = status_text

                            existing_task = db.get_task_status(info["task_number"])
                            if existing_task:
                                if info["status"] in ["Закрыта", "Отмена", "Закрыто", "Отменено"]:
                                    if existing_task[0] not in ["Закрыта", "Отмена"]:
                                        supervisors = db.get_all_supervisors()
                                        db.close_task(info["status"], info["finish_datetime"], info["task_number"])
                                        for supervisor in supervisors:
                                            supervisor_id = supervisor[0]
                                            await bot.send_message(supervisor_id, f"Заявка <code>{info['task_number']}</code>, на <b>б/c - {info['bs_number']}</b> обновлена, статус: <b>{info['status']}</b>.")
                            else:
                                if info["status"] in ["Закрыта", "Отмена", "Закрыто", "Отменено"]:
                                    db.add_task(
                                        info["task_number"], info["bs_number"], info["status"], None,
                                        info["issue_datetime"], None, info["finish_datetime"],
                                        info["work_type"], info["description"], info["short_description"],
                                        info["comments"], info["address"], info["responsible_person"]
                                    )
                                    supervisors = db.get_all_supervisors()
                                    for supervisor in supervisors:
                                        supervisor_id = supervisor[0]
                                        await bot.send_message(supervisor_id, f"Новая заявка \n <code>{info['task_number']}</code>\nНа б/с - <b>{info['bs_number']}</b>,  сразу отменилась.")
                                elif info["status"] == "Новое":
                                    encode = quote_plus(info['address'])
                                    url = f"https://yandex.ru/maps/?text={encode}"
                                    message_text = (
                                        f"<b>ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤНовое задание!</b>\n\n"
                                        f"<b>Номер задания:</b> <code>{info['task_number']}</code>\n"
                                        f"<b>Номер БС:</b> {info['bs_number']}\n"
                                        f"<b>Статус:</b> {info['status']}\n"
                                        f"<b>Дата выдачи:</b> {info['issue_datetime']}\n"
                                        f"<b>Время прибытия:</b> {info['arrival_datetime']}\n"
                                        f"<b>Тип работ:</b> {info['work_type']}\n"
                                        f"<b>Краткое описание работ:</b> {info['short_description']}\n"
                                        f"<b>Описание работ:</b> {info['description']}\n"
                                        f"<b>Примечание / Комментарии:</b> {info['comments']}\n"
                                        f'<b>Адрес:</b> <a href="{url}">{info["address"]}</a>\n'
                                        f"<b>Ответственный:</b> {info['responsible_person']}\n"
                                        f"<b>Для подтверждения принятия WO в работу отправьте на номер 359 СМС с текстом:</b> "
                                        f"<code>#107*{info['task_number'].replace('T2','')}#</code>\n"
                                    )
                                    supervisors = db.get_all_supervisors()
                                    for supervisor in supervisors:
                                        supervisor_id = supervisor[0]
                                        await bot.send_message(supervisor_id, message_text, parse_mode="HTML")
                                    db.add_task(
                                        info["task_number"], info["bs_number"], info["status"], None,
                                        info["issue_datetime"], None, None,
                                        info["work_type"], info["description"], info["short_description"],
                                        info["comments"], info["address"], info["responsible_person"]
                                    )
                                    topicid = db.get_topic_id_by_sitename(info["bs_number"])
                                    try:
                                        topicid = int(topicid[0])
                                    except (TypeError, ValueError, IndexError):
                                        topicid = 2
                                    await bot.send_message(
                                        group_id, message_text, parse_mode="HTML",
                                        reply_markup=accept_task(info['task_number']), message_thread_id=topicid
                                    )

            mail.close()
            mail.logout()
        except Exception as e:
            print(f"Ошибка при проверке почты: {e}")

        await asyncio.sleep(check_mail_interval)