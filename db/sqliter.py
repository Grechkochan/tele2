import sqlite3
from datetime import datetime, timedelta
conn = sqlite3.connect("db.db")
cursor = conn.cursor()

class SQLighter:

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def _create_sent_messages_table(self) -> None:
        """
        Создаёт таблицу sent_messages, если она ещё не существует.
        Хранит информацию о том, каким супервизорам (chat_id) и каким сообщением (message_id)
        была разослана каждая заявка (task_number).
        """
        with self.connection:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS `sent_messages` (
                    `id`           INTEGER PRIMARY KEY AUTOINCREMENT,
                    `task_number`  TEXT    NOT NULL,
                    `chat_id`      INTEGER NOT NULL,
                    `message_id`   INTEGER NOT NULL,
                    `sent_at`      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(`task_number`, `chat_id`, `message_id`)
                );
            """)

    def add_worker(self, tgId, WorkerFIO, phoneNumber, City, Position):
        with self.connection:
            self.cursor.execute("INSERT INTO `Workers` (`tgId`, `WorkerFIO`, `phoneNumber`, `City`, `Position` ) VALUES(?,?,?,?,?)",
                                (tgId, WorkerFIO, phoneNumber, City, Position))
            
    def add_task(self, tasknum, basestation, status, worker, issue_datetime, datetimeacc, datetimeclose,
             work_type, description, short_description, comments, address, responsible_person):
        with self.connection:
            self.cursor.execute(
                "INSERT INTO Tasks (tasknum, basestation, status, worker, datetime, datetimeacc, datetimeclose, "
                "work_type, description, short_description, comments, adress, responsible_person) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (tasknum, basestation, status, worker, issue_datetime, datetimeacc, datetimeclose,
                work_type, description, short_description, comments, address, responsible_person)
            )

    def add_closed_task(self,tasknum,status,finish_datetime):
        with self.connection:
            self.cursor.execute("INSERT INTO `Tasks` (`tasknum`, `status`, `datetimeclose`) VALUES(?,?,?)",
                                (tasknum, status,finish_datetime))

    def update_task(self,status,worker,datetime,tasknum):
        with self.connection:
            self.cursor.execute("""
                                UPDATE Tasks
                                SET status = ?, worker = ?, datetimeacc = ?
                                WHERE tasknum = ?
                            """, (status, worker, datetime, tasknum,))
            
            
    def close_task(self,status,finish_datetime, tasknum):
        with self.connection:
            self.cursor.execute("""
                                UPDATE Tasks
                                SET status = ?, datetimeclose = ?
                                WHERE tasknum = ?
                            """, (status, finish_datetime, tasknum,))
                                    
    def seek_worker(self,workerid):
        with self.connection:
            return self.cursor.execute("SELECT * FROM `Workers` Where `tgId` = ?",(workerid,)).fetchall()

    def check_worker(self,workerid):
        return len(self.seek_worker(workerid)) > 0

    def get_task_status(self,tasknum):
        with self.connection:
            return self.cursor.execute("SELECT `Status` FROM `Tasks` WHERE `tasknum` = ?",(tasknum,)).fetchone()
            
    def get_fio_worker(self, tgId):
        with self.connection:
            result = self.cursor.execute("SELECT `WorkerFIO` FROM `Workers` WHERE `tgId` = ?", (tgId,)).fetchone()
            return result[0] if result else None
    
    def get_sitename(self, task_number):
        with self.connection:
            result = self.cursor.execute("SELECT `basestation` FROM `Tasks` WHERE `tasknum` = ?",(task_number,)).fetchone()
            return result

    def is_supervisor(self, tgId):
        with self.connection:
            result = self.cursor.execute("Select `Position` FROM `Workers` WHERE `tgId` = ?",(tgId,)).fetchone()
            return result[0] if result else None
        
    def all_in_acc(self):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `Tasks` WHERE `status` = 'В работе'").fetchall()
            return result
        
    def all_in_new(self):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `Tasks` WHERE `status` = 'Новое'").fetchall()
            return result

    def get_task_by_number(self,tasknum):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `Tasks` WHERE `tasknum` = ?",(tasknum,)).fetchone()
            return result    

    def get_all_supervisors(self):
        with self.connection:
            result = self.cursor.execute("SELECT tgId FROM `Workers` WHERE `Position` = 'Supervisor'").fetchall()
            return result
        
    def tasks_by_worker(self,tgId):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `Tasks` WHERE `worker`= ? and `status` = 'В работе'",(tgId,)).fetchall()
            return result
        
    def get_status_counts_by_date(self, target_date: str):
        with self.connection:
            query = """
            SELECT status, COUNT(*) 
            FROM Tasks
            WHERE DATE(datetime) = ?
            GROUP BY status
            """
            result = self.cursor.execute(query, (target_date,)).fetchall()
            return {status: count for status, count in result}

    def get_status_counts_by_date_and_worker(self, target_date, worker_id):
        with self.connection:
            query = """
            SELECT status, COUNT(*)
            FROM Tasks
            WHERE DATE(datetime) = ?
            AND worker = ?
            GROUP BY status
            """
            result = self.cursor.execute(query, (target_date, worker_id)).fetchall()
            return {status: count for status, count in result}
        
    def get_status_counts_by_date_range(self, start_date: str, end_date: str):
        with self.connection:
            query = """
            SELECT status, COUNT(*)
            FROM Tasks
            WHERE DATE(datetime) BETWEEN ? AND ?
            GROUP BY status
            """
            result = self.cursor.execute(query, (start_date, end_date)).fetchall()
            return {status: count for status, count in result}
        
    def get_status_counts_by_date_range_and_worker(self, start_date: str, end_date: str, worker_id):
        with self.connection:
            query = """
            SELECT status, COUNT(*)
            FROM Tasks
            WHERE DATE(datetime) BETWEEN ? AND ?
            AND worker = ?
            GROUP BY status
            """
            result = self.cursor.execute(query, (start_date, end_date, worker_id)).fetchall()
            return {status: count for status, count in result}
        
    def get_topic_id_by_sitename(self, sitename):
        with self.connection:
            result = self.cursor.execute("SELECT `topic_id` FROM `BaseStations` WHERE `sitename` = ?", (sitename,)).fetchone()
            return result
        
    def get_accepted_tasks_day(self, date_str):
        start = datetime.strptime(date_str, "%Y-%m-%d")
        end = start + timedelta(days=1) - timedelta(microseconds=1)
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM `Tasks` WHERE `status` = 'В работе' AND `datetime` BETWEEN ? AND ?",
                (start, end)
            ).fetchall()
            return result

    def get_accepted_tasks_day_worker(self, date_str, workerid):
        start = datetime.strptime(date_str, "%Y-%m-%d")
        end = start + timedelta(days=1) - timedelta(microseconds=1)
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM `Tasks` WHERE `status` = 'В работе' AND `datetime` BETWEEN ? AND ? AND `worker` = ?",
                (start, end, workerid)
            ).fetchall()
            return result

    def get_accepted_tasks_week(self, start_date_str, end_date_str):
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(microseconds=1)
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM `Tasks` WHERE `status` = 'В работе' AND `datetime` BETWEEN ? AND ?",
                (start, end)
            ).fetchall()
            return result

    def get_accepted_tasks_week_worker(self, start_date_str, end_date_str, workerid):
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(microseconds=1)
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM `Tasks` WHERE `status` = 'В работе' AND `datetime` BETWEEN ? AND ? AND `worker` = ?",
                (start, end, workerid)
            ).fetchall()
            return result

    def get_new_tasks_today(self, date_str):
        start = datetime.strptime(date_str, "%Y-%m-%d")
        end = start + timedelta(days=1) - timedelta(microseconds=1)
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM `Tasks` WHERE `status` = 'Новое' AND `datetime` BETWEEN ? AND ?",
                (start, end)
            ).fetchall()
            return result

    def get_new_tasks_week(self, start_date_str, end_date_str):
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(microseconds=1)
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM `Tasks` WHERE `status` = 'Новое' AND `datetime` BETWEEN ? AND ?",
                (start, end)
            ).fetchall()
            return result
        
    def save_sent_message(self, task_number: str, chat_id: int, message_id: int) -> None:
        """
        Сохраняет факт того, что сообщение о задаче было отправлено супервизору.
        Дубли записей игнорируются.
        """
        with self.connection:
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO `sent_messages`
                    (`task_number`, `chat_id`, `message_id`)
                VALUES (?, ?, ?)
                """,
                (task_number, chat_id, message_id)
            )

    def get_sent_messages(self, task_number: str) -> list[tuple[int, int]]:
        """
        Возвращает список кортежей (chat_id, message_id)
        для всех супервизоров, которым была разослана заявка.
        """
        with self.connection:
            result = self.cursor.execute(
                """
                SELECT `chat_id`, `message_id`
                  FROM `sent_messages`
                 WHERE `task_number` = ?
                """,
                (task_number,)
            ).fetchall()
            return result    