from sqlite3 import Connection, Cursor
from datetime import datetime as dt
import hashlib
from typing import List

from core.data_structures import FeaturesStructure, Task


def verify_prescore_table(cursor_db: Cursor, connection_db: Connection, columns: List[str]) -> None:
    """Верификация таблицы с пре-скорингом, если таблицы нет - создание новой

    Args:
        cursor_db (Cursor): курсор коннектора БД
        connection_db (Connection): объект коннектора БД
        colums (Dict[str, Any]): список колонок банков
    """

    res = cursor_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prescore';")
    cols = ",".join(["task_id TEXT"] + columns)

    if res.fetchone() is None:
        cursor_db.execute(f"CREATE TABLE prescore({cols})")
    connection_db.commit()


def verify_data_table(cursor_db: Cursor, connection_db: Connection, columns: List[str]) -> None:
    """Верификация таблицы с данными, если таблицы нет - создание новой

    Args:
        cursor_db (Cursor): курсор коннектора БД
        connection_db (Connection): объект коннектора БД
        colums (Dict[str, Any]): список колонок фичей

    Notes:
        'SkillFactory_Id' - не используется, это внутренний id вендора
    """
    res = cursor_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='features';")
    # TODO когда модели достроим - поменять столбцы, которые используются
    cols = ",".join(["task_id TEXT"] + columns)

    if res.fetchone() is None:
        cursor_db.execute(f"CREATE TABLE features({cols})")
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


def get_or_create_task(features: FeaturesStructure, cursor_db: Cursor, connection_db: Connection) -> Task:
    """Получение пре-скоринга, если анкета с таким кешем уже была обработана или создание новой задачи

    Args:
        features (FeaturesStructure): данные для предсказания (см. FeaturesStructure)
        cursor_db (Cursor): курсор коннектора БД
        connection_db (Connection): объект коннектора БД

    Returns:
        Task: объект задачи (описан в core.data_structures)
    """

    features = features.dict()
    _sha1 = hashlib.sha1()
    _sha1.update(str.encode(str(features)))
    task_id = _sha1.hexdigest()
    res = cursor_db.execute(f"SELECT * FROM tasks WHERE task_id='{task_id}';")

    if res.fetchone() is None:
        cols = ",".join([f"'{x}'" for x in features.keys()])
        values = ",".join([f"'{x}'" for x in features.values()])
        cursor_db.execute(f"INSERT INTO features ('task_id', {cols}) VALUES ('{task_id}', {values})")
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
