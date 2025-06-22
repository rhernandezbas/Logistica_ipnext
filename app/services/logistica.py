import os

from functools import lru_cache

from dotenv import load_dotenv
import requests
from app.utils.logger import get_logger

logger = get_logger(__name__)

class Logistica:
    """ """

    def __init__(self):
        """ constructor """
        load_dotenv()
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

    @staticmethod
    def prioridad_tickets_by_date(tickets: list[dict])->list[dict]:
        """" """
        try:
            sorted_tickets = sorted(tickets, key=lambda x: x["creacion"])
            logger.info(f"Tickets priorizados: {len(sorted_tickets)} tickets ordenados por antigüedad")
            return sorted_tickets
        except Exception as e:
            logger.error(f"Error al priorizar tickets: {str(e)}")
            return tickets

    def segmentar_tickets_by_city(self, tickets: list[dict])->dict:
        """" """
        try:
            for ticket in tickets:
                encontrado = False
                for city in self.citys.keys():
                    if city != "else" and city.lower() in ticket['direccion'].lower():
                        self.citys[city].append(ticket)
                        encontrado = True
                        break

                if not encontrado:
                    self.citys["else"].append(ticket)

            logger.info(f"Tickets segmentados por ciudad: {len(self.citys)} ciudades")
            return self.citys
        except Exception as e:
            logger.error(f"Error al segmentar tickets: {str(e)}")
            return {}  # Devolvemos un diccionario vacío en caso de error

    def calculate_travel_time(self, origin: str, destination: str, consider_traffic: bool = True):
        """
        Calcula el tiempo estimado de viaje entre dos puntos usando la API de Distance Matrix de Google Maps.
        
        Args:
            origin (str): Coordenadas de origen en formato "latitud,longitud"
            destination (str): Coordenadas de destino en formato "latitud,longitud"
            consider_traffic (bool, optional): Si se debe considerar el tráfico actual. Por defecto es True.
            
        Returns:
            dict: Diccionario con información del tiempo de viaje:
                - duration_seconds: Tiempo en segundos sin considerar tráfico
                - duration_text: Tiempo formateado sin considerar tráfico (ej: "30 minutos")
                - duration_in_traffic_seconds: Tiempo en segundos considerando tráfico (si se solicitó)
                - duration_in_traffic_text: Tiempo formateado considerando tráfico (ej: "45 minutos")
                - distance_meters: Distancia en metros
                - distance_text: Distancia formateada (ej: "5.2 km")
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

    def segmentar_tickets_by_distance(self):
        """ """

    def asignar_tecnicos(self,tickets: list):
        """"""
        try:
            for city in self.citys:
                if city in tickets:
                    print(f"asignar_tecnicos a {city}")
                else:
                    print(f"no asignar_tecnicos a {city}")
            return True
        except Exception as e:
            print(f"Exception while asigning tecnicos: {str(e)}")
            return False

tickets = [
        {
            "id": 1,
            "nombre": "Ana María González",
            "edad": 34,
            "telefono": "2324-567890",
            "email": "anamar.gonzalez@email.com",
            "direccion": "Av. 39 N° 245, chivilcoy, Buenos Aires",
            "ocupacion": "Contadora",
            "creacion": "2023-09-12",
            "distancia": 2
        },
        {
            "id": 2,
            "nombre": "Carlos Eduardo Ramírez",
            "edad": 28,
            "telefono": "2324-456123",
            "email": "carlos.ramirez85@email.com",
            "direccion": "Calle 26 N° 156, Mercedes, Buenos Aires",
            "ocupacion": "Mecánico",
            "creacion": "2023-02-18"
        },
        {
            "id": 3,
            "nombre": "María Sol Fernández",
            "edad": 41,
            "telefono": "2324-789456",
            "email": "marisol.fernandez@email.com",
            "direccion": "Av. 6 N° 89, Mercedes, Buenos Aires",
            "ocupacion": "Docente",
            "creacion": "2023-11-25"
        },
        {
            "id": 4,
            "nombre": "Roberto Daniel López",
            "edad": 52,
            "telefono": "2324-321654",
            "email": "rd.lopez@email.com",
            "direccion": "Calle 25 N° 312, Mercedes, Buenos Aires",
            "ocupacion": "Comerciante",
            "creacion": "2023-04-07"
        },
        {
            "id": 5,
            "nombre": "Lucía Beatriz Morales",
            "edad": 29,
            "telefono": "2324-654987",
            "email": "lucia.morales@email.com",
            "direccion": "Av. 12 N° 178, lobos, Buenos Aires",
            "ocupacion": "Enfermera",
            "creacion": "2023-01-15"
        },
        {
            "id": 6,
            "nombre": "Juan Pablo Herrera",
            "edad": 36,
            "telefono": "2324-147258",
            "email": "jp.herrera@email.com",
            "direccion": "Calle 30 N° 267, Mercedes, Buenos Aires",
            "ocupacion": "Electricista",
            "creacion": "2023-12-03"
        },
        {
            "id": 7,
            "nombre": "Silvana Patricia Díaz",
            "edad": 45,
            "telefono": "2324-369741",
            "email": "silvana.diaz@email.com",
            "direccion": "Av. San Martín N° 543, Mercedes, Buenos Aires",
            "ocupacion": "Peluquera",
            "creacion": "2023-06-21"
        },
        {
            "id": 8,
            "nombre": "Miguel Ángel Castillo",
            "edad": 33,
            "telefono": "2324-852963",
            "email": "mcastillo@email.com",
            "direccion": "Calle 23 N° 134, Mercedes, Buenos Aires",
            "ocupacion": "Programador",
            "creacion": "2023-03-29"
        },
        {
            "id": 9,
            "nombre": "Carmen Estela Vega",
            "edad": 38,
            "telefono": "2324-741852",
            "email": "carmen.vega@email.com",
            "direccion": "Av. Rivadavia N° 421, Mercedes, Buenos Aires",
            "ocupacion": "Farmacéutica",
            "creacion": "2023-08-16"
        },
        {
            "id": 10,
            "nombre": "Diego Sebastián Torres",
            "edad": 42,
            "telefono": "2324-963852",
            "email": "diego.torres@email.com",
            "direccion": "Calle 28 N° 198, Mercedes, Buenos Aires",
            "ocupacion": "Veterinario",
            "creacion": "2023-10-04"
        }
    ]