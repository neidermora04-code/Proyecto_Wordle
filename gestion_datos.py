"""
Módulo de Gestión de Colecciones y Generación de Reportes Competitivos (Lab 02, 03 y 04).
Sincroniza automáticamente Jugadores (Ranking Global), Partidas y Palabras
entre todas las consolas conectadas a Google Sheets y el respaldo JSON local.
"""

# Importamos anotaciones de tipos para documentar colecciones y retornos
from typing import Dict, List, Set, Any, Optional, Tuple
# Importamos las clases de dominio definidas en modelos.py
from modelos import Participante, JugadorRegistrado, JugadorInvitado, RegistroPartida
# Importamos las validaciones y la excepción personalizada del proyecto
from validaciones import ValidadorDatos, ErrorValidacionWordle
# Importamos los gestores de persistencia local (JSON/CSV/TXT) y en la nube (Google Sheets)
from persistencia import GestorArchivosLocales, GestorGoogleSheets
# Importamos la configuración general del juego
from config import CONFIG_JUEGO


class GestorColecciones:
    """
    Clase que administra las colecciones principales del sistema en memoria y coordina su
    persistencia en tiempo real en Google Sheets (modo competitivo multi-consola) y en JSON local.
    """

    def __init__(self, gestor_local: GestorArchivosLocales, gestor_nube: GestorGoogleSheets) -> None:
        # Guardamos las referencias al gestor de archivos locales y al gestor de Google Sheets (Composición)
        self._gestor_local = gestor_local
        self._gestor_nube = gestor_nube

        # Tres colecciones principales en memoria con distinto propósito (Lab 02):
        # 1. Diccionario de objetos JugadorRegistrado (búsqueda rápida por alias en mayúsculas)
        self._jugadores: Dict[str, JugadorRegistrado] = {}
        # 2. Lista secuencial de objetos RegistroPartida (historial cronológico de partidas)
        self._partidas: List[RegistroPartida] = []
        # 3. Conjunto (Set) de cadenas con las palabras válidas de 5 letras (sin repetidos)
        self._catalogo_palabras: Set[str] = set()

        # Al iniciar, carga y combina automáticamente los datos locales con los de Google Sheets
        self.sincronizar_desde_nube_y_local()

    def sincronizar_desde_nube_y_local(self) -> None:
        """
        Descarga los jugadores registrados, el historial de partidas y las palabras
        desde Google Sheets (para ver a todos los competidores en tiempo real) y los
        combina con el respaldo JSON local.
        """
        # Paso 1: Leer los archivos JSON locales desde la carpeta 'datos/'
        jugadores_locales, partidas_locales, palabras_locales = self._gestor_local.cargar_estado_json()

        # Comprensión de diccionario: convierte cada diccionario leído del JSON en un objeto JugadorRegistrado
        self._jugadores = {
            clave.upper(): JugadorRegistrado.desde_diccionario(datos)
            for clave, datos in jugadores_locales.items()
        }

        # Paso 2: Si hay conexión a internet con Google Sheets, descargar jugadores y partidas globales
        if self._gestor_nube.esta_conectado:
            jugadores_nube = self._gestor_nube.obtener_jugadores_nube()
            for clave, datos_nube in jugadores_nube.items():
                obj_nube = JugadorRegistrado.desde_diccionario(datos_nube)
                if clave not in self._jugadores:
                    # Si el jugador fue creado en el computador de otro compañero, lo agregamos aquí
                    self._jugadores[clave] = obj_nube
                else:
                    # Si ya existía localmente, conservamos la versión que tenga más partidas registradas
                    if obj_nube.partidas_jugadas >= self._jugadores[clave].partidas_jugadas:
                        self._jugadores[clave] = obj_nube

            # Descargamos todas las partidas de la pestaña 'Puntajes' de Google Sheets
            partidas_nube = self._gestor_nube.obtener_partidas_nube()
            if partidas_nube:
                # Comprensión de lista: transforma cada diccionario en un objeto RegistroPartida
                self._partidas = [RegistroPartida.desde_diccionario(p) for p in partidas_nube]
                # Reconstruye o actualiza estadísticas de jugadores a partir de las partidas jugadas en la nube
                self._reconciliar_jugadores_desde_partidas()
            else:
                self._partidas = [RegistroPartida.desde_diccionario(p) for p in partidas_locales]
        else:
            # Si estamos en modo Offline, trabajamos con las partidas del archivo JSON local
            self._partidas = [RegistroPartida.desde_diccionario(p) for p in partidas_locales]

        # Paso 3: Sincronizar el conjunto (Set) de palabras en español y guardar el estado consolidado
        self._catalogo_palabras = self._gestor_nube.obtener_palabras(palabras_locales)
        self.guardar_cambios(sincronizar_jugadores_nube=True)

    def _reconciliar_jugadores_desde_partidas(self) -> None:
        """
        Asegura que cualquier jugador registrado que haya jugado en otra consola
        aparezca en la tabla de Jugadores con sus estadísticas reales calculadas.
        """
        conteo_por_jugador: Dict[str, Dict[str, Any]] = {}
        # Recorremos todas las partidas para sumar partidas jugadas, victorias, rachas y puntos de cada alias
        for p in self._partidas:
            if p.tipo_jugador == "Invitado":
                continue
            clave = p.jugador.strip().upper()
            if clave not in conteo_por_jugador:
                conteo_por_jugador[clave] = {
                    "alias": p.jugador.strip(),
                    "pj": 0,
                    "pg": 0,
                    "pts": 0,
                    "racha": 0
                }
            conteo_por_jugador[clave]["pj"] += 1
            if p.gano:
                conteo_por_jugador[clave]["pg"] += 1
                conteo_por_jugador[clave]["racha"] += 1
            else:
                conteo_por_jugador[clave]["racha"] = 0
            conteo_por_jugador[clave]["pts"] += p.puntaje

        # Actualizamos o creamos los objetos JugadorRegistrado según el conteo real de partidas
        for clave, stats in conteo_por_jugador.items():
            if clave not in self._jugadores:
                self._jugadores[clave] = JugadorRegistrado(
                    alias=stats["alias"],
                    categoria="Estándar",
                    partidas_jugadas=stats["pj"],
                    partidas_ganadas=stats["pg"],
                    puntaje_acumulado=stats["pts"],
                    racha_actual=stats["racha"]
                )
            elif stats["pj"] > self._jugadores[clave].partidas_jugadas:
                j_actual = self._jugadores[clave]
                self._jugadores[clave] = JugadorRegistrado(
                    alias=j_actual.alias,
                    categoria=j_actual.categoria,
                    partidas_jugadas=stats["pj"],
                    partidas_ganadas=stats["pg"],
                    puntaje_acumulado=stats["pts"],
                    racha_actual=stats["racha"],
                    activo=j_actual.activo
                )

    def guardar_cambios(self, sincronizar_jugadores_nube: bool = True) -> bool:
        """
        Persiste todas las colecciones en los archivos JSON locales y actualiza
        la pestaña competitiva 'Jugadores' en Google Sheets.
        """
        # Serializamos los objetos a diccionarios usando comprensiones de diccionario y de lista
        jugadores_serializados = {
            clave: obj.a_diccionario() for clave, obj in self._jugadores.items()
        }
        partidas_serializadas = [p.a_diccionario() for p in self._partidas]

        # Guardamos en los archivos JSON locales ('datos/partidas_y_jugadores.json' y 'diccionario_personalizado.json')
        exito_local = self._gestor_local.guardar_estado_json(
            jugadores_dict=jugadores_serializados,
            partidas_lista=partidas_serializadas,
            palabras_catalogo=self._catalogo_palabras
        )

        # Si está habilitada la sincronización con la nube y estamos online, subimos el ranking actualizado
        if sincronizar_jugadores_nube and self._gestor_nube.esta_conectado:
            ranking_ordenado = [j.a_diccionario() for j in self.listar_jugadores(solo_activos=False)]
            self._gestor_nube.sincronizar_tabla_jugadores_nube(ranking_ordenado)

        return exito_local

    # =========================================================================
    # 1. GESTIÓN DE JUGADORES (Registrar, Consultar, Actualizar, Cambiar Estado)
    # =========================================================================
    @property
    def total_jugadores(self) -> int:
        """Devuelve la cantidad total de jugadores registrados en el diccionario."""
        return len(self._jugadores)

    def registrar_jugador(self, alias: str, categoria: str = "Estándar") -> JugadorRegistrado:
        """
        Descarga primero la lista actual de la nube para evitar duplicados entre consolas,
        registra al nuevo jugador y sube inmediatamente la tabla actualizada a Google Sheets.
        """
        if self._gestor_nube.esta_conectado:
            self.sincronizar_desde_nube_y_local()

        # Validamos que el alias y la categoría cumplan las reglas de longitud y formato
        alias_limpio = ValidadorDatos.validar_alias(alias)
        categoria_limpia = ValidadorDatos.validar_categoria(categoria)
        clave = alias_limpio.upper()

        # Si el alias ya existe en el diccionario, lanzamos nuestra excepción de negocio
        if clave in self._jugadores:
            raise ErrorValidacionWordle(f"El jugador '{alias_limpio}' ya se encuentra registrado en la base de datos.")

        # Instanciamos el nuevo objeto JugadorRegistrado y lo guardamos en el diccionario
        nuevo = JugadorRegistrado(alias=alias_limpio, categoria=categoria_limpia)
        self._jugadores[clave] = nuevo
        self.guardar_cambios(sincronizar_jugadores_nube=True)
        self._gestor_local.registrar_bitacora_txt(f"Jugador registrado en BD local y Google Sheets: {alias_limpio} ({categoria_limpia})")
        return nuevo

    def obtener_o_crear_participante(self, alias: str, como_invitado: bool = False) -> Participante:
        """
        Retorna un `JugadorInvitado` si eligió jugar sin registro, o busca/crea un
        `JugadorRegistrado` sincronizado con Google Sheets (demostrando Polimorfismo).
        """
        if self._gestor_nube.esta_conectado:
            self.sincronizar_desde_nube_y_local()

        alias_limpio = ValidadorDatos.validar_alias(alias)
        clave = alias_limpio.upper()

        # Si juega como invitado, retorna una instancia de la subclase JugadorInvitado
        if como_invitado:
            return JugadorInvitado(alias=alias_limpio)

        # Si juega como registrado y aún no existe en el diccionario, lo crea automáticamente
        if clave not in self._jugadores:
            self._jugadores[clave] = JugadorRegistrado(alias=alias_limpio)
            self.guardar_cambios(sincronizar_jugadores_nube=True)
        return self._jugadores[clave]

    def buscar_jugador(self, alias: str) -> Optional[JugadorRegistrado]:
        """Busca un jugador registrado por su alias (sin importar mayúsculas o minúsculas)."""
        return self._jugadores.get(alias.strip().upper())

    def listar_jugadores(self, solo_activos: bool = False, refrescar_nube: bool = False) -> List[JugadorRegistrado]:
        """Retorna la lista de jugadores ordenada competitivamente por puntaje, % de victorias y ganadas."""
        if refrescar_nube and self._gestor_nube.esta_conectado:
            self.sincronizar_desde_nube_y_local()

        # Filtra los jugadores según si se pidieron solo los activos o todos
        lista = [
            j for j in self._jugadores.values()
            if (not solo_activos or j.activo)
        ]
        # Ordena de mayor a menor (reverse=True) usando una función lambda con criterio triple de desempate
        return sorted(lista, key=lambda j: (j.puntaje_acumulado, j.porcentaje_victorias, j.partidas_ganadas), reverse=True)

    def actualizar_jugador(
        self,
        alias_actual: str,
        nuevo_alias: Optional[str] = None,
        nueva_categoria: Optional[str] = None,
        nuevo_estado_activo: Optional[bool] = None
    ) -> JugadorRegistrado:
        """Actualiza el alias, categoría o estado activo de un jugador y sincroniza con Google Sheets."""
        clave_actual = alias_actual.strip().upper()
        jugador = self._jugadores.get(clave_actual)
        if not jugador:
            raise ErrorValidacionWordle(f"No se encontró ningún jugador con el alias '{alias_actual}'.")

        # Si el usuario solicitó cambiar el alias del jugador:
        if nuevo_alias is not None and nuevo_alias.strip():
            alias_validado = ValidadorDatos.validar_alias(nuevo_alias)
            nueva_clave = alias_validado.upper()
            if nueva_clave != clave_actual and nueva_clave in self._jugadores:
                raise ErrorValidacionWordle(f"El nuevo alias '{alias_validado}' ya está ocupado por otro jugador.")
            # Eliminamos la clave antigua del diccionario, actualizamos el setter y reinsertamos con la nueva clave
            del self._jugadores[clave_actual]
            jugador.alias = alias_validado
            self._jugadores[nueva_clave] = jugador

        # Si solicitó cambiar la categoría (Estándar, VIP, Pro):
        if nueva_categoria is not None and nueva_categoria.strip():
            jugador.categoria = ValidadorDatos.validar_categoria(nueva_categoria)
        # Si solicitó activar o desactivar el perfil:
        if nuevo_estado_activo is not None:
            jugador.cambiar_estado_activo(nuevo_estado_activo)

        self.guardar_cambios(sincronizar_jugadores_nube=True)
        self._gestor_local.registrar_bitacora_txt(f"Jugador actualizado en BD: {jugador.alias}")
        return jugador

    # =========================================================================
    # 2. GESTIÓN DEL CATÁLOGO DE PALABRAS (Sets)
    # =========================================================================
    @property
    def catalogo_palabras(self) -> Set[str]:
        """Retorna una copia del conjunto (Set) de palabras activas."""
        return set(self._catalogo_palabras)

    def agregar_palabra_catalogo(self, nueva_palabra: str) -> str:
        """Valida y agrega una nueva palabra de 5 letras al conjunto local y a Google Sheets."""
        palabra_limpia = ValidadorDatos.validar_palabra_catalogo(nueva_palabra, CONFIG_JUEGO[0])
        if palabra_limpia in self._catalogo_palabras:
            raise ErrorValidacionWordle(f"La palabra '{palabra_limpia}' ya existe en el catálogo.")

        # .add() inserta el elemento en el conjunto (Set)
        self._catalogo_palabras.add(palabra_limpia)
        self.guardar_cambios(sincronizar_jugadores_nube=False)
        self._gestor_nube.agregar_palabra_nube(palabra_limpia)
        self._gestor_local.registrar_bitacora_txt(f"Palabra agregada al catálogo: {palabra_limpia}")
        return palabra_limpia

    def eliminar_palabra_catalogo(self, palabra: str) -> str:
        """Elimina una palabra existente del catálogo cuidando que siempre queden mínimo 5 palabras."""
        palabra_limpia = ValidadorDatos.normalizar_palabra(palabra)
        if palabra_limpia not in self._catalogo_palabras:
            raise ErrorValidacionWordle(f"La palabra '{palabra_limpia}' no existe en el catálogo.")
        if len(self._catalogo_palabras) <= 5:
            raise ErrorValidacionWordle("No se puede eliminar: el catálogo debe conservar al menos 5 palabras.")

        # .remove() quita la palabra del conjunto (Set)
        self._catalogo_palabras.remove(palabra_limpia)
        self.guardar_cambios(sincronizar_jugadores_nube=False)
        self._gestor_local.registrar_bitacora_txt(f"Palabra eliminada del catálogo: {palabra_limpia}")
        return palabra_limpia

    def buscar_palabras_por_prefijo_o_letra(self, criterio: str) -> List[str]:
        """Filtra y devuelve ordenadas todas las palabras del catálogo que contengan la letra o subcadena."""
        subcadena = ValidadorDatos.normalizar_palabra(criterio)
        return sorted([p for p in self._catalogo_palabras if subcadena in p])

    # =========================================================================
    # 3. REGISTRO Y FILTRADO DE PARTIDAS COMPETITIVAS
    # =========================================================================
    def registrar_partida_completada(
        self,
        participante: Participante,
        palabra_secreta: str,
        gano: bool,
        intentos_usados: int,
        max_intentos: int,
        dificultad: str,
        puntaje_base: int,
        palabras_intentadas: List[str]
    ) -> Tuple[RegistroPartida, bool]:
        """
        Actualiza el estado del participante, sube la partida con `append_row()` a la pestaña
        'Puntajes' y actualiza la tabla de posiciones en la pestaña 'Jugadores' de Google Sheets.
        """
        # Polimorfismo: si es JugadorRegistrado actualiza racha y estadísticas; si es Invitado calcula el 90%
        if isinstance(participante, JugadorRegistrado):
            puntaje_final = participante.registrar_resultado_partida(gano, puntaje_base)
        else:
            puntaje_final = participante.calcular_bonificacion(puntaje_base) if gano else 0

        # Genera un identificador único secuencial (ej. PART-001, PART-002...)
        id_nuevo = f"PART-{len(self._partidas) + 1:03d}"
        # Crea el objeto RegistroPartida (Composición)
        registro = RegistroPartida(
            id_partida=id_nuevo,
            jugador=participante.alias,
            tipo_jugador=participante.obtener_tipo(),
            palabra_secreta=palabra_secreta,
            gano=gano,
            intentos_usados=intentos_usados,
            max_intentos=max_intentos,
            dificultad=dificultad,
            puntaje=puntaje_final,
            palabras_intentadas=palabras_intentadas
        )

        # Agrega la partida a la lista histórica en memoria
        self._partidas.append(registro)

        # 1. Subir la fila de la partida a la pestaña 'Puntajes' de Google Sheets con append_row()
        subido_nube = self._gestor_nube.guardar_resultado(registro.a_diccionario())

        # 2. Guardar en JSON local y actualizar la tabla de ranking en la pestaña 'Jugadores'
        self.guardar_cambios(sincronizar_jugadores_nube=True)
        return (registro, subido_nube)

    def filtrar_partidas(
        self,
        alias_jugador: Optional[str] = None,
        solo_victorias: Optional[bool] = None,
        dificultad: Optional[str] = None,
        palabra_secreta: Optional[str] = None,
        refrescar_nube: bool = False
    ) -> List[RegistroPartida]:
        """Permite búsquedas y filtros combinados sobre todas las partidas registradas."""
        if refrescar_nube and self._gestor_nube.esta_conectado:
            self.sincronizar_desde_nube_y_local()

        resultado: List[RegistroPartida] = []
        # Recorre cada partida verificando los filtros opcionales que el usuario haya activado
        for p in self._partidas:
            if alias_jugador and alias_jugador.strip().upper() not in p.jugador.upper():
                continue
            if solo_victorias is not None and p.gano != solo_victorias:
                continue
            if dificultad and dificultad.strip().lower() not in p.dificultad.lower():
                continue
            if palabra_secreta and palabra_secreta.strip().upper() != p.palabra_secreta.upper():
                continue
            resultado.append(p)
        return resultado


