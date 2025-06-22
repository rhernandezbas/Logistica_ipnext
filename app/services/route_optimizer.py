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

    def __init__(self, google_maps_api_key, default_reference_point, installation_times, use_llm=False):
        """
        Constructor para el optimizador de rutas.
        
        Args:
            google_maps_api_key: API key para Google Maps
            default_reference_point: Punto de referencia inicial para las rutas (lat, lng)
            installation_times: Diccionario con tiempos de instalación según tipo
            use_llm: Si es True, utiliza un modelo LLM para optimizar las rutas
        """
        self.google_maps_api_key = google_maps_api_key
        self.default_reference_point = default_reference_point
        self.installation_times = installation_times
        self.use_llm = use_llm
        
        # Constantes de tiempo (en horas)
        self.work_start = 9.5  # 9:30 AM
        self.work_end = 18.0   # 6:00 PM
        self.lunch_break = 1.0  # 1 hora de almuerzo
        self.lunch_threshold = self.work_start + 4  # Umbral para almuerzo (4 horas después del inicio)
    
    def optimize_routes(self, clients, geocode_func, travel_time_func):
        """
        Crea rutas optimizadas para visitar clientes, agrupados por localidad.
        
        Args:
            clients: Lista de diccionarios con información de clientes
            geocode_func: Función para geocodificar direcciones
            travel_time_func: Función para calcular tiempo de viaje
            
        Returns:
            Un diccionario con rutas optimizadas por localidad y una lista de usuarios con errores
        """
        try:
            # Agrupar clientes por localidad
            clients_by_locality, initial_errors = self._group_clients_by_locality(clients)
            
            # Si está habilitado el LLM, usar ese método de optimización
            if self.use_llm:
                logger.info("Utilizando optimización basada en LLM")
                
                # Primero, obtener las coordenadas para todos los clientes
                clients_by_locality_with_coords = {}
                all_geolocation_errors = initial_errors.copy() if initial_errors else []
                
                for locality, locality_clients in clients_by_locality.items():
                    clients_with_coords, locality_errors = self._get_clients_with_coordinates(
                        locality_clients, 
                        geocode_func, 
                        travel_time_func
                    )
                    
                    if locality_errors:
                        all_geolocation_errors.extend(locality_errors)
                    
                    if clients_with_coords:
                        clients_by_locality_with_coords[locality] = clients_with_coords
                
                # Usar el optimizador LLM con los clientes que tienen coordenadas
                optimized_routes = self.llm_optimizer.optimize_routes_with_llm(clients_by_locality_with_coords)
                
                # Asegurarse de que los errores de geolocalización estén incluidos
                if "usuarios_con_errores" in optimized_routes:
                    optimized_routes["usuarios_con_errores"].extend(all_geolocation_errors)
                else:
                    optimized_routes["usuarios_con_errores"] = all_geolocation_errors
                
                return optimized_routes
            
            # Si no está habilitado el LLM, usar el método tradicional
            else:
                logger.info("Utilizando optimización tradicional")
                
                # Resultado: rutas optimizadas por localidad
                optimized_routes = {}
                all_geolocation_errors = initial_errors.copy() if initial_errors else []
                
                # Procesar cada localidad
                for locality, locality_clients in clients_by_locality.items():
                    logger.info(f"Optimizando rutas para {locality} con {len(locality_clients)} clientes")
                    
                    # Obtener clientes con coordenadas y ordenados por proximidad
                    clients_with_coords, locality_errors = self._get_clients_with_coordinates(
                        locality_clients, 
                        geocode_func, 
                        travel_time_func
                    )
                    
                    # Agregar errores de esta localidad a la lista general
                    if locality_errors:
                        all_geolocation_errors.extend(locality_errors)
                    
                    # Crear rutas optimizadas para esta localidad
                    locality_routes = self._create_city_routes(
                        clients_with_coords, 
                        travel_time_func
                    )
                    
                    # Agregar rutas de esta localidad al resultado global con el formato requerido
                    for i, route in enumerate(locality_routes, 1):
                        route_key = f"{locality}_ruta_{i}"
                        optimized_routes[route_key] = route['clients']
                
                # Agregar lista de usuarios con errores de geolocalización
                optimized_routes["usuarios_con_errores"] = all_geolocation_errors
                
                logger.info(f"Rutas optimizadas creadas para {len(clients_by_locality)} localidades")
                return optimized_routes
            
        except Exception as e:
            logger.error(f"Error al crear rutas optimizadas: {str(e)}")
            return {"usuarios_con_errores": []}
    
    def _group_clients_by_locality(self, clients):
        """
        Agrupa los clientes por localidad según el campo 'Localidad'.
        
        Args:
            clients: Lista de diccionarios con información de clientes
        Returns:
            Tupla con (diccionario de clientes agrupados por localidad, lista de clientes con errores)
        """
        clients_by_locality = {}
        initial_errors = []
        
        for client in clients:
            # Determinar la localidad del cliente usando el campo 'Localidad'
            locality = client.get('Localidad', 'sin_localidad').lower()
            
            # Si la localidad está vacía, usar 'sin_localidad'
            if not locality or locality.strip() == "":
                locality = 'sin_localidad'
            
            # Normalizar el nombre de la localidad para usar como clave
            locality = locality.replace(" ", "_")
            
            if locality not in clients_by_locality:
                clients_by_locality[locality] = []
            
            clients_by_locality[locality].append(client)
        
        return clients_by_locality, initial_errors
    
    def _get_clients_with_coordinates(self, clients, geocode_func, travel_time_func):
        """
        Obtiene las coordenadas geográficas de los clientes y los ordena por proximidad
        al punto de referencia.
        
        Args:
            clients: Lista de clientes de una localidad
            geocode_func: Función para geocodificar direcciones
            travel_time_func: Función para calcular tiempo de viaje
            
        Returns:
            Lista de clientes con coordenadas, ordenados por proximidad
        """
        clients_with_coords = []
        geolocation_errors = []
        
        for client in clients:
            try:
                # Obtener coordenadas del cliente
                address = client['Domicilio']
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
                    else:
                        # Error al calcular tiempo de viaje
                        error_client = client.copy()
                        error_client['error_type'] = 'error_calculo_tiempo_viaje'
                        geolocation_errors.append(error_client)
                else:
                    # Error en geocodificación
                    error_client = client.copy()
                    error_client['error_type'] = 'error_geocodificacion'
                    geolocation_errors.append(error_client)
            except Exception as e:
                # Error general
                error_client = client.copy()
                error_client['error_type'] = f'error_general: {str(e)}'
                geolocation_errors.append(error_client)
        
        # Ordenar por tiempo de viaje desde el punto de referencia
        clients_with_coords.sort(key=lambda x: x['travel_time_from_start'])
        return clients_with_coords, geolocation_errors
    
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
