from pydantic import BaseModel
from fastapi import Query


class FeaturesStructure(BaseModel):
    """Класс описывающий структуру данных для полей анкеты"""

    # TODO как выберем модель - поменять схему данных!
    birthdate: str = Query(
        None, description="Дата рождения в формате 'YYYY-mm-dd HH:MM:SS.(s)' - пример '2000-11-22 00:00:00.0000000'"
    )
    education: str = Query(None, description="Образование (текстом)")
    employment_status: str = Query(None, description="Род деятельности (рабочий по найму, свой бизнес)")
    value: str = Query(None, description="Стаж работы в годах")
    jobstartdate: str = Query(
        None,
        description="Дата начала работы на текущей позиции 'YYYY-mm-dd HH:MM:SS.(s)'"
        + " - пример '2000-11-22 00:00:00.0000000'",
    )
    position: str = Query(None, description="Должность")
    monthprofit: float = Query(None, description="Ежемесячный доходв (в руб.)")
    monthexpense: float = Query(None, description="Ежемесячные расходы (в руб.)")
    gender: int = Query(None, description="Пол: 0 = мужчина, 1 = женщина")
    family_status: str = Query(None, description="Семейное положение")
    childcount: int = Query(None, description="Кол-во детей младше 18 лет")
    snils: int = Query(None, description="СНИЛС, значения: 0 = не указан в анкете, 1 = указан")
    merch_code: int = Query(None, description="Код магазина")
    loan_amount: float = Query(None, description="Объем займа (в руб.)")
    loan_term: float = Query(None, description="Длительность займа (в месяцах)")
    goods_category: str = Query(None, description="Категория товара")


class Task(BaseModel):
    """Класс описывающий структуру данных для задачи"""

    task_id: str = Query(None, description="Хеш задачи")
    is_complete: bool = Query(None, description="Флаг, определяющий состояние задачи 'выполнена'")
