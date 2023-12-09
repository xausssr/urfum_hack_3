from sqlite3 import Connection, Cursor
from datetime import datetime as dt
import hashlib
from typing import List

from core.data_structures import Task


def verify_data_table(cursor_db: Cursor, connection_db: Connection, columns: List[str]) -> None:
    """Верификация таблицы с данными, если таблицы нет - создание новой

    Args:
        cursor_db (Cursor): курсор коннектора БД
        connection_db (Connection): объект коннектора БД
        colums (Dict[str, Any]): список полонок фичей в формате [ИМЯ SQL_тип_данных, ИМЯ SQL_тип_данных, ....]

    Notes:
        'SkillFactory_Id' - не используется, это внутренний id вендора
    """
    res = cursor_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks';")
    # TODO когда модели достроим - поменять столбцы, которые используются
    cols = ",".join(["task_id TEXT"] + columns)

    if res.fetchone() is None:
        cursor_db.execute(f"CREATE TABLE tasks({cols})")
    connection_db.commit()


def verify_task_table(cursor_db: Cursor, connection_db: Connection) -> None:
    """Верификация таблицы задач, если таблицы нет - создание новой

    Args:
        cursor_db (Cursor): курсор коннектора БД
        connection_db (Connection): объект коннектора БД

    """
    res = cursor_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks';")
    if res.fetchone() is None:
        cursor_db.execute("CREATE TABLE tasks(task_id TEXT, timestamp NUMERIC, is_complete BOOLEAN)")
    connection_db.commit()


def get_or_create_task(text: str, cursor_db: Cursor, connection_db: Connection) -> Task:
    """Получение аннотации, если статья с таким кешем уже была обработана или создание новой задачи

    Args:
        text (str): текст для аннотации
        cursor_db (Cursor): курсор коннектора БД
        connection_db (Connection): объект коннектора БД

    Returns:
        Task: объект задачи (описан в core.data_structures)
    """

    _sha1 = hashlib.sha1()
    _sha1.update(str.encode(text))
    task_id = _sha1.hexdigest()
    res = cursor_db.execute(f"SELECT * FROM tasks WHERE task_id='{task_id}';")
    if res.fetchone() is None:
        with open(f"./data/texts/{task_id}.text", "w") as f:
            f.write(text)
        cursor_db.execute(
            f"INSERT INTO tasks (task_id,timestamp,is_complete) VALUES ('{task_id}', '{dt.now().timestamp()}', false)"
        )
        task = Task(task_id=task_id, is_complete=False)
    else:
        task = Task(task_id=task_id, is_complete=True)
    connection_db.commit()
    return task


def check_task_state(task_id: str, cursor_db: Cursor, connection_db: Connection) -> int:
    """Проверка состояния задачи

    Args:
        task_id (str): id задачи
        cursor_db (Cursor): курсор коннектора БД
        connection_db (Connection): объект коннектора БД

    Returns:
        int: 0 - задача в очереди, 1 - задача выполнена, -1 задачи не существует
    """
    res = cursor_db.execute(f"SELECT * FROM tasks WHERE task_id='{task_id}';")
    connection_db.commit()
    res = res.fetchone()
    if res is None:
        return -1
    else:
        return int(res[2].strip() == "true")
