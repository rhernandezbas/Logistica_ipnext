""" """

from abc import ABC, abstractmethod
from app.models.cliente import Cliente


class LogisticaInterface(ABC):
    """ """

    @abstractmethod
    def get_user_by_id(self, id_client:str )->Cliente:
        """ """
        pass