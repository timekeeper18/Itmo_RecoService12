from pathlib import Path

import dill
import numpy as np
from rectools import Columns


class KionReco:
    """
    Класс, содержащий методы получения рекомендаций по датасету Kion
    """

    def __init__(self, model_name_, dataset_):
        assert Path(model_name_).is_file()#проверка на наличие файла с моделью
        assert Path(dataset_).is_file()#проверка на наличие файла с датасетом
        # подгружаем модель
        with open(Path(model_name_), 'rb') as f:
            self.model = dill.load(f)
        # подгружаем датасет
        with open(Path(dataset_), 'rb') as f:
            self.dataset = dill.load(f)

        self.sorted_top = self.dataset.interactions.df[
            [Columns.Item]].value_counts().reset_index()[Columns.Item].values

    def __check_user(self, user_id) -> bool:
        return False if len(np.where(
            self.dataset.user_id_map.external_ids == user_id)[0]) == 0 \
            else True

    def reco(self, user_id, k_recos=10) -> np.ndarray:
        """
        Получение К рекомендаций для пользователя
        :param user_id: идентификатор пользователя
        :param k_recos: количество рекомендаций
        :return:
        """
        if self.__check_user(user_id):
            # рекомендации для теплого пользователя (который попал в обучение)
            df_recos = self.model.recommend(
                users=[user_id],
                dataset=self.dataset,
                k=k_recos,
                filter_viewed=True
            )
            return df_recos[Columns.Item].values
        else:
            return self.sorted_top[:k_recos]
