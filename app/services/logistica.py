import csv
import os

from functools import lru_cache

from dotenv import load_dotenv
import requests
from app.utils.logger import get_logger
import chardet
from app.services.route_optimizer import RouteOptimizer
from app.repositories.logistica_repositories import LogisticaRepository

logger = get_logger(__name__)

class Logistica:
    """ """
    def __init__(self):
        """ constructor """
        load_dotenv()
        self.repository = LogisticaRepository()
        self.goole_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.hf_token = os.getenv("HF_TOKEN")
        self.default_reference_point = "-34.6554574,-59.4324731"
        self.tecnicos = {
            "tecnico1": "antonio",
            "tecnico2": "andy",
            "tecnico3": "xxx"
        }
        self.unidades = {
            "unidade1": ["antonio", "jose"],
        }
        self.citys = {
            "mercedes": [],
            "chivilco": [],
            "else": []
        }
        self.time = {
            "instalacion": 1.30,
            "verificaciones_wirreles": 1,
            "verificaciones_fibra": 1
        }
        

        use_llm = bool(self.hf_token)
        self.route_optimizer = RouteOptimizer(
            google_maps_api_key=self.goole_maps_api_key,
            default_reference_point=self.default_reference_point,
            installation_times=self.time,
            use_llm=use_llm
        )
        
        if use_llm:
            logger.info("Optimizador de rutas configurado para usar LLM de Hugging Face")
        else:
            logger.info("Optimizador de rutas configurado en modo tradicional (sin LLM)")


    def prueba_db(self):
        """"""
        data = self.repository.get_user_by_id("1")

        return data

    @lru_cache(maxsize=100)
    def geocode_address(self, address: str) -> dict:
        """
        Convierte una dirección en coordenadas geográficas usando Google Maps API.
        Utiliza caché para evitar llamadas repetidas con la misma dirección.
        """
        try:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={self.goole_maps_api_key}"
            response = requests.get(url)
            data = response.json()

            if data['status'] == 'OK':
                location = data['results'][0]['geometry']['location']
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': data['results'][0]['formatted_address']
                }
            else:
                logger.error(f"Error geocoding address: {data['status']}")
                return {}
        except Exception as e:
            logger.error(f"Exception during geocoding: {str(e)}")
            return {}


    def calculate_travel_time(self, origin: str, destination: str, consider_traffic: bool = True):
        """
        Calcula el tiempo estimado de viaje entre dos puntos usando la API de Distance Matrix de Google Maps.
        
        Args:
            origin (str): Coordenadas de origen en formato "latitud, longitud"
            destination (str): Coordenadas de destino en formato "latitud, longitud"
            consider_traffic (bool, optional): Sí se debe considerar el tráfico actual. Por defecto es True.
            
        Returns:
            dict: Diccionario con información del tiempo de viaje:
                - duration_seconds: Tiempo en segundos sin considerar tráfico
                - duration_text: Tiempo formateado sin considerar tráfico (ej.: "30 minutos")
                - duration_in_traffic_seconds: Tiempo en segundos considerando tráfico (si se solicitó)
                - duration_in_traffic_text: Tiempo formateado considerando tráfico (ej.: "45 minutos")
                - distance_meters: Distancia en metros
                - distance_text: Distancia formateada (ej.: "5.2 km")
        """
        try:
            # Parámetros base
            params = {
                "origins": origin,
                "destinations": destination,
                "key": self.goole_maps_api_key
            }
            
            # Si queremos considerar el tráfico, añadimos los parámetros necesarios
            if consider_traffic:
                params["departure_time"] = "now"  # Usar la hora actual
                params["traffic_model"] = "best_guess"  # Opciones: best_guess, pessimistic, optimistic
            
            # Construir la URL con los parámetros
            url_params = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?{url_params}"
            
            response = requests.get(url)
            data = response.json()
            
            if data['status'] == 'OK' and data['rows'][0]['elements'][0]['status'] == 'OK':
                element = data['rows'][0]['elements'][0]
                result = {
                    "distance_meters": element['distance']['value'],
                    "distance_text": element['distance']['text'],
                    "duration_seconds": element['duration']['value'],
                    "duration_text": element['duration']['text']
                }
                
                # Si se solicitó información de tráfico y está disponible
                if consider_traffic and 'duration_in_traffic' in element:
                    result["duration_in_traffic_seconds"] = element['duration_in_traffic']['value']
                    result["duration_in_traffic_text"] = element['duration_in_traffic']['text']
                
                logger.info(f"Tiempo de viaje calculado: {result['duration_text']} " + 
                           (f"(con tráfico: {result['duration_in_traffic_text']})" if consider_traffic and 'duration_in_traffic_text' in result else ""))
                return result
            else:
                status = data.get('status', 'Unknown error')
                element_status = data.get('rows', [{}])[0].get('elements', [{}])[0].get('status', 'Unknown error') if data.get('rows') else 'No data'
                logger.error(f"Error calculating travel time: API status: {status}, Element status: {element_status}")
                return None
        except Exception as e:
            logger.error(f"Exception during travel time calculation: {str(e)}")
            return None

    def create_optimized_routes(self, clients: list[dict]) -> dict:
        """
        Crea rutas optimizadas para visitar clientes, agrupados por ciudad.
        
        Parámetros:
        - clients: Lista de diccionarios con información de clientes, incluyendo 'direccion'
        
        Retorna:
        - Un diccionario con rutas optimizadas por día, donde cada ruta respeta:
          - Horario de trabajo: 9:30 a 18:00
          - 1 hora de almuerzo
          - Tiempo de instalación según self. Time
        """
        try:
            return self.route_optimizer.optimize_routes(
                clients=clients,
                geocode_func=self.geocode_address,
                travel_time_func=self.calculate_travel_time
            )
        except Exception as e:
            logger.error(f"Error al crear rutas optimizadas: {str(e)}")
            return {}

    @staticmethod
    def csv_to_user_dict(csv_file_path: str, user_key_field: str = "email") -> list[dict]:
        """
        Convierte un archivo CSV en una lista de diccionarios donde cada elemento representa un usuario.

        Args:
            csv_file_path (str): Ruta al archivo CSV
            user_key_field (str): Campo que se usará como clave para identificar a cada usuario (por defecto: "email")

        Returns:
            list: Lista de diccionarios donde cada diccionario contiene los datos de un usuario
        """
        try:

            with open(csv_file_path, 'rb') as raw_file:
                result = chardet.detect(raw_file.read())
                encoding = result['encoding']
                confidence = result['confidence']

            logger.info(f"Codificación detectada: {encoding} (confianza: {confidence:.2f})")

            # Lista de codificaciones a probar si la detección automática falla
            encodings_to_try = [encoding, 'latin-1', 'iso-8859-1', 'windows-1252', 'utf-8']

            user_list = []
            success = False

            # Intentar con diferentes codificaciones hasta que una funcione
            for enc in encodings_to_try:
                try:
                    with open(csv_file_path, 'r', encoding=enc) as csv_file:
                        csv_reader = csv.DictReader(csv_file, delimiter=';')

                        for row in csv_reader:
                            # Verificar si el campo clave existe en la fila
                            if user_key_field not in row:
                                logger.warning(f"El campo '{user_key_field}' no existe en la fila: {row}")
                                # Intentar usar el primer campo como clave si el campo especificado no existe
                                if len(row) > 0:
                                    first_key = list(row.keys())[0]
                                    user_key = row[first_key]
                                    logger.warning(f"Usando '{first_key}' como clave alternativa: {user_key}")
                                else:
                                    continue
                            else:
                                user_key = row[user_key_field]

                            # Si la clave está vacía, generar una clave única
                            if not user_key or user_key.strip() == "":
                                user_key = f"usuario_{len(user_list) + 1}"
                                logger.warning(f"Clave vacía, generando clave automática: {user_key}")
                                row[user_key_field] = user_key

                            # Añadir el diccionario de usuario a la lista
                            user_list.append(row)

                    success = True
                    logger.info(f"CSV procesado correctamente con codificación: {enc}")
                    break

                except UnicodeDecodeError:
                    logger.warning(f"No se pudo decodificar el archivo con codificación: {enc}")
                    continue

            if not success:
                logger.error("No se pudo procesar el archivo CSV con ninguna codificación")
                return []

            logger.info(f"CSV convertido a lista: {len(user_list)} usuarios procesados")
            return user_list

        except FileNotFoundError:
            logger.error(f"No se encontró el archivo CSV: {csv_file_path}")
            return []
        except Exception as e:
            logger.error(f"Error al procesar el archivo CSV: {str(e)}")
            return []
