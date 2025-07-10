import imaplib
import email
import re
import asyncio
from email.header import decode_header
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from config import mail_imap, mail_login, mail_password, check_mail_interval, group_id
from mail.extractor import extract_important_info, extract_important_info_resp
from db import db
from keyboards.menu import send_to_topic_button
from email.utils import parseaddr

async def check_mail(bot):
    while True:
        try:
            mail = imaplib.IMAP4_SSL(mail_imap)
            mail.login(mail_login, mail_password)
            mail.select("inbox")
            status, messages = mail.search(None, "UNSEEN")
            mail_ids = messages[0].split()
            for mail_id in mail_ids:
                status, msg_data = mail.fetch(mail_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        sender = msg["From"]
                        subject_parts = decode_header(msg["Subject"])
                        subject = " ".join(
                                part.decode(encoding or "utf-8", errors="ignore") if isinstance(part, bytes) else part
                                for part, encoding in subject_parts
                        )
                        print(repr(sender))
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
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
                        sender_email = parseaddr(sender)[1].lower()
                        is_noc = (sender_email == "noc.rostov@info.t2.ru")
                        extract = extract_important_info if is_noc else extract_important_info_resp
                        info = extract(body)
                        if is_noc:
                            match = re.search(r"\((.*?)\)", subject)
                            if match:
                                info["status"] = match.group(1)
                            else:
                                info.pop("status", None)
                        if info["status"] in {"Закрыта", "Закрыто"}:
                            info["status"] = "Закрыта"
                        elif info["status"] in {"Отменено", "Отмена"}:
                            info["status"] = "Отмена"
                        task_exists = db.get_task_status(info["task_number"])
                        if info["status"] in ["Новое", "Новая", "В работе"]:
                            if not task_exists:
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
                                    sent = await bot.send_message(supervisor_id, message_text, parse_mode="HTML", reply_markup=send_to_topic_button(info["task_number"]))
                                    db.save_sent_message(info["task_number"], supervisor_id, sent.message_id)
                                db.add_task(
                                    info["task_number"], info["bs_number"], "Новое", None,
                                    info["issue_datetime"], info["arrival_datetime"], None, None,
                                    info["work_type"], info["description"], info["short_description"],
                                    info["comments"], info["address"], info["responsible_person"]
                                )
                        else:
                            text = f"Заявка <code>{info['task_number']}</code>, на <b>б/c - {info['bs_number']}</b> обновлена, статус: <b>{info['status']}</b>."
                            if task_exists:
                                db.close_task(info["status"], info["finish_datetime"], info["task_number"])
                                supervisors = db.get_all_supervisors()
                                for supervisor in supervisors:
                                    supervisor_id = supervisor[0]
                                    await bot.send_message(supervisor_id, text)
                                worker = db.get_task_by_number(info["task_number"])
                                if worker and len(worker) > 4 and worker[4]:
                                    await bot.send_message(int(worker[4]), text)
                                sent_info = db.ifsent(info["task_number"])
                                if sent_info:
                                    topic_id = db.get_topic_id_by_sitename(info["bs_number"])
                                    try:
                                        topicid = int(topic_id[0])
                                    except (TypeError, ValueError, IndexError):
                                        topicid = 2
                                    if topic_id:
                                        await bot.send_message(chat_id = group_id, text = text, message_thread_id=int(topicid))
                            else:
                                db.add_task(
                                    info["task_number"], info["bs_number"], info["status"], None,
                                    info["issue_datetime"], info["arrival_datetime"], None, info["finish_datetime"],
                                    info["work_type"], info["description"], info["short_description"],
                                    info["comments"], info["address"], info["responsible_person"]
                                )
                                text = f"Новая заявка \n<code>{info['task_number']}</code>\nНа б/с - <b>{info['bs_number']}</b>, сразу закрылась со статусом: {info['status']}."
                                supervisors = db.get_all_supervisors()
                                for supervisor in supervisors:
                                    supervisor_id = supervisor[0]
                                    await bot.send_message(supervisor_id, text)
            mail.close()
            mail.logout()
        except Exception as e:
            print(f"Ошибка при проверке почты: {e}")

        await asyncio.sleep(check_mail_interval)