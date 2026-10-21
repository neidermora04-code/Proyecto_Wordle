"""
Módulo de Persistencia Híbrida y Sincronización Competitiva en Tiempo Real:
- Google Sheets (`gspread`): Base de datos central online para **Palabras**, **Puntajes (Partidas)** y **Jugadores (Ranking Competitivo)**.
- Archivos Locales (`pathlib.Path`): Respaldo y persistencia obligatoria del Lab 04 en **JSON**, exportación **CSV** y bitácora **TXT**.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Set, List, Dict, Any, Tuple

try:
    import gspread
    from gspread.exceptions import GSpreadException, SpreadsheetNotFound, WorksheetNotFound
    GSPREAD_DISPONIBLE = True
except ImportError:
    GSPREAD_DISPONIBLE = False

from config import (
    DIRECTORIO_DATOS,
    DIRECTORIO_EXPORTACIONES,
    ARCHIVO_HISTORIAL_JSON,
    ARCHIVO_PALABRAS_JSON,
    ARCHIVO_BITACORA_TXT,
    ARCHIVO_REPORTE_CSV,
    ARCHIVO_RANKING_CSV,
    CONFIG_JUEGO,
    HOJAS_GOOGLE_SHEETS,
    PALABRAS_RESPALDO,
    ID_DOCUMENTO_SHEETS,
    obtener_credenciales_desde_env
)
from validaciones import ValidadorDatos


class GestorArchivosLocales:
    """
    Clase responsable de la persistencia local en archivos JSON, exportación CSV
    y bitácora en archivos de texto (.txt) utilizando `pathlib.Path` (Lab 04).
    """

    def __init__(self) -> None:
        self._asegurar_directorios()

    def _asegurar_directorios(self) -> None:
        """Crea las carpetas `datos/` y `exportaciones/` usando `pathlib.Path.mkdir()`."""
        DIRECTORIO_DATOS.mkdir(parents=True, exist_ok=True)
        DIRECTORIO_EXPORTACIONES.mkdir(parents=True, exist_ok=True)

    def registrar_bitacora_txt(self, evento: str) -> None:
        """
        Escribe una línea con marca de tiempo en un archivo de texto plano (`.txt`).
        Demuestra el uso de `try / except / else / finally` con archivos de texto (Lab 04).
        """
        marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{marca_tiempo}] {evento}\n"
        archivo_abierto = False
        try:
            with ARCHIVO_BITACORA_TXT.open(mode="a", encoding="utf-8") as archivo_txt:
                archivo_abierto = True
                archivo_txt.write(linea)
        except OSError as error_io:
            print(f"[!] No se pudo escribir en la bitácora TXT: {error_io}")
        else:
            pass
        finally:
            _ = archivo_abierto

    def guardar_estado_json(
        self,
        jugadores_dict: Dict[str, Dict[str, Any]],
        partidas_lista: List[Dict[str, Any]],
        palabras_catalogo: Set[str]
    ) -> bool:
        """Conserva toda la información del sistema entre ejecuciones utilizando archivos JSON."""
        exito = False
        try:
            datos_principales = {
                "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "jugadores": jugadores_dict,
                "partidas": partidas_lista
            }
            with ARCHIVO_HISTORIAL_JSON.open(mode="w", encoding="utf-8") as f_hist:
                json.dump(datos_principales, f_hist, indent=4, ensure_ascii=False)

            datos_palabras = {
                "longitud_palabra": CONFIG_JUEGO[0],
                "total_palabras": len(palabras_catalogo),
                "palabras": sorted(list(palabras_catalogo))
            }
            with ARCHIVO_PALABRAS_JSON.open(mode="w", encoding="utf-8") as f_pal:
                json.dump(datos_palabras, f_pal, indent=4, ensure_ascii=False)

        except (OSError, TypeError, ValueError) as error_json:
            print(f"[Error JSON] No se pudo guardar la persistencia local: {error_json}")
            exito = False
        else:
            exito = True
            self.registrar_bitacora_txt(
                f"Estado JSON guardado ({len(jugadores_dict)} jugadores, {len(partidas_lista)} partidas, {len(palabras_catalogo)} palabras)."
            )
        finally:
            _ = exito
        return exito

    def cargar_estado_json(self) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], Set[str]]:
        """Carga los jugadores, el historial de partidas y el catálogo de palabras desde JSON."""
        jugadores: Dict[str, Dict[str, Any]] = {}
        partidas: List[Dict[str, Any]] = []
        palabras: Set[str] = set(PALABRAS_RESPALDO)

        if ARCHIVO_HISTORIAL_JSON.exists():
            try:
                with ARCHIVO_HISTORIAL_JSON.open(mode="r", encoding="utf-8") as f_hist:
                    contenido = json.load(f_hist)
            except (OSError, json.JSONDecodeError) as error_lectura:
                print(f"[!] Aviso: Archivo JSON de historial ilegible ({error_lectura}). Se iniciará limpio.")
            else:
                jugadores = contenido.get("jugadores", {})
                partidas = contenido.get("partidas", [])
            finally:
                pass

        if ARCHIVO_PALABRAS_JSON.exists():
            try:
                with ARCHIVO_PALABRAS_JSON.open(mode="r", encoding="utf-8") as f_pal:
                    contenido_pal = json.load(f_pal)
            except (OSError, json.JSONDecodeError):
                pass
            else:
                lista_cargada = contenido_pal.get("palabras", [])
                palabras_validas = {
                    ValidadorDatos.normalizar_palabra(p)
                    for p in lista_cargada
                    if isinstance(p, str) and len(ValidadorDatos.normalizar_palabra(p)) == CONFIG_JUEGO[0]
                }
                if palabras_validas:
                    palabras = palabras_validas

        return (jugadores, partidas, palabras)

    def exportar_partidas_csv(self, partidas_lista: List[Dict[str, Any]], ruta_destino: Path = ARCHIVO_REPORTE_CSV) -> Path:
        """Exporta el historial de partidas a un archivo CSV estándar."""
        encabezados = [
            "ID_Partida", "Fecha", "Jugador", "Tipo_Jugador", "Palabra_Secreta",
            "Estado", "Intentos_Usados", "Max_Intentos", "Dificultad", "Puntaje", "Secuencia_Intentos"
        ]
        try:
            with ruta_destino.open(mode="w", newline="", encoding="utf-8") as archivo_csv:
                escritor = csv.writer(archivo_csv)
                escritor.writerow(encabezados)
                for p in partidas_lista:
                    secuencia = " -> ".join(p.get("palabras_intentadas", []))
                    escritor.writerow([
                        p.get("id_partida", ""),
                        p.get("fecha", ""),
                        p.get("jugador", ""),
                        p.get("tipo_jugador", ""),
                        p.get("palabra_secreta", ""),
                        p.get("estado", "VICTORIA" if p.get("gano") else "DERROTA"),
                        p.get("intentos_usados", 0),
                        p.get("max_intentos", 6),
                        p.get("dificultad", "Normal"),
                        p.get("puntaje", 0),
                        secuencia
                    ])
        except OSError as error_csv:
            raise OSError(f"Error al exportar el archivo CSV en {ruta_destino}: {error_csv}") from error_csv
        else:
            self.registrar_bitacora_txt(f"Exportación CSV de partidas generada en: {ruta_destino}")
            return ruta_destino

    def exportar_ranking_csv(self, jugadores_lista: List[Dict[str, Any]], ruta_destino: Path = ARCHIVO_RANKING_CSV) -> Path:
        """Exporta el ranking competitivo de jugadores con sus métricas calculadas a formato CSV."""
        encabezados = [
            "Posicion", "Alias", "Categoria", "Estado",
            "Partidas_Jugadas", "Partidas_Ganadas", "Porcentaje_Victorias",
            "Racha_Actual", "Puntaje_Acumulado"
        ]
        try:
            with ruta_destino.open(mode="w", newline="", encoding="utf-8") as archivo_csv:
                escritor = csv.writer(archivo_csv)
                escritor.writerow(encabezados)
                for idx, j in enumerate(jugadores_lista, start=1):
                    escritor.writerow([
                        idx,
                        j.get("alias", ""),
                        j.get("categoria", ""),
                        "Activo" if j.get("activo", True) else "Inactivo",
                        j.get("partidas_jugadas", 0),
                        j.get("partidas_ganadas", 0),
                        f"{j.get('porcentaje_victorias', 0.0)}%",
                        j.get("racha_actual", 0),
                        j.get("puntaje_acumulado", 0)
                    ])
        except OSError as error_csv:
            raise OSError(f"Error al exportar el ranking CSV en {ruta_destino}: {error_csv}") from error_csv
        else:
            self.registrar_bitacora_txt(f"Exportación CSV de ranking generada en: {ruta_destino}")
            return ruta_destino


class GestorGoogleSheets:
    """
    Clase encargada de gestionar la Base de Datos Competitiva Online en Google Sheets (`gspread`).
    Sincroniza en tiempo real:
    1. Pestaña `Palabras` (Catálogo de palabras secretas en español).
    2. Pestaña `Puntajes` (Historial global de partidas de todos los jugadores con `append_row()`).
    3. Pestaña `Jugadores` (Tabla de Clasificación / Ranking Global en vivo de usuarios registrados).
    """

    ENCABEZADOS_PUNTAJES = [
        "Fecha", "Jugador", "Palabra Secreta", "Resultado",
        "Intentos", "Puntaje", "Dificultad", "Tipo Jugador", "ID Partida"
    ]

    ENCABEZADOS_JUGADORES = [
        "Posición", "Alias", "Categoría", "Estado",
        "Partidas Jugadas", "Partidas Ganadas", "% Victorias", "Racha Actual", "Puntaje Total"
    ]

    def __init__(self, ruta_credenciales: str, nombre_documento: str) -> None:
        self._ruta_credenciales: Path = Path(ruta_credenciales)
        self._nombre_documento: str = nombre_documento
        self._cliente: Any = None
        self._documento: Any = None
        self._modo_online: bool = False

        self._conectar()

    @property
    def esta_conectado(self) -> bool:
        return self._modo_online

    def _conectar(self) -> None:
        """
        Autentica la Service Account priorizando las variables de entorno del archivo `.env`
        (`service_account_from_dict`) o el archivo físico `credentials.json` como respaldo.
        """
        intento_completado = False
        if not GSPREAD_DISPONIBLE:
            self._modo_online = False
            return

        credenciales_env = obtener_credenciales_desde_env()
        if credenciales_env is None and not self._ruta_credenciales.exists():
            self._modo_online = False
            return

        try:
            if credenciales_env is not None:
                self._cliente = gspread.service_account_from_dict(credenciales_env)
            else:
                self._cliente = gspread.service_account(filename=str(self._ruta_credenciales))

            try:
                self._documento = self._cliente.open_by_key(ID_DOCUMENTO_SHEETS)
            except SpreadsheetNotFound:
                self._documento = self._cliente.open(self._nombre_documento)
        except FileNotFoundError:
            print(f"[Error] Archivo de credenciales no encontrado: {self._ruta_credenciales}")
            self._modo_online = False
        except SpreadsheetNotFound:
            print(f"[Error] No se encontró la hoja '{self._nombre_documento}' en Google Drive.")
            self._modo_online = False
        except GSpreadException as error_api:
            print(f"[Error API Google Sheets] {error_api}")
            self._modo_online = False
        except Exception as error_inesperado:
            print(f"[Error Crítico Google Sheets] {error_inesperado}")
            self._modo_online = False
        else:
            self._modo_online = True
        finally:
            intento_completado = True
            _ = intento_completado

    # =========================================================================
    # 1. SINCRONIZACIÓN DE PALABRAS (PESTAÑA 'Palabras')
    # =========================================================================
    def obtener_palabras(self, palabras_locales: Set[str]) -> Set[str]:
        """Descarga la lista de palabras en español desde Google Sheets."""
        longitud_requerida: int = CONFIG_JUEGO[0]
        nombre_hoja_palabras: str = HOJAS_GOOGLE_SHEETS[0]

        if not self._modo_online or self._documento is None:
            return set(palabras_locales) if palabras_locales else set(PALABRAS_RESPALDO)

        try:
            hoja = self._documento.worksheet(nombre_hoja_palabras)
            valores_crudos: List[str] = hoja.col_values(1)

            palabras_nube: Set[str] = {
                ValidadorDatos.normalizar_palabra(p)
                for p in valores_crudos
                if p and p.strip().isalpha() and len(ValidadorDatos.normalizar_palabra(p)) == longitud_requerida
            }
        except (WorksheetNotFound, GSpreadException, Exception):
            return set(palabras_locales) if palabras_locales else set(PALABRAS_RESPALDO)
        else:
            return palabras_nube.union(palabras_locales) if palabras_nube else set(palabras_locales)

    def agregar_palabra_nube(self, nueva_palabra: str) -> bool:
        """Añade una palabra nueva al final de la pestaña 'Palabras' con `append_row()`."""
        if not self._modo_online or self._documento is None:
            return False

        nombre_hoja_palabras: str = HOJAS_GOOGLE_SHEETS[0]
        try:
            hoja = self._documento.worksheet(nombre_hoja_palabras)
            hoja.append_row([nueva_palabra.upper()], value_input_option="USER_ENTERED")
        except Exception:
            return False
        else:
            return True

    # =========================================================================
    # 2. SINCRONIZACIÓN DE PARTIDAS / PUNTAJES (PESTAÑA 'Puntajes')
    # =========================================================================
    def guardar_resultado(self, datos_partida: Dict[str, Any]) -> bool:
        """
        Guarda el puntaje/resultado del jugador al finalizar la partida en Google Sheets
        utilizando explícitamente `append_row()`.
        """
        nombre_hoja_puntajes: str = HOJAS_GOOGLE_SHEETS[1]
        fecha_actual = datos_partida.get("fecha", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        estado_texto = "VICTORIA" if datos_partida.get("gano") else "DERROTA"

        fila_nuevo_registro: List[Any] = [
            fecha_actual,
            datos_partida.get("jugador", "Anónimo"),
            datos_partida.get("palabra_secreta", "?????"),
            estado_texto,
            datos_partida.get("intentos_usados", 0),
            datos_partida.get("puntaje", 0),
            datos_partida.get("dificultad", "Normal (6 intentos)"),
            datos_partida.get("tipo_jugador", "Registrado"),
            datos_partida.get("id_partida", "")
        ]

        if not self._modo_online or self._documento is None:
            return False

        try:
            try:
                hoja_puntajes = self._documento.worksheet(nombre_hoja_puntajes)
            except WorksheetNotFound:
                hoja_puntajes = self._documento.add_worksheet(title=nombre_hoja_puntajes, rows=500, cols=10)
                hoja_puntajes.append_row(self.ENCABEZADOS_PUNTAJES)

            # REQUISITO CLAVE: Uso de append_row()
            hoja_puntajes.append_row(fila_nuevo_registro, value_input_option="USER_ENTERED")
        except (GSpreadException, Exception) as error_escritura:
            print(f"\n[Error API Google Sheets] No se pudo subir fila de partida: {error_escritura}")
            return False
        else:
            return True

    def obtener_partidas_nube(self) -> List[Dict[str, Any]]:
        """
        Descarga el historial completo de partidas jugadas por todos los competidores
        desde la pestaña 'Puntajes' de Google Sheets.
        """
        if not self._modo_online or self._documento is None:
            return []

        nombre_hoja_puntajes: str = HOJAS_GOOGLE_SHEETS[1]
        try:
            hoja = self._documento.worksheet(nombre_hoja_puntajes)
            filas = hoja.get_all_values()
        except Exception:
            return []

        if len(filas) <= 1:
            return []

        partidas_descargadas: List[Dict[str, Any]] = []
        for idx, fila in enumerate(filas[1:], start=1):
            if not fila or len(fila) < 6:
                continue
            fecha = fila[0].strip()
            jugador = fila[1].strip() or "Anónimo"
            palabra = fila[2].strip().upper() or "ARBOL"
            estado_txt = fila[3].strip().upper()
            gano = (estado_txt == "VICTORIA")
            try:
                intentos = int(fila[4])
            except ValueError:
                intentos = 0
            try:
                puntaje = int(float(fila[5]))
            except ValueError:
                puntaje = 0

            dificultad = fila[6].strip() if len(fila) > 6 and fila[6].strip() else "Normal (6 intentos)"
            tipo_jugador = fila[7].strip() if len(fila) > 7 and fila[7].strip() else "Registrado"
            id_partida = fila[8].strip() if len(fila) > 8 and fila[8].strip() else f"PART-{idx:03d}"

            max_int = 7 if "Fácil" in dificultad else (4 if "Experto" in dificultad else 6)

            partidas_descargadas.append({
                "id_partida": id_partida,
                "fecha": fecha,
                "jugador": jugador,
                "tipo_jugador": tipo_jugador,
                "palabra_secreta": palabra,
                "gano": gano,
                "estado": "VICTORIA" if gano else "DERROTA",
                "intentos_usados": intentos,
                "max_intentos": max_int,
                "dificultad": dificultad,
                "puntaje": puntaje,
                "palabras_intentadas": []
            })

        return partidas_descargadas

    # =========================================================================
    # 3. SINCRONIZACIÓN DE JUGADORES Y RANKING COMPETITIVO (PESTAÑA 'Jugadores')
    # =========================================================================
    def obtener_jugadores_nube(self) -> Dict[str, Dict[str, Any]]:
        """
        Descarga todos los jugadores registrados y sus estadísticas competitivas
        desde la pestaña 'Jugadores' de Google Sheets.
        """
        if not self._modo_online or self._documento is None:
            return {}

        nombre_hoja_jugadores: str = HOJAS_GOOGLE_SHEETS[2]
        try:
            hoja = self._documento.worksheet(nombre_hoja_jugadores)
            filas = hoja.get_all_values()
        except WorksheetNotFound:
            try:
                hoja = self._documento.add_worksheet(title=nombre_hoja_jugadores, rows=200, cols=10)
                hoja.append_row(self.ENCABEZADOS_JUGADORES, value_input_option="USER_ENTERED")
            except Exception:
                pass
            return {}
        except Exception:
            return {}

        if len(filas) <= 1:
            return {}

        jugadores_nube: Dict[str, Dict[str, Any]] = {}
        for fila in filas[1:]:
            if not fila or len(fila) < 9:
                continue
            alias = fila[1].strip()
            if not alias:
                continue
            categoria = fila[2].strip() or "Estándar"
            activo = (fila[3].strip().lower() != "inactivo")
            try:
                pj = int(fila[4])
            except ValueError:
                pj = 0
            try:
                pg = int(fila[5])
            except ValueError:
                pg = 0
            try:
                racha = int(fila[7])
            except ValueError:
                racha = 0
            try:
                pts = int(float(fila[8]))
            except ValueError:
                pts = 0

            jugadores_nube[alias.upper()] = {
                "alias": alias,
                "categoria": categoria,
                "activo": activo,
                "partidas_jugadas": pj,
                "partidas_ganadas": pg,
                "racha_actual": racha,
                "puntaje_acumulado": pts
            }

        return jugadores_nube

    def sincronizar_tabla_jugadores_nube(self, jugadores_ordenados: List[Dict[str, Any]]) -> bool:
        """
        Actualiza la pestaña 'Jugadores' en Google Sheets con la tabla de posiciones
        ordenada por puntaje (Ranking Competitivo Global en tiempo real).
        """
        if not self._modo_online or self._documento is None:
            return False

        nombre_hoja_jugadores: str = HOJAS_GOOGLE_SHEETS[2]
        try:
            try:
                hoja = self._documento.worksheet(nombre_hoja_jugadores)
            except WorksheetNotFound:
                hoja = self._documento.add_worksheet(title=nombre_hoja_jugadores, rows=200, cols=10)

            matriz_filas: List[List[Any]] = [self.ENCABEZADOS_JUGADORES]
            for posicion, j in enumerate(jugadores_ordenados, start=1):
                estado_str = "Activo" if j.get("activo", True) else "Inactivo"
                matriz_filas.append([
                    posicion,
                    j.get("alias", ""),
                    j.get("categoria", "Estándar"),
                    estado_str,
                    j.get("partidas_jugadas", 0),
                    j.get("partidas_ganadas", 0),
                    f"{j.get('porcentaje_victorias', 0.0)}%",
                    j.get("racha_actual", 0),
                    j.get("puntaje_acumulado", 0)
                ])

            hoja.clear()
            hoja.update(range_name=f"A1:I{len(matriz_filas)}", values=matriz_filas)
        except Exception as err:
            print(f"[!] Aviso al actualizar tabla competitiva 'Jugadores' en Google Sheets: {err}")
            return False
        else:
            return True
