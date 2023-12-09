import os
import pickle
import numpy as np

from typing import Any, Dict, List
import pandas as pd

from sklearn.preprocessing import OneHotEncoder


def dump_or_load_object(path: str, obj: Any = None, force: bool = False) -> Any:
    """Дамп объекта или его загрузка, если он уже был сохранен

    Args:
        path (str): путь до сохранения
        obj (Any, Optional): объект для сохранения
        force (bool): перезаписать объект

    Returns:
        (Any): объект (загруженый или входной)
    """

    folders, filename = os.path.split(path)
    if not os.path.exists(folders):
        os.makedirs(folders, exist_ok=True)
        pickle.dump(obj, open(path, "wb"))
    elif filename not in os.listdir(folders):
        pickle.dump(obj, open(path, "wb"))
    else:
        obj = pickle.load(open(path, "rb"))

    return obj


def basic_process(data: pd.DataFrame, columns_cat: Dict[str, List[str]], drop: bool = True) -> pd.DataFrame:
    """Базовые преобразования
        * дата рождения -> возраст (полных лет?)
        * дата новой работы -> время пребывания на последней работе (лет ? 0 - меньше года)
        * одобрение банка -> цифры (denied = 0, success = 1, error = 2)
        * если вся строка nan - drop
        * удаляем id
        * Position - в нижний регистр + удалем пробелы

    Args:
        data (pd.DataFrame): датасет/данные
        columns_cat (str, Dict[List[str]]): сортировка колонок
        drop (bool): удалить исходные колонки? Defaults to False

    Returns:
        (pd.DataFrame): преобразованный датасет/данные
    """

    data["age"] = 2023 - pd.to_datetime(data["BirthDate"]).dt.year
    data["last_work_years"] = 2023 - pd.to_datetime(data["JobStartDate"]).dt.year
    data["Position"] = data["Position"].str.lower().str.strip()

    drop_rows = lambda row: row.isna().sum() == data.shape[1]
    data = data.drop(data[data.apply(drop_rows, axis=1)].index)

    if drop:
        data = data.drop(columns=["BirthDate", "JobStartDate"])
    return data


def process_nan(data: pd.DataFrame) -> pd.DataFrame:
    """Добавление колоноки с числом пропусков, замена пропусков на -1
    Args:
        data (pd.DataFrame): датасет/данные

    Returns:
        (pd.DataFrame): преобразованный датасет/данные
    """

    return data.fillna(-1)


def add_features(data: pd.DataFrame) -> pd.DataFrame:
    """
    Добавление фичей:
        * отношение доход/расход
        * отношение объем кредита/срок кредита
        * отношение (доход - расход) / (объем кредита/срок кредита)

    Args:
        data (pd.DataFrame): данные

    Returns:
        (pd.DataFrame): данные, обогощенные фичами
    """

    data["profit_expense"] = data["MonthProfit"] / data["MonthExpense"]
    data["loan_term_amount"] = data["Loan_amount"] / data["Loan_term"]
    data["month_load"] = (data["MonthProfit"] - data["MonthExpense"]) / (data["Loan_amount"] / data["Loan_term"])

    # проверям на бесконечность
    data[data["profit_expense"] == np.inf] = -1
    data[data["loan_term_amount"] == np.inf] = -1
    data[data["month_load"] == np.inf] = -1
    return data


class ModelInference:
    """Класс для полной предобработки сырых данных"""

    def __init__(self, processor_path: str, model_path: str) -> None:
        """Инициализация препроцессора, загружает функции из папки

        Args:
            processor_path (str): путь до сохраненных препроцессоров
            model_path (str): путь до папки с моделями
        """
        self.model_path = model_path
        self.processor_path = processor_path

        self.columns_cat = dump_or_load_object(os.path.join(processor_path, "columns_cat.pkl"))
        self.post_columns = dump_or_load_object(os.path.join(processor_path, "post_columns_cat.pkl"))
        self.cat_preprocessor = dump_or_load_object(os.path.join(processor_path, "cat_preprocessor.pkl"))

        self.one_hot_preprocess = None

        self.models = {}
        self.__load_state()

    def __load_state(self):
        """Загрузка состояния эксперимента (для продолжения)"""
        for model in os.listdir(self.model_path):
            self.models[model] = pickle.load(open(os.path.join(self.model_path, model), "rb"))
        if os.path.exists(os.path.join(self.processor_path, "onehot.pkl")):
            self.one_hot_preprocess = pickle.load(open(os.path.join(self.processor_path, "onehot.pkl"), "rb"))

    def preprocess(self, data: pd.DataFrame, add_none: bool = True) -> pd.DataFrame:
        """Препроцессинг данных

        Args:
            data (pd.DataFrame): данные
            add_none (bool): добовлять ли столбцы для обработки None

        Returns:
            (pd.DataFrame): данные, обогощенные фичами
        """
        data = basic_process(data, self.columns_cat)
        data = process_nan(data)
        data[self.columns_cat["cat"]] = self.cat_preprocessor.transform(data[self.columns_cat["cat"]].astype(str))
        data = add_features(data)

        if add_none:
            for col in data.columns:
                data[f"{col}_none"] = 0
                data.loc[data[col] == -1, f"{col}_none"] = 1
            if self.one_hot_preprocess is None:
                self.one_hot_preprocess = {}
                one_hot = []
                for col in self.post_columns["cat"]:
                    encoder = OneHotEncoder()
                    one_hot.append(encoder.fit_transform(data[col].values.reshape((-1, 1))).toarray())
                    self.one_hot_preprocess[col] = encoder
                    pickle.dump(self.one_hot_preprocess, open(os.path.join(self.runs_path, "onehot.pkl"), "wb"))
            else:
                one_hot = []
                for col in self.post_columns["cat"]:
                    one_hot.append(
                        self.one_hot_preprocess[col].fit_transform(data[col].values.reshape((-1, 1))).toarray()
                    )
            feature_names = []
            for i in self.one_hot_preprocess.keys():
                feature_names += [
                    f"{i}_{p}" for p in range(len(self.one_hot_preprocess[i].get_feature_names_out().tolist()))
                ]
            one_hot = pd.DataFrame(np.hstack(one_hot), columns=feature_names)
            data = data.drop(columns=self.post_columns["cat"])
            data = pd.concat([data, one_hot], axis=1)
        return data

    def predict(self, x: pd.DataFrame, banks: List[str]) -> Dict[str, Any]:
        """Предсказание модели для входных данных (с точки зрения вероятности одобрения)

        Args:
            x (pd.DataFrame): входные данные в формате pd.DataFrame (одна строка, пока без батчей)
            banks (List[str]): список имен банков (для консистентности с API)

        Returns:
            Dict[str, Any]: словарь с пре-скорингом для каждого банка и коэффициентами шапа (важность полей анкеты)
        """

        preprocessed_data = self.preprocess(x, add_none=False)
        results = {}
        for idx, clf in enumerate(self.models.values()):
            results[banks[idx]] = clf.predict_proba(preprocessed_data)[0, 1]
        return results
