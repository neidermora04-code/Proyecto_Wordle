"""
Módulo de Persistencia Híbrida y Sincronización Competitiva en Tiempo Real:
- Google Sheets (`gspread` y WebApp HTTP): Base de datos central online para **Palabras**, **Puntajes (Partidas)** y **Jugadores (Ranking Competitivo)**.
- Archivos Locales (`pathlib.Path`): Respaldo y persistencia obligatoria del Lab 04 en **JSON**, exportación **CSV** y bitácora **TXT**.
"""

# Importamos 'csv' para generar archivos de hojas de cálculo separadas por comas (.csv)
import csv
# Importamos 'json' para serializar y deserializar estructuras de datos en formato .json
import json
# Importamos 'urllib.parse' y 'urllib.request' para conectarnos por HTTP a la Web App de Google Sheets sin requerir librerías externas
import urllib.parse
import urllib.request
# Importamos 'datetime' para estampar fechas y horas en la bitácora TXT y en los guardados
from datetime import datetime
# Importamos 'Path' de 'pathlib' para manipular rutas y abrir archivos de forma moderna (Lab 04)
from pathlib import Path
# Importamos tipos de datos para documentar parámetros y valores de retorno
from typing import Set, List, Dict, Any, Tuple

# Intentamos importar la librería externa 'gspread' para conexión directa con cuenta de servicio de Google Cloud
try:
    import gspread
    from gspread.exceptions import GSpreadException, SpreadsheetNotFound, WorksheetNotFound
    GSPREAD_DISPONIBLE = True
except ImportError:
    # Si 'gspread' no está instalada, la bandera queda en False y el sistema usará la WebApp HTTP o el modo JSON local
    GSPREAD_DISPONIBLE = False

# Importamos todas las rutas de carpetas, archivos y constantes configuradas en config.py
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
    URL_WEBAPP_SHEETS,
    obtener_credenciales_desde_env
)
# Importamos ValidadorDatos para limpiar y validar las palabras que se leen desde archivos o desde la nube
from validaciones import ValidadorDatos


