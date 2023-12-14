import os
import pickle
import numpy as np

from typing import Any, Dict, List
import pandas as pd

from sklearn.preprocessing import OneHotEncoder

from activity_bins import activity_bins


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
    """Производит базовые преобразования набора данных.

    Args:
        data (pd.DataFrame): Исходные данные.
        columns_cat (Dict[str, List[str]]): Сортировка колонок.
        drop (bool): Удалить исходные колонки? Defaults to True.

    Returns:
        pd.DataFrame: Преобразованные данные.
    """
    #удаление пропусков
    drop_rows = lambda row: row.isna().sum() == data.shape[1]
    data = data.drop(data[data.apply(drop_rows, axis=1)].index)

    # Возраст заемшика
    data['age'] = 2023 - pd.to_datetime(data['BirthDate']).dt.year

    # Возрастной статус человека
    def get_age_status(age, is_female):
        minor_age = 17
        adult_age = 18
        pensioner_age_woman = 65
        pensioner_age_man = 68

        if age <= minor_age:
            age_status = 'несовершеннолетний'
        elif is_female:
            if adult_age <= age < pensioner_age_woman:
                age_status = 'трудоспособный'
            else:
                age_status = 'пенсионер'
        else:
            if adult_age <= age < pensioner_age_man:
                age_status = 'трудоспособный'
            else:
                age_status = 'пенсионер'

        return age_status

    data['age_status'] = data.apply(lambda row: get_age_status(row['age'], row['Gender']), axis=1)

    data['education'] = data['education'].fillna('Неоконченное среднее')

    # Выделим недоучившихся в отдельную колонку 1 - Оконченное, 0 - Неоконченное
    data['finished_education'] = data['education'].apply(lambda x: 0 if 'Неоконченное' in x else 1)

    # Наличие высшего образования 0 - Нет, 1 - Есть
    data['education_raiting'] = data['education'].replace({
            "Высшее - специалист": 1,
            "Среднее профессиональное": 0,
            "Среднее": 0,
            "Неоконченное высшее": 1,
            "Бакалавр": 1,
            "Несколько высших": 1,
            "Магистр": 1,
            "Неоконченное среднее": 0,
            "MBA": 1,
            "Ученая степень": 1
            })

    data['employment status'] = data['employment status'].fillna('Не работаю')

    # Студенты
    data['is_student'] = data['employment status'].apply(lambda x: 1 if 'Студент' in x else 0)

    # пенсионеры
    data['is_pensioner'] = data['employment status'].apply(lambda x: 1 if 'Пенсионер' in x else 0)

    # в декрете
    data['is_maternity_leave'] = data['employment status'].apply(lambda x: 1 if 'Декретный отпуск' in x else 0)

    # Натятый рабочий
    data['is_hired_worker'] = data['employment status'].apply(lambda x: 1 if 'Работаю по найму' in x else 0)

    # Тунеядец
    data['is_not_worker'] = data['employment status'].apply(lambda x: 1 if 'Не работаю' in x else 0)

    # 0 - не полный рабочий день, 1 - полный рабочий день
    data['is_works_full_time'] = data['employment status'].apply(lambda x: 1 if 'полный рабочий день' in x else 0)

    # Самозанятый
    data['is_self_employed'] = data['employment status'].apply(lambda x: 1 if 'Собственное дело' in x else 0)

    data['Value'] = data['Value'].fillna('Не работал')

    # Стаж работы от 10 лет и выше
    data['experience_over_10_year'] = data['Value'].apply(lambda x: 1 if '10 и более лет' in x else 0)

    data['JobStartDate'] = data['JobStartDate'].fillna(0)

    data['last_work_years'] = 2023 - pd.to_datetime(data['JobStartDate']).dt.year

    data['Position'] = data['Position'].fillna('нет должности')

    # Переводим в нижний регистр и Удалить лишние пробелы в значениях столбиков
    data['Position'] = data['Position'].str.strip().str.lower()

    data['is_position'] = data['Position'].apply(lambda x: 1 if not 'нет должности' in x else 0)

    data['Position'] = data['Position'].replace(activity_bins)

    # Отноешние ЗП к среднему доходу
    average_income = 70.3
    data['salary_to_avg_income_Ratio'] = data['MonthProfit'] / average_income

    # Заполняем пропуски по медиане
    data['Family status'] = data['Family status'].fillna(data['Family status'].mode()[0])

    data['ChildCount'] = data['ChildCount'].fillna(data['ChildCount'].mode()[0])

    data['Gender'] = data['Gender'].fillna(data['Gender'].mode()[0])

    # Отношение возроста гражданина к Среднему значению возраста россиян, которые вступают в брак
    def get_age_to_average_marriage_age_ratio(gender, age):
        average_men = 25.4
        average_woman = 23.2
        if gender:
            age_to_average_marriage_age_ratio = age / average_woman
        else:
            age_to_average_marriage_age_ratio = age / average_men
        return age_to_average_marriage_age_ratio
            
    data['age_to_average_marriage_age_ratio'] = data.apply(
        lambda row: get_age_to_average_marriage_age_ratio(row['Gender'], row['age']), axis=1)

    def get_single_parent(family_status, child_count):
        single_parent_arr = ['Никогда в браке не состоял(а)',
                             'Разведён / Разведена',
                             'Вдовец / вдова']

        return 1 if family_status in single_parent_arr and child_count > 0 else 0

    # Родители одиночки
    data['is_single_parent'] = data.apply(
        lambda row: get_single_parent(row['Family status'], row['ChildCount']), axis=1)

    # Многодетные семьи
    data['large_family'] = data['ChildCount'].apply(lambda x: 1 if x > 2 else 0)

    # В браке
    data['is_married'] = data.apply(
        lambda row: 1 if row['Family status'] == 'Женат / замужем' else 0, axis=1)
    # Были в браке
    # Суды, наследство, кредиты долги
    data['was_married'] = data.apply(
        lambda row: 1 if row['Family status'] in ['Разведён / Разведена', 'Вдовец / вдова'] else 0,
        axis=1
        )
    # Живет С/Без Парнера
    # Есть кому финансово помочь
    data['living_with_partner'] = data.apply(
        lambda row: 1 if row['Family status'] in ['Женат / замужем', 'Гражданский брак / совместное проживание'] else 0,
        axis=1
        )

    def get_family_mrot(age_status, child_count, is_married):
        child_mrot = 13944
        worked_mrot = 15669
        pensioner_mrot = 12363

        # для женщин
        if age_status == 'трудоспособный':
            family_mrot = worked_mrot + child_count * child_mrot + is_married * worked_mrot
        elif age_status == 'пенсионер':
            family_mrot = pensioner_mrot + child_count * child_mrot + is_married * worked_mrot
        else:
            family_mrot = child_mrot + child_count * child_mrot + is_married * worked_mrot

        return family_mrot
    data['family_mrot'] = data.apply(
        lambda row: get_family_mrot(row['age_status'], row['ChildCount'], row['is_married']),
        axis=1
        )

    # Возможно платит элименты
    data['is_possibly_pays_bills'] = data.apply(
        lambda row: 1 if row['Family status'] in ['Никогда в браке не состоял(а)', 'Разведён / Разведена', 'Вдовец / вдова'] and row['ChildCount'] else 0,
        axis=1
        )

    # Показатель отношения возроста к среднему возрасту заболеванию раком 65
    age_cancer = 65
    data['Age/Cancer_Incidence_Ratio'] = data.apply(lambda row: row['age'] / age_cancer, axis=1)

    if drop:
        data = data.drop(columns=['BirthDate', 'JobStartDate', 'Position', 'employment status', 'Family status'])
    return data


def process_nan(data: pd.DataFrame) -> pd.DataFrame:
    """Добавляет колонку с числом пропусков и заменяет пропуски на -1.

    Args:
        data (pd.DataFrame): Исходные данные.

    Returns:
        pd.DataFrame: Преобразованные данные.
    """
    return data.fillna(-1)


def add_features(data: pd.DataFrame) -> pd.DataFrame:
    """Добавляет новые признаки в данные.

    Args:
        data (pd.DataFrame): Исходные данные.

    Returns:
        pd.DataFrame: Данные с новыми признаками.
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
        print('!!!!!!!!!!!!model!!!!!!!!!')
        print(data)
        data[self.columns_cat["cat"]] = self.cat_preprocessor.transform(data[self.columns_cat["cat"]].astype(str))

        print('!!!!!!!!!!!!onehot!!!!!!!!!')
        print(data)
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
