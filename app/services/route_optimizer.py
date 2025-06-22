"""
Módulo para la optimización de rutas de clientes.
"""
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RouteOptimizer:
    """
    Clase para optimizar rutas de visita a clientes, considerando
    restricciones de tiempo, distancias y tipos de instalación.
    """

    def __init__(self, google_maps_api_key, default_reference_point, installation_times):
        """
        Constructor para el optimizador de rutas.
        
        Args:
            google_maps_api_key: API key para Google Maps
            default_reference_point: Punto de referencia inicial para las rutas (lat, lng)
            installation_times: Diccionario con tiempos de instalación según tipo
        """
        self.google_maps_api_key = google_maps_api_key
        self.default_reference_point = default_reference_point
        self.installation_times = installation_times
        
        # Constantes de tiempo (en horas)
        self.work_start = 9.5  # 9:30 AM
        self.work_end = 18.0   # 6:00 PM
        self.lunch_break = 1.0  # 1 hora de almuerzo
        self.lunch_threshold = self.work_start + 4  # Umbral para almuerzo (4 horas después del inicio)
    
    def optimize_routes(self, clients, city_mapping, geocode_func, travel_time_func):
        """
        Crea rutas optimizadas para visitar clientes, agrupados por ciudad.
        
        Args:
            clients: Lista de diccionarios con información de clientes
            city_mapping: Diccionario con las ciudades disponibles
            geocode_func: Función para geocodificar direcciones
            travel_time_func: Función para calcular tiempo de viaje
            
        Returns:
            Un diccionario con rutas optimizadas por día y ciudad
        """
        try:
            # Agrupar clientes por ciudad
            clients_by_city = self._group_clients_by_city(clients, city_mapping)
            
            # Resultado: rutas optimizadas por día
            optimized_routes = {}
            
            # Procesar cada ciudad
            for city, city_clients in clients_by_city.items():
                logger.info(f"Optimizando rutas para {city} con {len(city_clients)} clientes")
                
                # Obtener clientes con coordenadas y ordenados por proximidad
                clients_with_coords = self._get_clients_with_coordinates(
                    city_clients, 
                    geocode_func, 
                    travel_time_func
                )
                
                # Crear rutas optimizadas para esta ciudad
                city_routes = self._create_city_routes(
                    clients_with_coords, 
                    travel_time_func
                )
                
                # Agregar rutas de esta ciudad al resultado global
                optimized_routes[city] = city_routes
            
            logger.info(f"Rutas optimizadas creadas para {len(optimized_routes)} ciudades")
            return optimized_routes
            
        except Exception as e:
            logger.error(f"Error al crear rutas optimizadas: {str(e)}")
            return {}
    
    def _group_clients_by_city(self, clients, city_mapping):
        """
        Agrupa los clientes por ciudad según su dirección.
        
        Args:
            clients: Lista de diccionarios con información de clientes
            city_mapping: Diccionario con las ciudades disponibles
            
        Returns:
            Diccionario con clientes agrupados por ciudad
        """
        clients_by_city = {}
        for client in clients:
            city = "else"
            # Determinar la ciudad del cliente
            for city_name in city_mapping.keys():
                if city_name != "else" and city_name.lower() in client['direccion'].lower():
                    city = city_name
                    break
            
            if city not in clients_by_city:
                clients_by_city[city] = []
            clients_by_city[city].append(client)
        
        return clients_by_city
    
    def _get_clients_with_coordinates(self, clients, geocode_func, travel_time_func):
        """
        Obtiene las coordenadas geográficas de los clientes y los ordena por proximidad
        al punto de referencia.
        
        Args:
            clients: Lista de clientes de una ciudad
            geocode_func: Función para geocodificar direcciones
            travel_time_func: Función para calcular tiempo de viaje
            
        Returns:
            Lista de clientes con coordenadas, ordenados por proximidad
        """
        clients_with_coords = []
        for client in clients:
            # Obtener coordenadas del cliente
            address = client['direccion']
            coords = geocode_func(address)
            
            if coords and 'latitude' in coords and 'longitude' in coords:
                client_coords = f"{coords['latitude']},{coords['longitude']}"
                
                # Calcular tiempo de viaje desde el punto de referencia
                travel_info = travel_time_func(self.default_reference_point, client_coords)
                
                if travel_info:
                    # Guardar información relevante
                    client_with_coords = client.copy()
                    client_with_coords['coordinates'] = client_coords
                    client_with_coords['travel_time_from_start'] = travel_info['duration_seconds'] / 3600  # Convertir a horas
                    clients_with_coords.append(client_with_coords)
        
        # Ordenar por tiempo de viaje desde el punto de referencia
        clients_with_coords.sort(key=lambda x: x['travel_time_from_start'])
        return clients_with_coords
    
    def _create_city_routes(self, clients, travel_time_func):
        """
        Crea rutas optimizadas para una ciudad específica.
        
        Args:
            clients: Lista de clientes con coordenadas
            travel_time_func: Función para calcular tiempo de viaje
            
        Returns:
            Lista de rutas optimizadas para la ciudad
        """
        city_routes = []
        current_route = []
        current_time = self.work_start
        current_location = self.default_reference_point
        day_counter = 1
        
        for client in clients:
            # Calcular tiempo de viaje y de instalación
            travel_info, travel_time, installation_time = self._calculate_times(
                client, 
                current_location, 
                travel_time_func
            )
            
            if travel_info is None:
                continue
            
            # Verificar si hay tiempo suficiente para este cliente en la ruta actual
            total_time_needed = travel_time + installation_time
            
            # Verificar si necesitamos crear una nueva ruta para el día siguiente
            if self._should_create_new_route(current_time, total_time_needed):
                if current_route:  # Solo si la ruta actual tiene clientes
                    # Guardar la ruta actual
                    city_routes.append(self._create_route_dict(
                        day_counter, 
                        current_route, 
                        self.work_start, 
                        current_time
                    ))
                    
                    # Iniciar una nueva ruta para el día siguiente
                    day_counter += 1
                    current_route = []
                    current_time = self.work_start
                    current_location = self.default_reference_point
                    
                    # Recalcular el tiempo de viaje desde el punto de inicio
                    travel_info, travel_time, _ = self._calculate_times(
                        client, 
                        current_location, 
                        travel_time_func
                    )
                    if travel_info is None:
                        continue
            
            # Considerar el almuerzo si estamos en el rango adecuado
            if self._should_take_lunch(current_time, total_time_needed):
                current_time += self.lunch_break
            
            # Agregar cliente a la ruta actual
            client_info = self._prepare_client_info(client, current_time, travel_time, installation_time)
            current_route.append(client_info)
            
            # Actualizar tiempo y ubicación actuales
            current_time += total_time_needed
            current_location = client['coordinates']
        
        # Agregar la última ruta si tiene clientes
        if current_route:
            city_routes.append(self._create_route_dict(
                day_counter, 
                current_route, 
                self.work_start, 
                current_time
            ))
        
        return city_routes
    
    def _calculate_times(self, client, current_location, travel_time_func):
        """
        Calcula los tiempos de viaje e instalación para un cliente.
        
        Args:
            client: Información del cliente
            current_location: Ubicación actual (coordenadas)
            travel_time_func: Función para calcular tiempo de viaje
            
        Returns:
            Tupla con (travel_info, travel_time, installation_time)
        """
        # Calcular tiempo de viaje desde la ubicación actual
        travel_info = travel_time_func(current_location, client['coordinates'])
        
        if not travel_info:
            return None, 0, 0
        
        travel_time = travel_info['duration_seconds'] / 3600  # Convertir a horas
        
        # Determinar el tipo de instalación y su tiempo
        installation_time = self.installation_times.get('instalacion', 1.5)  # Valor predeterminado
        if 'tipo_instalacion' in client:
            if 'wireless' in client['tipo_instalacion'].lower():
                installation_time = self.installation_times.get('verificaciones_wirreles', 1.0)
            elif 'fibra' in client['tipo_instalacion'].lower():
                installation_time = self.installation_times.get('verificaciones_fibra', 1.0)
        
        return travel_info, travel_time, installation_time
    
    def _should_create_new_route(self, current_time, total_time_needed):
        """
        Determina si se debe crear una nueva ruta para el día siguiente.
        
        Args:
            current_time: Hora actual
            total_time_needed: Tiempo total necesario para el cliente
            
        Returns:
            True si se debe crear una nueva ruta, False en caso contrario
        """
        # Si agregar este cliente excede el horario de trabajo, crear una nueva ruta
        lunch_adjustment = 0.5 if current_time < self.lunch_threshold else 0
        
        return current_time + total_time_needed > self.work_end - lunch_adjustment
    
    def _should_take_lunch(self, current_time, total_time_needed):
        """
        Determina si se debe tomar el almuerzo en este momento.
        
        Args:
            current_time: Hora actual
            total_time_needed: Tiempo total necesario para el cliente
            
        Returns:
            True si se debe tomar el almuerzo, False en caso contrario
        """
        return current_time <= self.lunch_threshold < current_time + total_time_needed

    def _prepare_client_info(self, client, current_time, travel_time, installation_time):
        """
        Prepara la información del cliente para incluirla en la ruta.
        
        Args:
            client: Información del cliente
            current_time: Hora actual
            travel_time: Tiempo de viaje
            installation_time: Tiempo de instalación
            
        Returns:
            Diccionario con la información del cliente para la ruta
        """
        client_info = client.copy()
        client_info['estimated_arrival'] = current_time
        client_info['travel_time'] = travel_time
        client_info['installation_time'] = installation_time
        client_info['estimated_completion'] = current_time + travel_time + installation_time
        
        return client_info
    
    def _create_route_dict(self, day, clients, start_time, end_time):
        """
        Crea un diccionario con la información de una ruta.
        
        Args:
            day: Número de día
            clients: Lista de clientes en la ruta
            start_time: Hora de inicio
            end_time: Hora de finalización
            
        Returns:
            Diccionario con la información de la ruta
        """
        return {
            'day': day,
            'clients': clients,
            'start_time': start_time,
            'end_time': end_time
        }
