import json
import sqlite3
import time
from datetime import datetime as dt

from core.worker_utils import verify_worker_table
from model_inference import ModelInference


class Worker:
    """Класс для инференса пре-скоринга"""

    def __init__(self) -> None:
        """Инициализация класса"""
        self.settings = json.load(open("./configs/worker_config.json", "r", encoding="utf-8"))
        self.connection_db = sqlite3.connect(self.settings["data_base"])
        self.cursor_db = self.connection_db.cursor()

        self.inference = ModelInference(
            processor_path=self.settings["processor_path"], model_path=self.settings["model_path"]
        )

        self.last_task_id = None
        verify_worker_table(cursor_db=self.cursor_db, connection_db=self.connection_db)

    def get_task(self):
        """Получение новой задачи"""
        res_task = self.cursor_db.execute("SELECT * FROM tasks WHERE is_complete=false;")
        res_task = res_task.fetchall()
        if len(res_task) > 0:
            available_tasks = " OR".join([" task_id='" + x[0] + "'" for x in res_task])
            res_available = self.cursor_db.execute(f"SELECT * FROM workers WHERE{available_tasks};")
            res_available = res_available.fetchall()
            if len(res_available) == 0:
                self.last_task_id = res_task[0][0]
            else:
                worker_tasks = list(set([x[0] for x in res_task]) - set([x[0] for x in res_available]))
                if len(worker_tasks) > 0:
                    self.last_task_id = worker_tasks[0]

        if self.last_task_id is not None:
            self.cursor_db.execute(
                "INSERT INTO workers (task_id, timestamp_start, timestamp_end) VALUES "
                f"('{self.last_task_id}', '{dt.now().timestamp()}', '-1')"
            )
            self.connection_db.commit()

    def predict(self) -> None:
        """Получение пре-скоринга для задачи (self.last_task_id)"""

        in_data = self.cursor_db.execute(f"SELECT * FROM features WHERE task_id='{self.task_id}';")
        print(in_data)
        self.last_task_id = None
        return
        self.cursor_db.execute(
            f"UPDATE workers SET timestamp_end='{dt.now().timestamp()}' WHERE task_id='{self.last_task_id}'"
        )
        self.cursor_db.execute(f"UPDATE tasks SET is_complete='true' WHERE task_id='{self.last_task_id}'")
        self.connection_db.commit()
        self.last_task_id = None

    def run(self) -> None:
        """Бесконечный цикл чтения базы, при появлении новой задачи - её выполнение и запись в базу"""

        while True:
            self.get_task()
            if self.last_task_id is None:
                time.sleep(5)
            else:
                self.predict()


if __name__ == "__main__":
    worker = Worker()
    worker.run()
