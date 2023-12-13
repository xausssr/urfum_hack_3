from sqlite3 import Connection, Cursor


def verify_worker_table(cursor_db: Cursor, connection_db: Connection) -> None:
    """Верификация таблицы воркеров, если таблицы нет - создание новой

    Args:
        cursor_db (Cursor): курсор коннектора БД
        connection_db (Connection): объект коннектора БД

    """
    res = cursor_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workers';")
    if res.fetchone() is None:
        cursor_db.execute("CREATE TABLE workers(task_id TEXT, timestamp_start NUMERIC, timestamp_end NUMERIC)")
    connection_db.commit()
