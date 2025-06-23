import imaplib
import email
import re
import asyncio
import pytz
from datetime import datetime, timedelta
from email.header import decode_header
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from config import mail_imap, mail_login, mail_password, check_mail_interval
from mail.extractor import extract_important_info
from db import db
from keyboards.menu import send_to_topic_button

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
                            status_match = re.search(r"\((.*?)\)", subject)
                            status_text = status_match.group(1) if status_match else "Неизвестно"
                            print(sender)
                            print(status_text)
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    print("Content-Type:", part.get_content_type())
                                    print("Content-Transfer-Encoding:", part.get("Content-Transfer-Encoding"))
                                    print("Content-Disposition:", part.get("Content-Disposition"))
                                    print("Charset:", part.get_content_charset())
                                    ctype = part.get_content_type()
                                    disp = str(part.get("Content-Disposition") or "").lower()
                                    charset = part.get_content_charset() or "utf-8"
                                    if ctype == "text/html" and "attachment" not in disp:
                                        payload = part.get_payload(decode=True)
                                        html = payload.decode(charset, errors="ignore")
                                        body = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
                                        break
                                    elif ctype == "text/plain" and "attachment" not in disp and not body:
                                        payload = part.get_payload(decode=True)
                                        body = payload.decode(charset, errors="ignore")
                                        
                            else:
                                payload = msg.get_payload(decode=True)
                                charset = msg.get_content_charset() or "utf-8"
                                body = payload.decode(charset, errors="ignore")

                            info = extract_important_info(body)
                            info["status"] = status_text
                                
                            existing_task = db.get_task_status(info["task_number"])
                            if existing_task:
                                if info["status"] in ["Закрыта", "Закрыто"]:
                                    if info["status"] == "Закрыто" :
                                        info["status"] = "Закрыта"
                                    if existing_task[0] not in ["Закрыта"]:
                                        supervisors = db.get_all_supervisors()
                                        db.close_task(info["status"], info["finish_datetime"], info["task_number"])
                                        text = f"Заявка <code>{info['task_number']}</code>, на <b>б/c - {info['bs_number']}</b> обновлена, статус: <b>{info['status']}</b>."
                                        for supervisor in supervisors:
                                            supervisor_id = supervisor[0]
                                            await bot.send_message(supervisor_id, text)
                                        worker = db.get_task_by_number(info["task_number"])
                                        if worker and len(worker) > 4 and worker[4]:
                                            await bot.send_message(worker[4], text)
                                if info["status"] in ["Отмена", "Отменено"]:
                                    if info["status"] == "Отменено":
                                        info["status"] = "Отмена"
                                    if existing_task[0] not in ["Отмена"]:
                                        db.close_task(info["status"], info["finish_datetime"], info["task_number"])
                                        text = f"Заявка <code>{info['task_number']}</code>, на <b>б/c - {info['bs_number']}</b> обновлена, статус: <b>{info['status']}</b>."
                                        worker = db.get_task_by_number(info["task_number"])
                                        if worker and len(worker) > 4 and worker[4]:
                                            await bot.send_message(worker[4], text)
                                        supervisors = db.get_all_supervisors()
                                        for supervisor in supervisors:
                                            supervisor_id = supervisor[0]
                                            await bot.send_message(supervisor_id, f"Новая заявка \n <code>{info['task_number']}</code>\nНа б/с - <b>{info['bs_number']}</b>, сразу {info['status']}.")
                            else:
                                if info["status"] in ["Закрыта", "Отмена", "Закрыто", "Отменено", "Не выполнено подрядчиком", "Выдано ошибочно"]:
                                    if info["status"] == "Отменено" :
                                        info["status"] = "Отмена"
                                    elif info["status"] == "Закрыто":
                                        info["status"] = "Закрыта"
                                    db.add_task(
                                        info["task_number"], info["bs_number"], info["status"], None,
                                        info["issue_datetime"], info["arrival_datetime"], None, info["finish_datetime"],
                                        info["work_type"], info["description"], info["short_description"],
                                        info["comments"], info["address"], info["responsible_person"]
                                    )
                                    supervisors = db.get_all_supervisors()
                                    for supervisor in supervisors:
                                        supervisor_id = supervisor[0]
                                        await bot.send_message(supervisor_id, f"Новая заявка \n <code>{info['task_number']}</code>\nНа б/с - <b>{info['bs_number']}</b>,  сразу {info['status']}.")

                                elif info["status"] in ["Новое","В работе","Новая"]:
                                    encode = quote_plus(info['address'])
                                    url = f"https://yandex.ru/maps/?text={encode}"
                                    message_text = (
                                        f"<b>ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤНовое задание!</b>\n\n"
                                        f"<b>Номер задания:</b> <code>{info['task_number']}</code>\n"
                                        f"<b>Номер БС:</b> {info['bs_number']}\n"
                                        f"<b>Статус:</b> Новое\n"
                                        f"<b>Дата выдачи:</b> {info['issue_datetime']}\n"
                                        f"<b>Время прибытия:</b> {info['arrival_datetime']}\n"
                                        f"<b>Тип работ:</b> {info['work_type']}\n"
                                        f"<b>Краткое описание работ:</b> {info['short_description']}\n"
                                        f"<b>Описание работ:</b> {info['description']}\n"
                                        f"<b>Примечание / Комментарии:</b> {info['comments']}\n"
                                        f'<b>Адрес:</b> <a href="{url}">{info["address"]}</a>\n'
                                        f"<b>Ответственный:</b> {info['responsible_person']}\n"
                                    )
                                    supervisors = db.get_all_supervisors()
                                    for supervisor in supervisors:
                                        supervisor_id = supervisor[0]
                                        sent = await bot.send_message(supervisor_id, message_text, parse_mode="HTML", reply_markup = send_to_topic_button(info["task_number"]))
                                        db.save_sent_message(info["task_number"], supervisor_id, sent.message_id)
                                    db.add_task(
                                        info["task_number"], info["bs_number"], "Новое", None,
                                        info["issue_datetime"], info["arrival_datetime"], None, None,
                                        info["work_type"], info["description"], info["short_description"],
                                        info["comments"], info["address"], info["responsible_person"]
                                    )
            mail.close()
            mail.logout()
        except Exception as e:
            print(f"Ошибка при проверке почты: {e}")

        await asyncio.sleep(check_mail_interval)