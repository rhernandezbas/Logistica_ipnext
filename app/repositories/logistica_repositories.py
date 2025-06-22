""""""


from app.interfaces.interface_logistica import LogisticaInterface
from app.models import Cliente
from app.utils.config import db


class LogisticaRepository(LogisticaInterface):
    """"""

    def get_user_by_id(self, id_client:str ) ->Cliente:
        """ """
        return db.session().query(Cliente).get(id_client)