class GestorArchivosLocales:
    """
    Clase responsable de la persistencia local en archivos JSON, exportación CSV
    y bitácora en archivos de texto (.txt) utilizando `pathlib.Path` (Lab 04).
    """

    def __init__(self) -> None:
        # Al instanciar el gestor local, verifica inmediatamente que existan las carpetas 'datos/' y 'exportaciones/'
        self._asegurar_directorios()

    def _asegurar_directorios(self) -> None:
        """Crea las carpetas `datos/` y `exportaciones/` usando `pathlib.Path.mkdir()` si aún no existen."""
        # parents=True crea carpetas padre si faltan; exist_ok=True evita error si la carpeta ya existe
        DIRECTORIO_DATOS.mkdir(parents=True, exist_ok=True)
        DIRECTORIO_EXPORTACIONES.mkdir(parents=True, exist_ok=True)

    def registrar_bitacora_txt(self, evento: str) -> None:
        """
        Escribe una línea con marca de tiempo en el archivo `datos/bitacora_eventos.txt`.
        Demuestra el uso de `try / except / else / finally` con archivos de texto (Lab 04).
        """
        # Obtiene fecha y hora actual en formato Año-Mes-Día Hora:Minuto:Segundo
        marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Arma la línea de texto que se agregará al final de la bitácora
        linea = f"[{marca_tiempo}] {evento}\n"
        archivo_abierto = False
        try:
            # Abre el archivo TXT en modo "a" (append = agregar al final sin borrar lo anterior) con codificación UTF-8
            with ARCHIVO_BITACORA_TXT.open(mode="a", encoding="utf-8") as archivo_txt:
                archivo_abierto = True
                archivo_txt.write(linea)
        except OSError as error_io:
            # Captura errores de permisos o de disco lleno sin detener el programa
            print(f"[!] No se pudo escribir en la bitácora TXT: {error_io}")
        else:
            # Se ejecuta si la escritura en el TXT fue exitosa
            pass
        finally:
            # Se ejecuta siempre al finalizar el bloque try/except
            _ = archivo_abierto

    def guardar_estado_json(
        self,
        jugadores_dict: Dict[str, Dict[str, Any]],
        partidas_lista: List[Dict[str, Any]],
        palabras_catalogo: Set[str]
    ) -> bool:
        """Conserva toda la información del sistema entre ejecuciones utilizando dos archivos JSON locales."""
        exito = False
        try:
            # 1. Estructura el diccionario principal con la fecha de actualización, los jugadores y las partidas
            datos_principales = {
                "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "jugadores": jugadores_dict,
                "partidas": partidas_lista
            }
            # Abre 'datos/partidas_y_jugadores.json' en modo escritura ("w") y vuelca el JSON con sangría de 4 espacios
            with ARCHIVO_HISTORIAL_JSON.open(mode="w", encoding="utf-8") as f_hist:
                json.dump(datos_principales, f_hist, indent=4, ensure_ascii=False)

            # 2. Estructura el diccionario del catálogo de palabras ordenándolas alfabéticamente con sorted()
            datos_palabras = {
                "longitud_palabra": CONFIG_JUEGO[0],
                "total_palabras": len(palabras_catalogo),
                "palabras": sorted(list(palabras_catalogo))
            }
            # Abre 'datos/diccionario_personalizado.json' en modo escritura ("w") y guarda la lista de palabras
            with ARCHIVO_PALABRAS_JSON.open(mode="w", encoding="utf-8") as f_pal:
                json.dump(datos_palabras, f_pal, indent=4, ensure_ascii=False)

        except (OSError, TypeError, ValueError) as error_json:
            # Si ocurre un error de entrada/salida o de formato JSON, lo informa por pantalla
            print(f"[Error JSON] No se pudo guardar la persistencia local: {error_json}")
            exito = False
        else:
            # Si ambos archivos JSON se guardaron sin errores, marcamos éxito y anotamos el evento en la bitácora TXT
            exito = True
            self.registrar_bitacora_txt(
                f"Estado JSON guardado ({len(jugadores_dict)} jugadores, {len(partidas_lista)} partidas, {len(palabras_catalogo)} palabras)."
            )
        finally:
            _ = exito
        return exito

    def cargar_estado_json(self) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], Set[str]]:
        """Carga los jugadores, el historial de partidas y el catálogo de palabras desde los archivos JSON."""
        # Inicializamos colecciones por defecto en caso de que sea la primera vez que se abre el programa
        jugadores: Dict[str, Dict[str, Any]] = {}
        partidas: List[Dict[str, Any]] = []
        palabras: Set[str] = set(PALABRAS_RESPALDO)

        # Si existe el archivo 'datos/partidas_y_jugadores.json', lo leemos con json.load()
        if ARCHIVO_HISTORIAL_JSON.exists():
            try:
                with ARCHIVO_HISTORIAL_JSON.open(mode="r", encoding="utf-8") as f_hist:
                    contenido = json.load(f_hist)
            except (OSError, json.JSONDecodeError) as error_lectura:
                print(f"[!] Aviso: Archivo JSON de historial ilegible ({error_lectura}). Se iniciará limpio.")
            else:
                # Extraemos los diccionarios de jugadores y la lista de partidas guardadas
                jugadores = contenido.get("jugadores", {})
                partidas = contenido.get("partidas", [])
            finally:
                pass

        # Si existe el archivo 'datos/diccionario_personalizado.json', cargamos sus palabras
        if ARCHIVO_PALABRAS_JSON.exists():
            try:
                with ARCHIVO_PALABRAS_JSON.open(mode="r", encoding="utf-8") as f_pal:
                    contenido_pal = json.load(f_pal)
            except (OSError, json.JSONDecodeError):
                pass
            else:
                lista_cargada = contenido_pal.get("palabras", [])
                # Comprensión de conjunto (Set): limpia y filtra solo palabras válidas de 5 letras
                palabras_validas = {
                    ValidadorDatos.normalizar_palabra(p)
                    for p in lista_cargada
                    if isinstance(p, str) and len(ValidadorDatos.normalizar_palabra(p)) == CONFIG_JUEGO[0]
                }
                if palabras_validas:
                    palabras = palabras_validas

        # Retorna una tupla con las 3 estructuras cargadas
        return (jugadores, partidas, palabras)

    def exportar_partidas_csv(self, partidas_lista: List[Dict[str, Any]], ruta_destino: Path = ARCHIVO_REPORTE_CSV) -> Path:
        """Exporta el historial completo de partidas al archivo `exportaciones/reporte_partidas.csv`."""
        # Definimos los nombres de las columnas de la primera fila del CSV
        encabezados = [
            "ID_Partida", "Fecha", "Jugador", "Tipo_Jugador", "Palabra_Secreta",
            "Estado", "Intentos_Usados", "Max_Intentos", "Dificultad", "Puntaje", "Secuencia_Intentos"
        ]
        try:
            # Abrimos el archivo CSV en modo escritura ("w") con newline="" para evitar líneas en blanco en Excel
            with ruta_destino.open(mode="w", newline="", encoding="utf-8") as archivo_csv:
                escritor = csv.writer(archivo_csv)
                # Escribimos la fila de encabezados
                escritor.writerow(encabezados)
                # Recorremos cada partida y escribimos sus datos como una fila en el CSV
                for p in partidas_lista:
                    # Unimos las palabras intentadas con flechas (ej. "AUDIO -> ARBOL")
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
            # Registramos en la bitácora TXT que se generó el reporte CSV y retornamos la ruta del archivo
            self.registrar_bitacora_txt(f"Exportación CSV de partidas generada en: {ruta_destino}")
            return ruta_destino

    def exportar_ranking_csv(self, jugadores_lista: List[Dict[str, Any]], ruta_destino: Path = ARCHIVO_RANKING_CSV) -> Path:
        """Exporta el ranking competitivo de jugadores al archivo `exportaciones/ranking_jugadores.csv`."""
        encabezados = [
            "Posicion", "Alias", "Categoria", "Estado",
            "Partidas_Jugadas", "Partidas_Ganadas", "Porcentaje_Victorias",
            "Racha_Actual", "Puntaje_Acumulado"
        ]
        try:
            with ruta_destino.open(mode="w", newline="", encoding="utf-8") as archivo_csv:
                escritor = csv.writer(archivo_csv)
                escritor.writerow(encabezados)
                # enumerate(..., start=1) numera automáticamente la posición en el ranking (1°, 2°, 3°...)
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
    Clase encargada de gestionar la Base de Datos Competitiva Online en Google Sheets.
    Sincroniza en tiempo real:
    1. Pestaña `Palabras` (Catálogo de palabras secretas en español).
    2. Pestaña `Puntajes` (Historial global de partidas de todos los jugadores con `append_row()`).
    3. Pestaña `Jugadores` (Tabla de Clasificación / Ranking Global en vivo de usuarios registrados).
    """

    # Encabezados oficiales para la pestaña 'Puntajes' en Google Sheets
    ENCABEZADOS_PUNTAJES = [
        "Fecha", "Jugador", "Palabra Secreta", "Resultado",
        "Intentos", "Puntaje", "Dificultad", "Tipo Jugador", "ID Partida"
    ]

    # Encabezados oficiales para la pestaña 'Jugadores' en Google Sheets
    ENCABEZADOS_JUGADORES = [
        "Posición", "Alias", "Categoría", "Estado",
        "Partidas Jugadas", "Partidas Ganadas", "% Victorias", "Racha Actual", "Puntaje Total"
    ]

    def __init__(self, ruta_credenciales: str, nombre_documento: str) -> None:
        # Guardamos la ruta del archivo credentials.json y el nombre de la hoja de cálculo
        self._ruta_credenciales: Path = Path(ruta_credenciales)
        self._nombre_documento: str = nombre_documento
        self._cliente: Any = None
        self._documento: Any = None
        # Banderas de estado de conexión a la nube
        self._modo_online: bool = False
        self._usar_webapp: bool = False
        self._url_webapp: str = URL_WEBAPP_SHEETS.strip()

        # Intentamos establecer la conexión con Google Sheets al iniciar el objeto
        self._conectar()

    @property
    def esta_conectado(self) -> bool:
        """Indica si el sistema logró conectarse en línea con Google Sheets."""
        return self._modo_online

    def _peticion_webapp_get(self, nombre_hoja: str) -> List[List[str]]:
        """Obtiene todas las filas de una pestaña mediante petición HTTP GET a la Web App de Google Apps Script."""
        if not self._url_webapp:
            return []
        # Codifica el nombre de la pestaña en la URL (ej. ?hoja=Palabras)
        url = f"{self._url_webapp}?hoja={urllib.parse.quote(nombre_hoja)}"
        req = urllib.request.Request(url, method="GET")
        # Abre la conexión con un tiempo máximo de espera (timeout) de 10 segundos
        with urllib.request.urlopen(req, timeout=10) as resp:
            datos = json.loads(resp.read().decode("utf-8"))
            if isinstance(datos, dict) and datos.get("ok"):
                return datos.get("filas", [])
        return []

    def _peticion_webapp_post(self, payload: Dict[str, Any]) -> bool:
        """Envía una operación de escritura (append o replace) mediante petición HTTP POST a la Web App."""
        if not self._url_webapp:
            return False
        # Convierte el diccionario payload a bytes JSON en UTF-8
        cuerpo = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url_webapp,
            data=cuerpo,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            datos = json.loads(resp.read().decode("utf-8"))
            return bool(isinstance(datos, dict) and datos.get("ok"))

    def _conectar(self) -> None:
        """
        Autentica la Service Account priorizando `.env` / `credentials.json` con `gspread`, o
        conecta automáticamente vía `URL_WEBAPP_SHEETS` para cualquier usuario que clone desde GitHub.
        """
        intento_completado = False
        # Verifica si existen credenciales privadas en el archivo .env o en credentials.json
        credenciales_env = obtener_credenciales_desde_env()
        tiene_credenciales_locales = (credenciales_env is not None or self._ruta_credenciales.exists())

        # Opción A: Conexión directa mediante librería 'gspread' y Service Account
        if GSPREAD_DISPONIBLE and tiene_credenciales_locales:
            try:
                if credenciales_env is not None:
                    self._cliente = gspread.service_account_from_dict(credenciales_env)
                else:
                    self._cliente = gspread.service_account(filename=str(self._ruta_credenciales))

                try:
                    # Intenta abrir la hoja de Google Sheets por su ID único
                    self._documento = self._cliente.open_by_key(ID_DOCUMENTO_SHEETS)
                except SpreadsheetNotFound:
                    # Si no la encuentra por ID, la busca por nombre ("Wordle_DB")
                    self._documento = self._cliente.open(self._nombre_documento)
            except Exception:
                self._modo_online = False
            else:
                self._modo_online = True
                self._usar_webapp = False
                return

        # Opción B: Conexión automática por Web App HTTP (sin necesitar archivos de claves locales)
        if self._url_webapp:
            try:
                self._peticion_webapp_get(HOJAS_GOOGLE_SHEETS[0])
            except Exception:
                # Si no hay internet, pasa limpiamente a Modo Local (Offline) sin caerse
                self._modo_online = False
                self._usar_webapp = False
            else:
                self._modo_online = True
                self._usar_webapp = True
        else:
            self._modo_online = False
            self._usar_webapp = False

        intento_completado = True
        _ = intento_completado

    # =========================================================================
    # 1. SINCRONIZACIÓN DE PALABRAS (PESTAÑA 'Palabras')
    # =========================================================================
    def obtener_palabras(self, palabras_locales: Set[str]) -> Set[str]:
        """Descarga la lista de palabras en español desde Google Sheets y la une con el catálogo local."""
        longitud_requerida: int = CONFIG_JUEGO[0]
        nombre_hoja_palabras: str = HOJAS_GOOGLE_SHEETS[0]

        # Si estamos sin internet, retorna las palabras locales o el catálogo base de respaldo
        if not self._modo_online:
            return set(palabras_locales) if palabras_locales else set(PALABRAS_RESPALDO)

        try:
            if self._usar_webapp:
                filas = self._peticion_webapp_get(nombre_hoja_palabras)
                valores_crudos: List[str] = [f[0] for f in filas if f]
            else:
                hoja = self._documento.worksheet(nombre_hoja_palabras)
                # col_values(1) obtiene todos los valores de la Columna A de la hoja 'Palabras'
                valores_crudos = hoja.col_values(1)

            # Comprensión de conjunto que normaliza y filtra solo palabras alfabéticas de 5 letras
            palabras_nube: Set[str] = {
                ValidadorDatos.normalizar_palabra(p)
                for p in valores_crudos
                if p and p.strip().isalpha() and len(ValidadorDatos.normalizar_palabra(p)) == longitud_requerida
            }
        except Exception:
            return set(palabras_locales) if palabras_locales else set(PALABRAS_RESPALDO)
        else:
            # Une (.union) las palabras descargadas de la nube con las palabras locales sin duplicados
            return palabras_nube.union(palabras_locales) if palabras_nube else set(palabras_locales)

    def agregar_palabra_nube(self, nueva_palabra: str) -> bool:
        """Añade una palabra nueva al final de la pestaña 'Palabras' en Google Sheets con `append_row()`."""
        if not self._modo_online:
            return False

        nombre_hoja_palabras: str = HOJAS_GOOGLE_SHEETS[0]
        try:
            if self._usar_webapp:
                return self._peticion_webapp_post({
                    "accion": "append",
                    "hoja": nombre_hoja_palabras,
                    "fila": [nueva_palabra.upper()]
                })
            hoja = self._documento.worksheet(nombre_hoja_palabras)
            # Inserta la nueva palabra en la primera fila vacía de la pestaña 'Palabras'
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
        Guarda el puntaje y resultado del jugador al finalizar la partida en Google Sheets
        utilizando explícitamente `append_row()`.
        """
        nombre_hoja_puntajes: str = HOJAS_GOOGLE_SHEETS[1]
        fecha_actual = datos_partida.get("fecha", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        estado_texto = "VICTORIA" if datos_partida.get("gano") else "DERROTA"

        # Prepara la lista con las 9 columnas que se insertarán en la fila de la pestaña 'Puntajes'
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

        if not self._modo_online:
            return False

        try:
            if self._usar_webapp:
                return self._peticion_webapp_post({
                    "accion": "append",
                    "hoja": nombre_hoja_puntajes,
                    "fila": fila_nuevo_registro
                })

            try:
                hoja_puntajes = self._documento.worksheet(nombre_hoja_puntajes)
            except WorksheetNotFound:
                # Si la pestaña 'Puntajes' no existía en el documento, la crea y le agrega los encabezados
                hoja_puntajes = self._documento.add_worksheet(title=nombre_hoja_puntajes, rows=500, cols=10)
                hoja_puntajes.append_row(self.ENCABEZADOS_PUNTAJES)

            # REQUISITO CLAVE: Uso de append_row() para agregar la partida al final de la hoja en la nube
            hoja_puntajes.append_row(fila_nuevo_registro, value_input_option="USER_ENTERED")
        except Exception as error_escritura:
            print(f"\n[Error API Google Sheets] No se pudo subir fila de partida: {error_escritura}")
            return False
        else:
            return True

    def obtener_partidas_nube(self) -> List[Dict[str, Any]]:
        """
        Descarga el historial completo de partidas jugadas por todos los competidores
        desde la pestaña 'Puntajes' de Google Sheets.
        """
        if not self._modo_online:
            return []

        nombre_hoja_puntajes: str = HOJAS_GOOGLE_SHEETS[1]
        try:
            if self._usar_webapp:
                filas = self._peticion_webapp_get(nombre_hoja_puntajes)
            else:
                hoja = self._documento.worksheet(nombre_hoja_puntajes)
                filas = hoja.get_all_values()
        except Exception:
            return []

        # Si solo está la fila de encabezados (o está vacía), retorna lista vacía
        if len(filas) <= 1:
            return []

        partidas_descargadas: List[Dict[str, Any]] = []
        # Recorre desde la fila 2 en adelante (filas[1:]), omitiendo los encabezados
        for idx, fila in enumerate(filas[1:], start=1):
            if not fila or len(fila) < 6:
                continue
            fecha = str(fila[0]).strip()
            jugador = str(fila[1]).strip() or "Anónimo"
            palabra = str(fila[2]).strip().upper() or "ARBOL"
            estado_txt = str(fila[3]).strip().upper()
            gano = (estado_txt == "VICTORIA")
            # Conversión segura de intentos y puntaje con bloques try/except
            try:
                intentos = int(fila[4])
            except ValueError:
                intentos = 0
            try:
                puntaje = int(float(fila[5]))
            except ValueError:
                puntaje = 0

            dificultad = str(fila[6]).strip() if len(fila) > 6 and str(fila[6]).strip() else "Normal (6 intentos)"
            tipo_jugador = str(fila[7]).strip() if len(fila) > 7 and str(fila[7]).strip() else "Registrado"
            id_partida = str(fila[8]).strip() if len(fila) > 8 and str(fila[8]).strip() else f"PART-{idx:03d}"

            # Determina el máximo de intentos según el nombre de la dificultad
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
        if not self._modo_online:
            return {}

        nombre_hoja_jugadores: str = HOJAS_GOOGLE_SHEETS[2]
        try:
            if self._usar_webapp:
                filas = self._peticion_webapp_get(nombre_hoja_jugadores)
            else:
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
        # Recorremos cada fila de la hoja 'Jugadores' omitiendo la cabecera (filas[1:])
        for fila in filas[1:]:
            if not fila or len(fila) < 9:
                continue
            alias = str(fila[1]).strip()
            if not alias:
                continue
            categoria = str(fila[2]).strip() or "Estándar"
            activo = (str(fila[3]).strip().lower() != "inactivo")
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

            # Guardamos en el diccionario usando el alias en mayúsculas como clave única
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
        if not self._modo_online:
            return False

        nombre_hoja_jugadores: str = HOJAS_GOOGLE_SHEETS[2]
        # La primera fila de la matriz son los encabezados de la tabla
        matriz_filas: List[List[Any]] = [self.ENCABEZADOS_JUGADORES]
        # Agregamos cada jugador con su posición competitiva (1, 2, 3...)
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

        try:
            if self._usar_webapp:
                return self._peticion_webapp_post({
                    "accion": "replace",
                    "hoja": nombre_hoja_jugadores,
                    "filas": matriz_filas
                })

            try:
                hoja = self._documento.worksheet(nombre_hoja_jugadores)
            except WorksheetNotFound:
                hoja = self._documento.add_worksheet(title=nombre_hoja_jugadores, rows=200, cols=10)

            # Limpia la hoja y escribe la tabla de posiciones actualizada de una sola vez
            hoja.clear()
            hoja.update(range_name=f"A1:I{len(matriz_filas)}", values=matriz_filas)
        except Exception as err:
            print(f"[!] Aviso al actualizar tabla competitiva 'Jugadores' en Google Sheets: {err}")
            return False
        else:
            return True
