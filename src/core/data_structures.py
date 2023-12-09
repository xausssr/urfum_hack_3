from pydantic import BaseModel
from fastapi import Query


class TextToAnnotate(BaseModel):
    """Класс описывающий структуру данных для загрузки текста"""

    text: str = Query(None, description="Текст для аннотации")


class Task(BaseModel):
    """Класс описывающий структуру данныз для задачи"""

    task_id: str = Query(None, description="Хеш задачи")
    is_complete: bool = Query(None, description="Флаг, определяющий состояние задачи 'выполнена'")
