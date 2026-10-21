"""
Módulo de Gestión de Colecciones y Generación de Reportes Competitivos (Lab 02, 03 y 04).
Sincroniza automáticamente Jugadores (Ranking Global), Partidas y Palabras
entre todas las consolas conectadas a Google Sheets y el respaldo JSON local.
"""

from typing import Dict, List, Set, Any, Optional, Tuple
from modelos import Participante, JugadorRegistrado, JugadorInvitado, RegistroPartida
from validaciones import ValidadorDatos, ErrorValidacionWordle
from persistencia import GestorArchivosLocales, GestorGoogleSheets
from config import CONFIG_JUEGO


class GestorColecciones:
    """
    Clase que administra las colecciones principales del sistema y coordina su
    persistencia en tiempo real en Google Sheets (modo competitivo multi-consola) y en JSON local.
    """

    def __init__(self, gestor_local: GestorArchivosLocales, gestor_nube: GestorGoogleSheets) -> None:
        self._gestor_local = gestor_local
        self._gestor_nube = gestor_nube

        self._jugadores: Dict[str, JugadorRegistrado] = {}
        self._partidas: List[RegistroPartida] = []
        self._catalogo_palabras: Set[str] = set()

        self.sincronizar_desde_nube_y_local()

    def sincronizar_desde_nube_y_local(self) -> None:
        """
        Descarga los jugadores registrados, el historial de partidas y las palabras
        desde Google Sheets (para ver a todos los competidores en tiempo real) y los
        combina con el respaldo JSON local.
        """
        jugadores_locales, partidas_locales, palabras_locales = self._gestor_local.cargar_estado_json()

        # 1. Cargar jugadores locales base
        self._jugadores = {
            clave.upper(): JugadorRegistrado.desde_diccionario(datos)
            for clave, datos in jugadores_locales.items()
        }

        # 2. Si estamos conectados a Google Sheets, descargar jugadores y partidas de toda la comunidad
        if self._gestor_nube.esta_conectado:
            jugadores_nube = self._gestor_nube.obtener_jugadores_nube()
            for clave, datos_nube in jugadores_nube.items():
                obj_nube = JugadorRegistrado.desde_diccionario(datos_nube)
                if clave not in self._jugadores:
                    self._jugadores[clave] = obj_nube
                else:
                    # Conservar el estado con más partidas jugadas o actualizar desde la nube
                    if obj_nube.partidas_jugadas >= self._jugadores[clave].partidas_jugadas:
                        self._jugadores[clave] = obj_nube

            partidas_nube = self._gestor_nube.obtener_partidas_nube()
            if partidas_nube:
                self._partidas = [RegistroPartida.desde_diccionario(p) for p in partidas_nube]
                # Además, reconstruir automáticamente cualquier jugador que aparezca en Puntajes
                # y que aún no esté en la pestaña Jugadores
                self._reconciliar_jugadores_desde_partidas()
            else:
                self._partidas = [RegistroPartida.desde_diccionario(p) for p in partidas_locales]
        else:
            self._partidas = [RegistroPartida.desde_diccionario(p) for p in partidas_locales]

        # 3. Sincronizar catálogo de palabras en español
        self._catalogo_palabras = self._gestor_nube.obtener_palabras(palabras_locales)
        self.guardar_cambios(sincronizar_jugadores_nube=True)

    def _reconciliar_jugadores_desde_partidas(self) -> None:
        """
        Asegura que cualquier jugador registrado que haya jugado en otra consola
        aparezca en la tabla de Jugadores con sus estadísticas reales.
        """
        conteo_por_jugador: Dict[str, Dict[str, int]] = {}
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
        jugadores_serializados = {
            clave: obj.a_diccionario() for clave, obj in self._jugadores.items()
        }
        partidas_serializadas = [p.a_diccionario() for p in self._partidas]

        exito_local = self._gestor_local.guardar_estado_json(
            jugadores_dict=jugadores_serializados,
            partidas_lista=partidas_serializadas,
            palabras_catalogo=self._catalogo_palabras
        )

        if sincronizar_jugadores_nube and self._gestor_nube.esta_conectado:
            ranking_ordenado = [j.a_diccionario() for j in self.listar_jugadores(solo_activos=False)]
            self._gestor_nube.sincronizar_tabla_jugadores_nube(ranking_ordenado)

        return exito_local

    # =========================================================================
    # 1. GESTIÓN DE JUGADORES (Registrar, Consultar, Actualizar, Cambiar Estado)
    # =========================================================================
    @property
    def total_jugadores(self) -> int:
        return len(self._jugadores)

    def registrar_jugador(self, alias: str, categoria: str = "Estándar") -> JugadorRegistrado:
        """
        Descarga primero la lista actual de la nube para evitar duplicados entre consolas,
        registra al jugador y sube inmediatamente la tabla actualizada a Google Sheets.
        """
        if self._gestor_nube.esta_conectado:
            self.sincronizar_desde_nube_y_local()

        alias_limpio = ValidadorDatos.validar_alias(alias)
        categoria_limpia = ValidadorDatos.validar_categoria(categoria)
        clave = alias_limpio.upper()

        if clave in self._jugadores:
            raise ErrorValidacionWordle(f"El jugador '{alias_limpio}' ya se encuentra registrado en la base de datos.")

        nuevo = JugadorRegistrado(alias=alias_limpio, categoria=categoria_limpia)
        self._jugadores[clave] = nuevo
        self.guardar_cambios(sincronizar_jugadores_nube=True)
        self._gestor_local.registrar_bitacora_txt(f"Jugador registrado en BD local y Google Sheets: {alias_limpio} ({categoria_limpia})")
        return nuevo

    def obtener_o_crear_participante(self, alias: str, como_invitado: bool = False) -> Participante:
        """
        Retorna un `JugadorRegistrado` existente (sincronizado con Google Sheets)
        o lo registra automáticamente en la tabla competitiva.
        """
        if self._gestor_nube.esta_conectado:
            self.sincronizar_desde_nube_y_local()

        alias_limpio = ValidadorDatos.validar_alias(alias)
        clave = alias_limpio.upper()

        if como_invitado:
            return JugadorInvitado(alias=alias_limpio)

        if clave not in self._jugadores:
            self._jugadores[clave] = JugadorRegistrado(alias=alias_limpio)
            self.guardar_cambios(sincronizar_jugadores_nube=True)
        return self._jugadores[clave]

    def buscar_jugador(self, alias: str) -> Optional[JugadorRegistrado]:
        return self._jugadores.get(alias.strip().upper())

    def listar_jugadores(self, solo_activos: bool = False, refrescar_nube: bool = False) -> List[JugadorRegistrado]:
        """Retorna la lista de jugadores ordenada competitivamente por puntaje y % de victorias."""
        if refrescar_nube and self._gestor_nube.esta_conectado:
            self.sincronizar_desde_nube_y_local()

        lista = [
            j for j in self._jugadores.values()
            if (not solo_activos or j.activo)
        ]
        return sorted(lista, key=lambda j: (j.puntaje_acumulado, j.porcentaje_victorias, j.partidas_ganadas), reverse=True)

    def actualizar_jugador(
        self,
        alias_actual: str,
        nuevo_alias: Optional[str] = None,
        nueva_categoria: Optional[str] = None,
        nuevo_estado_activo: Optional[bool] = None
    ) -> JugadorRegistrado:
        """Actualiza los atributos del jugador y sincroniza la tabla en Google Sheets."""
        clave_actual = alias_actual.strip().upper()
        jugador = self._jugadores.get(clave_actual)
        if not jugador:
            raise ErrorValidacionWordle(f"No se encontró ningún jugador con el alias '{alias_actual}'.")

        if nuevo_alias is not None and nuevo_alias.strip():
            alias_validado = ValidadorDatos.validar_alias(nuevo_alias)
            nueva_clave = alias_validado.upper()
            if nueva_clave != clave_actual and nueva_clave in self._jugadores:
                raise ErrorValidacionWordle(f"El nuevo alias '{alias_validado}' ya está ocupado por otro jugador.")
            del self._jugadores[clave_actual]
            jugador.alias = alias_validado
            self._jugadores[nueva_clave] = jugador

        if nueva_categoria is not None and nueva_categoria.strip():
            jugador.categoria = ValidadorDatos.validar_categoria(nueva_categoria)
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
        return set(self._catalogo_palabras)

    def agregar_palabra_catalogo(self, nueva_palabra: str) -> str:
        palabra_limpia = ValidadorDatos.validar_palabra_catalogo(nueva_palabra, CONFIG_JUEGO[0])
        if palabra_limpia in self._catalogo_palabras:
            raise ErrorValidacionWordle(f"La palabra '{palabra_limpia}' ya existe en el catálogo.")

        self._catalogo_palabras.add(palabra_limpia)
        self.guardar_cambios(sincronizar_jugadores_nube=False)
        self._gestor_nube.agregar_palabra_nube(palabra_limpia)
        self._gestor_local.registrar_bitacora_txt(f"Palabra agregada al catálogo: {palabra_limpia}")
        return palabra_limpia

    def eliminar_palabra_catalogo(self, palabra: str) -> str:
        palabra_limpia = ValidadorDatos.normalizar_palabra(palabra)
        if palabra_limpia not in self._catalogo_palabras:
            raise ErrorValidacionWordle(f"La palabra '{palabra_limpia}' no existe en el catálogo.")
        if len(self._catalogo_palabras) <= 5:
            raise ErrorValidacionWordle("No se puede eliminar: el catálogo debe conservar al menos 5 palabras.")

        self._catalogo_palabras.remove(palabra_limpia)
        self.guardar_cambios(sincronizar_jugadores_nube=False)
        self._gestor_local.registrar_bitacora_txt(f"Palabra eliminada del catálogo: {palabra_limpia}")
        return palabra_limpia

    def buscar_palabras_por_prefijo_o_letra(self, criterio: str) -> List[str]:
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
        if isinstance(participante, JugadorRegistrado):
            puntaje_final = participante.registrar_resultado_partida(gano, puntaje_base)
        else:
            puntaje_final = participante.calcular_bonificacion(puntaje_base) if gano else 0

        id_nuevo = f"PART-{len(self._partidas) + 1:03d}"
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

        self._partidas.append(registro)

        # 1. Subir la fila de la partida a la pestaña 'Puntajes' con append_row()
        subido_nube = self._gestor_nube.guardar_resultado(registro.a_diccionario())

        # 2. Guardar JSON local y actualizar la tabla de ranking en la pestaña 'Jugadores'
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
        """Permite búsquedas y filtros combinados sobre las partidas globales registradas."""
        if refrescar_nube and self._gestor_nube.esta_conectado:
            self.sincronizar_desde_nube_y_local()

        resultado: List[RegistroPartida] = []
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
        total_partidas = len(partidas)
        victorias = [p for p in partidas if p.gano]
        derrotas = [p for p in partidas if not p.gano]

        tasa_exito_global = round((len(victorias) / total_partidas) * 100.0, 2) if total_partidas > 0 else 0.0
        promedio_intentos_victoria = (
            round(sum(p.intentos_usados for p in victorias) / len(victorias), 2)
            if victorias else 0.0
        )
        puntaje_maximo = max((p.puntaje for p in partidas), default=0)

        agrupado_dificultad: Dict[str, Dict[str, int]] = {}
        for p in partidas:
            dif = p.dificultad
            if dif not in agrupado_dificultad:
                agrupado_dificultad[dif] = {"jugadas": 0, "victorias": 0, "puntos_totales": 0}
            agrupado_dificultad[dif]["jugadas"] += 1
            if p.gano:
                agrupado_dificultad[dif]["victorias"] += 1
            agrupado_dificultad[dif]["puntos_totales"] += p.puntaje

        distribucion_intentos: Dict[int, int] = {i: 0 for i in range(1, 8)}
        for v in victorias:
            distribucion_intentos[v.intentos_usados] = distribucion_intentos.get(v.intentos_usados, 0) + 1

        conteo_palabras: Dict[str, int] = {}
        for p in partidas:
            conteo_palabras[p.palabra_secreta] = conteo_palabras.get(p.palabra_secreta, 0) + 1
        palabra_mas_frecuente = (
            max(conteo_palabras.items(), key=lambda item: item[1])[0]
            if conteo_palabras else "N/A"
        )

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