class GeneradorReportes:
    """
    Clase especializada en generar resúmenes y reportes con información
    calculada, agrupada y filtrada a partir de las colecciones competitivas.
    """

    @staticmethod
    def generar_resumen_estadistico(
        partidas: List[RegistroPartida],
        jugadores: List[JugadorRegistrado],
        total_palabras: int
    ) -> Dict[str, Any]:
        """Calcula indicadores globales, agrupaciones por dificultad y el histograma de intentos."""
        total_partidas = len(partidas)
        # Comprensiones de listas para separar partidas ganadas y perdidas
        victorias = [p for p in partidas if p.gano]
        derrotas = [p for p in partidas if not p.gano]

        # Porcentaje global de victorias (evitando dividir por cero si no hay partidas)
        tasa_exito_global = round((len(victorias) / total_partidas) * 100.0, 2) if total_partidas > 0 else 0.0
        # Promedio de intentos requeridos para ganar
        promedio_intentos_victoria = (
            round(sum(p.intentos_usados for p in victorias) / len(victorias), 2)
            if victorias else 0.0
        )
        # Puntaje más alto logrado en una sola partida usando max()
        puntaje_maximo = max((p.puntaje for p in partidas), default=0)

        # Agrupación de métricas por Nivel de Dificultad usando un diccionario anidado
        agrupado_dificultad: Dict[str, Dict[str, int]] = {}
        for p in partidas:
            dif = p.dificultad
            if dif not in agrupado_dificultad:
                agrupado_dificultad[dif] = {"jugadas": 0, "victorias": 0, "puntos_totales": 0}
            agrupado_dificultad[dif]["jugadas"] += 1
            if p.gano:
                agrupado_dificultad[dif]["victorias"] += 1
            agrupado_dificultad[dif]["puntos_totales"] += p.puntaje

        # Diccionario por comprensión para contar cuántas victorias ocurrieron en 1, 2, 3... 7 intentos
        distribucion_intentos: Dict[int, int] = {i: 0 for i in range(1, 8)}
        for v in victorias:
            distribucion_intentos[v.intentos_usados] = distribucion_intentos.get(v.intentos_usados, 0) + 1

        # Conteo de frecuencia para hallar cuál ha sido la palabra secreta más jugada
        conteo_palabras: Dict[str, int] = {}
        for p in partidas:
            conteo_palabras[p.palabra_secreta] = conteo_palabras.get(p.palabra_secreta, 0) + 1
        palabra_mas_frecuente = (
            max(conteo_palabras.items(), key=lambda item: item[1])[0]
            if conteo_palabras else "N/A"
        )

        # Retorna todas las estadísticas empaquetadas en un diccionario listo para mostrarse en pantalla
        return {
            "total_partidas": total_partidas,
            "total_victorias": len(victorias),
            "total_derrotas": len(derrotas),
            "tasa_exito_global": tasa_exito_global,
            "promedio_intentos_victoria": promedio_intentos_victoria,
            "puntaje_maximo_partida": puntaje_maximo,
            "total_jugadores_registrados": len(jugadores),
            "total_palabras_catalogo": total_palabras,
            "palabra_mas_jugada": palabra_mas_frecuente,
            "agrupado_por_dificultad": agrupado_dificultad,
            "distribucion_intentos": distribucion_intentos
        }
