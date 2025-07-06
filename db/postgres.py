import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

class DB:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def add_worker(self, tgId, workerFIO, phoneNumber, City, Position):
        sql = """
            INSERT INTO Workers (tgId, workerfio, phoneNumber, City, Position)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.cur.execute(sql, (tgId, workerFIO, phoneNumber, City, Position))

    def add_task(self, tasknum, basestation, status, worker, issue_datetime,
                 datetimereq=None, datetimeacc=None, datetimeclose=None,
                 work_type=None, description=None, short_description=None,
                 comments=None, address=None, responsible_person=None):
        sql = """
            INSERT INTO Tasks (
                tasknum, basestation, status, worker,
                datetime, datetimereq, datetimeacc, datetimeclose,
                work_type, description, short_description,
                comments, address, responsible_person
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            tasknum, basestation, status, worker,
            issue_datetime, datetimereq, datetimeacc, datetimeclose,
            work_type, description, short_description,
            comments, address, responsible_person
        )
        self.cur.execute(sql, params)

    def update_task(self, status, worker, datetimeacc, tasknum):
        sql = """
            UPDATE Tasks
               SET status      = %s,
                   worker      = %s,
                   datetimeacc = %s
             WHERE tasknum    = %s
        """
        self.cur.execute(sql, (status, worker, datetimeacc, tasknum))

    def close_task(self, status, finish_datetime, tasknum):
        sql = """
            UPDATE Tasks
               SET status        = %s,
                   datetimeclose = %s
             WHERE tasknum      = %s
        """
        self.cur.execute(sql, (status, finish_datetime, tasknum))

    def seek_worker(self, workerid):
        sql = "SELECT * FROM Workers WHERE tgId = %s"
        self.cur.execute(sql, (workerid,))
        return self.cur.fetchall()

    def check_worker(self, workerid):
        return len(self.seek_worker(workerid)) > 0

    def get_task_status(self, tasknum):
        sql = "SELECT status FROM Tasks WHERE tasknum = %s"
        self.cur.execute(sql, (tasknum,))
        return self.cur.fetchone()

    def get_fio_worker(self, tgId):
        tg_str = str(tgId)
        sql = "SELECT workerfio FROM Workers WHERE tgId = %s"
        self.cur.execute(sql, (tg_str,))
        row = self.cur.fetchone()
        return row['workerfio'] if row else None

    def get_workers(self):
        sql = "SELECT tgId, workerfio FROM Workers"
        self.cur.execute(sql)
        return self.cur.fetchall()

    def get_sitename(self, task_number):
        sql = "SELECT basestation FROM Tasks WHERE tasknum = %s"
        self.cur.execute(sql, (task_number,))
        return self.cur.fetchone()

    def is_supervisor(self, tgId):
        tg_str = str(tgId)
        sql = "SELECT Position FROM Workers WHERE tgId = %s"
        self.cur.execute(sql, (tg_str,))
        row = self.cur.fetchone()
        return row['position'] if row else None

    def all_in_acc(self):
        sql = """
            SELECT
                *,
                CASE
                    WHEN exited_by_worker IS NULL THEN 'Закрыта'
                    ELSE status
                END AS status
            FROM Tasks
            WHERE status = %s
            OR exited_by_worker IS NULL
        """
        self.cur.execute(sql, ('В работе',))
        return self.cur.fetchall()

    def all_in_new(self):
        sql = "SELECT * FROM Tasks WHERE status = 'Новое'"
        self.cur.execute(sql)
        return self.cur.fetchall()

    def get_task_by_number(self, tasknum):
        sql = "SELECT * FROM Tasks WHERE tasknum = %s"
        self.cur.execute(sql, (tasknum,))
        return self.cur.fetchone()

    def get_all_supervisors(self):
        sql = "SELECT tgId FROM Workers WHERE Position = 'Supervisor'"
        self.cur.execute(sql)
        return self.cur.fetchall()

    def tasks_by_worker(self, tgId):
        tg_str = str(tgId)
        sql = "SELECT * FROM Tasks WHERE worker = %s AND status = 'В работе' OR status = 'Закрыта'"
        self.cur.execute(sql, (tg_str,))
        return self.cur.fetchall()

    def get_status_counts_by_date(self, target_date: str):
        sql = """
            SELECT status, COUNT(*) 
              FROM Tasks
             WHERE DATE(datetime) = %s
             GROUP BY status
        """
        self.cur.execute(sql, (target_date,))
        return dict(self.cur.fetchall())

    def get_status_counts_by_date_and_worker(self, target_date, worker_id):
        tg_str = str(worker_id)
        sql = """
            SELECT status, COUNT(*)
              FROM Tasks
             WHERE DATE(datetime) = %s
               AND worker = %s
             GROUP BY status
        """
        self.cur.execute(sql, (target_date, tg_str))
        return dict(self.cur.fetchall())

    def get_status_counts_by_date_range(self, start_date, end_date):
        sql = """
            SELECT status, COUNT(*)
              FROM Tasks
             WHERE DATE(datetime) BETWEEN %s AND %s
             GROUP BY status
        """
        self.cur.execute(sql, (start_date, end_date))
        return dict(self.cur.fetchall())

    def get_status_counts_by_date_range_and_worker(self, start_date, end_date, worker_id):
        tg_str = str(worker_id)
        sql = """
            SELECT status, COUNT(*)
              FROM Tasks
             WHERE DATE(datetime) BETWEEN %s AND %s
               AND worker = %s
             GROUP BY status
        """
        self.cur.execute(sql, (start_date, end_date, tg_str))
        return dict(self.cur.fetchall())

    def get_topic_id_by_sitename(self, sitename):
        sql = "SELECT topic_id FROM BaseStations WHERE sitename = %s"
        self.cur.execute(sql, (sitename,))
        return self.cur.fetchone()

    def get_accepted_tasks_day(self, date_str):
        start = datetime.strptime(date_str, "%Y-%m-%d")
        end = start + timedelta(days=1) - timedelta(microseconds=1)
        sql = """
            SELECT * FROM Tasks
             WHERE datetime BETWEEN %s AND %s
               AND exited_by_worker IS NULL
        """
        self.cur.execute(sql, (start, end))
        return self.cur.fetchall()

    def get_accepted_tasks_day_worker(self, date_str, tgId):
        tg_str = str(tgId)
        start = datetime.strptime(date_str, "%Y-%m-%d")
        end = start + timedelta(days=1) - timedelta(microseconds=1)
        sql = """
            SELECT * FROM Tasks
             WHERE datetime BETWEEN %s AND %s
               AND worker = %s
               AND exited_by_worker IS NULL
        """
        self.cur.execute(sql, (start, end, tg_str))
        return self.cur.fetchall()

    def get_accepted_tasks_week(self, start_date_str, end_date_str):
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(microseconds=1)
        sql = """
            SELECT * FROM Tasks
             WHERE datetime BETWEEN %s AND %s
               AND exited_by_worker IS NULL
        """
        self.cur.execute(sql, (start, end))
        return self.cur.fetchall()

    def get_accepted_tasks_week_worker(self, start_date_str, end_date_str, tgId):
        tg_str = str(tgId)
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(microseconds=1)
        sql = """
            SELECT * FROM Tasks
             WHERE datetime BETWEEN %s AND %s
               AND worker = %s
               AND exited_by_worker IS NULL
        """
        self.cur.execute(sql, (start, end, tg_str))
        return self.cur.fetchall()

    def get_new_tasks_today(self, date_str):
        start = datetime.strptime(date_str, "%Y-%m-%d")
        end = start + timedelta(days=1) - timedelta(microseconds=1)
        sql = """
            SELECT * FROM Tasks
             WHERE status = 'Новое'
               AND datetime BETWEEN %s AND %s
        """
        self.cur.execute(sql, (start, end))
        return self.cur.fetchall()

    def get_new_tasks_week(self, start_date_str, end_date_str):
        start = datetime.strptime(start_date_str, "%Y-%m-%d")
        end = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(microseconds=1)
        sql = """
            SELECT * FROM Tasks
             WHERE status = 'Новое'
               AND datetime BETWEEN %s AND %s
        """
        self.cur.execute(sql, (start, end))
        return self.cur.fetchall()

    def save_sent_message(self, task_number: str, chat_id: int, message_id: int) -> None:
        sql = """
            INSERT INTO sent_messages (task_number, chat_id, message_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (message_id) DO NOTHING
        """
        self.cur.execute(sql, (task_number, chat_id, message_id))

    def get_sent_messages(self, task_number: str):
        sql = """
            SELECT chat_id, message_id
              FROM sent_messages
             WHERE task_number = %s
        """
        self.cur.execute(sql, (task_number,))
        return self.cur.fetchall()

    def issent(self, tasknum):
        sql = """
            UPDATE sent_messages
               SET sent_to_topic = 'YES'
             WHERE task_number = %s
        """
        self.cur.execute(sql, (tasknum,))

    def ifsent(self, tasknum):
        sql = """
            SELECT 1
              FROM sent_messages
             WHERE task_number = %s
               AND sent_to_topic = 'YES'
             LIMIT 1
        """
        self.cur.execute(sql, (tasknum,))
        return self.cur.fetchone() is not None

    def close_task_by_worker(self, task_number: str, exited_by_worker: datetime,
                             close_code: str, quantity: int):
        sql = """
            UPDATE Tasks
               SET status           = 'Закрыта',
                   exited_by_worker = %s,
                   close_code       = %s::text[],
                   quantity         = %s::int4[],
                   datetimeclose    = COALESCE(datetimeclose, %s)
             WHERE tasknum         = %s
        """
        self.cur.execute(sql, (
            exited_by_worker,
            close_code,
            quantity,
            exited_by_worker,
            task_number
        ))

    def deny_task(self, tasknum):
        sql = """
            UPDATE Tasks
               SET worker      = NULL,
                   datetimereq = NULL,
                   status      = 'Новое'
             WHERE tasknum    = %s
        """
        self.cur.execute(sql, (tasknum,))
