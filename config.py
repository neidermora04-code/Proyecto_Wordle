"""
Módulo de configuración y constantes globales del proyecto Wordle CLI.
Integra:
- Lab 01: Constantes por convención, tipos de datos primitivos.
- Lab 02: Tuplas (inmutabilidad), Conjuntos (sets), Diccionarios y Comprensiones.
- Lab 04: Uso de `pathlib.Path` y carga segura de variables de entorno desde `.env` (`python-dotenv`).
"""

# Importamos 'os' para leer variables de entorno del sistema operativo
import os
# Importamos 'Path' de 'pathlib' (Lab 04) para manejar rutas de carpetas y archivos de forma segura en cualquier SO (Linux/Windows/Mac)
from pathlib import Path
# Importamos tipos de datos de 'typing' para documentar qué tipo de dato guarda cada variable o retorna cada función
from typing import Tuple, Set, Dict, Optional

# Bloque try/except para intentar importar la librería 'python-dotenv' sin que el programa falle si no está instalada
try:
    # Intenta cargar la función 'load_dotenv' que lee el archivo oculto '.env'
    from dotenv import load_dotenv
    # Bandera booleana que indica que la librería sí está disponible
    DOTENV_DISPONIBLE = True
except ImportError:
    # Si el usuario no instaló 'python-dotenv', marcamos la bandera en False y el juego sigue funcionando
    DOTENV_DISPONIBLE = False

# ==========================================
# LAB 04: USO DE PATHLIB Y CARGA DE .ENV
# ==========================================
# Obtiene la ruta absoluta de la carpeta raíz donde está guardado este archivo 'config.py'
DIRECTORIO_BASE: Path = Path(__file__).resolve().parent
# Construye la ruta hacia el archivo '.env' dentro de la carpeta raíz del proyecto
ARCHIVO_ENV: Path = DIRECTORIO_BASE / ".env"

# Si la librería dotenv está instalada Y el archivo '.env' existe físicamente en la carpeta:
if DOTENV_DISPONIBLE and ARCHIVO_ENV.exists():
    # Carga todas las variables definidas en '.env' hacia las variables de entorno del sistema
    load_dotenv(dotenv_path=ARCHIVO_ENV)

# Ruta de la carpeta 'datos/' donde se guardan los archivos JSON de persistencia y la bitácora TXT
DIRECTORIO_DATOS: Path = DIRECTORIO_BASE / "datos"
# Ruta de la carpeta 'exportaciones/' donde se generan los reportes en formato CSV para Excel
DIRECTORIO_EXPORTACIONES: Path = DIRECTORIO_BASE / "exportaciones"

# Rutas de archivos locales (JSON, TXT, CSV) construidas con el operador '/' de pathlib.Path:
# Archivo JSON principal que guarda los perfiles de jugadores y el historial de todas las partidas jugadas
ARCHIVO_HISTORIAL_JSON: Path = DIRECTORIO_DATOS / "partidas_y_jugadores.json"
# Archivo JSON que guarda el diccionario o catálogo personalizado de palabras de 5 letras
ARCHIVO_PALABRAS_JSON: Path = DIRECTORIO_DATOS / "diccionario_personalizado.json"
# Archivo de texto plano (.txt) donde se registra cada evento del sistema con fecha y hora (auditoría)
ARCHIVO_BITACORA_TXT: Path = DIRECTORIO_DATOS / "bitacora_eventos.txt"
# Archivo CSV donde se exporta la tabla de todas las partidas jugadas
ARCHIVO_REPORTE_CSV: Path = DIRECTORIO_EXPORTACIONES / "reporte_partidas.csv"
# Archivo CSV donde se exporta la tabla del ranking competitivo de jugadores
ARCHIVO_RANKING_CSV: Path = DIRECTORIO_EXPORTACIONES / "ranking_jugadores.csv"

# Configuración de Google Sheets leída desde variables de entorno (.env) o usando valores por defecto:
# Ruta al archivo 'credentials.json' de Google Cloud (si se usa autenticación por archivo local)
RUTA_CREDENCIALES_DEFAULT: str = os.getenv(
    "GOOGLE_CREDENTIALS_PATH",
    str(DIRECTORIO_BASE / "credentials.json")
)
# Nombre del documento de Google Sheets en la nube (por defecto "Wordle_DB")
NOMBRE_DOCUMENTO_SHEETS: str = os.getenv("GOOGLE_SHEET_NAME", "Wordle_DB")
# ID único de la hoja de cálculo de Google Sheets compartida en la nube
ID_DOCUMENTO_SHEETS: str = os.getenv(
    "GOOGLE_SHEET_ID",
    "17_TzEIOid9tCwlmm0NzOPqM2sIY6pix9Z_raB41usOc"
)
# Enlace URL completo hacia el documento de Google Sheets para referencia visual
URL_DOCUMENTO_SHEETS: str = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO_SHEETS}/edit"
# URL de la Web App de Google Apps Script que permite conectarse a Google Sheets sin necesitar 'credentials.json'
URL_WEBAPP_SHEETS: str = os.getenv(
    "GOOGLE_WEBAPP_URL",
    "https://script.google.com/macros/s/AKfycbxyjjETLxdO_9m8hZxQ0fZ39r9OgKOkryKdmaVr-bN4cP7Z4xd8_HW1X4kiozl9ypF1/exec"
)


def obtener_credenciales_desde_env() -> Optional[Dict[str, str]]:
    """
    Construye el diccionario de credenciales de Google Cloud directamente
    desde las variables de entorno definidas en `.env` (sin exponer archivos JSON en GitHub).
    Retorna `None` si no están definidas las variables mínimas en `.env`.
    """
    # Lee la clave privada de la cuenta de servicio desde la variable de entorno
    private_key = os.getenv("GCP_PRIVATE_KEY")
    # Lee el correo electrónico de la cuenta de servicio (Service Account)
    client_email = os.getenv("GCP_CLIENT_EMAIL")
    # Lee el identificador del proyecto en Google Cloud Platform
    project_id = os.getenv("GCP_PROJECT_ID")

    # Si falta alguno de los 3 datos obligatorios, retorna None (indicando que no hay credenciales en .env)
    if not private_key or not client_email or not project_id:
        return None

    # Reemplaza los saltos de línea escapados ("\\n") por saltos de línea reales ("\n") para que la clave RSA sea válida
    clave_formateada = private_key.replace("\\n", "\n")

    # Retorna un diccionario con la estructura exacta que exige la librería 'gspread' para autenticar
    return {
        "type": os.getenv("GCP_TYPE", "service_account"),
        "project_id": project_id,
        "private_key_id": os.getenv("GCP_PRIVATE_KEY_ID", ""),
        "private_key": clave_formateada,
        "client_email": client_email,
        "client_id": os.getenv("GCP_CLIENT_ID", ""),
        "auth_uri": os.getenv("GCP_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
        "token_uri": os.getenv("GCP_TOKEN_URI", "https://oauth2.googleapis.com/token"),
        "auth_provider_x509_cert_url": os.getenv(
            "GCP_AUTH_PROVIDER_X509_CERT_URL",
            "https://www.googleapis.com/oauth2/v1/certs"
        ),
        "client_x509_cert_url": os.getenv("GCP_CLIENT_X509_CERT_URL", ""),
        "universe_domain": os.getenv("GCP_UNIVERSE_DOMAIN", "googleapis.com"),
    }


# ==========================================
# LAB 02: ESTRUCTURAS DE DATOS - TUPLAS (Inmutables)
# ==========================================
# Tupla inmutable con reglas base del juego: (longitud_de_palabra = 5 letras, intentos_por_defecto = 6)
CONFIG_JUEGO: Tuple[int, int] = (5, 6)

# Tupla anidada de tuplas para definir los niveles de dificultad:
# Cada elemento contiene: (código_opción, nombre_descriptivo, número_de_intentos, multiplicador_de_puntaje)
NIVELES_DIFICULTAD: Tuple[Tuple[str, str, int, float], ...] = (
    ("1", "Fácil (7 intentos)", 7, 0.8),     # Más intentos, pero multiplica el puntaje por 0.8
    ("2", "Normal (6 intentos)", 6, 1.0),    # Estándar de Wordle: 6 intentos, puntaje x1.0
    ("3", "Experto (4 intentos)", 4, 1.5),   # Menos intentos, premia con 50% más de puntos (x1.5)
)

# Tupla con los nombres exactos de las 3 pestañas dentro del documento de Google Sheets
HOJAS_GOOGLE_SHEETS: Tuple[str, str, str] = ("Palabras", "Puntajes", "Jugadores")

# ==========================================
# LAB 02: ESTRUCTURAS DE DATOS - CONJUNTOS (Sets) y COMPRENSIONES
# ==========================================
# Conjunto (Set) de palabras en español. Un Set no permite elementos duplicados y permite búsquedas rápidas O(1)
PALABRAS_BASE: Set[str] = {
    "ABETO", "ACTOR", "AGUDO", "ALTAR", "AMIGO", "ANEXO", "ANGEL", "ANIMO", "APOYO", "ARBOL",
    "ARENA", "AROMA", "ASADO", "ATLAS", "ATOMO", "AUTOR", "AVENA", "AVION", "AYUDA", "BAILE",
    "BALON", "BANCO", "BARCO", "BARRO", "BATEA", "BICHO", "BOLSA", "BOMBA", "BORDE", "BOTON",
    "BRAZO", "BRISA", "BRUJA", "BUENO", "BUFON", "BUQUE", "CABRA", "CACAO", "CAJON", "CALLE",
    "CALMA", "CAMPO", "CANAL", "CANTO", "CARGO", "CARNE", "CARRO", "CARTA", "CASCO", "CAUSA",
    "CEBRA", "CEDRO", "CELDA", "CENSO", "CERCA", "CERDO", "CERRO", "CESTA", "CHICO", "CIELO",
    "CIFRA", "CINCO", "CIRCO", "CISNE", "CLARA", "CLASE", "CLIMA", "COBRE", "COCHE", "COFRE",
    "COLOR", "CONDE", "CORAL", "CORTE", "COSTA", "CREMA", "CRUCE", "CUADRO", "CUERO", "CUEVA",
    "CULPA", "CURSO", "DANZA", "DATOS", "DEBER", "DEDAL", "DIETA", "DISCO", "DOBLE", "DOGMA",
    "DOLOR", "DRAMA", "DUCHA", "DUELO", "DUQUE", "DULCE", "EPOCA", "ERROR", "ETAPA", "EXITO",
    "FABULA", "FALDA", "FALLO", "FALSO", "FANGO", "FAROL", "FAUNA", "FECHA", "FELIZ", "FERIA",
    "FIBRA", "FICHA", "FIERA", "FIJACION", "FILA", "FINAL", "FINCA", "FIRMA", "FLACO", "FLECHA",
    "FLORA", "FLOTA", "FLUJO", "FONDO", "FORMA", "FORRO", "FUEGO", "FUENTE", "FUGAZ", "FUNDA",
    "GAFAS", "GALAN", "GALLO", "GAMBA", "GANAS", "GANSO", "GARRA", "GASTO", "GENIO", "GENTE",
    "GESTO", "GLOBO", "GOLPE", "GORDO", "GORRA", "GOTAS", "GOZAR", "GRADO", "GRAMO", "GRANO",
    "GRASA", "GRAVE", "GRIFO", "GRITO", "GRUPO", "GUAPO", "GUION", "GUSTO", "HABER", "HABLA",
    "HACER", "HACHA", "HIELO", "HIerro", "HIGADO", "HIMNO", "HOGAR", "HOJAS", "HONDO", "HONGO",
    "HONOR", "HORAS", "HORNO", "HOTEL", "HUESO", "HUEVO", "HUMOR", "IDEAL", "IDOLO", "IGUAL",
    "IMAGEN", "IMAN", "INDIA", "ISLAS", "JABON", "JAULA", "JEFES", "JERGA", "JOVEN", "JUEGO",
    "JUEZA", "JUGAR", "JUGOS", "JULIO", "JUNIO", "JUNTO", "JUSTO", "LABIO", "LABOR", "LADOS",
    "LAGO", "LANZA", "LAPIZ", "LARGO", "LARVA", "LASER", "LATIN", "LAUREL", "LAVAR", "LAZOS",
    "LECHE", "LECHO", "LEGAL", "LEJOS", "LENGUA", "LENTO", "LEONA", "LETRA", "LIBRA", "LIBRE",
    "LIBRO", "LIDER", "LIMON", "LINDO", "LINEA", "LISTA", "LITRO", "LLAMA", "LLANO", "LLAVE",
    "LLENO", "LOCAL", "LOGRO", "LUCHA", "LUGAR", "LUCES", "LUNAR", "LUNES", "MADRE", "MAGIA",
    "MANGO", "MANOS", "MANTA", "MAPAS", "MARCA", "MARCO", "MAREA", "MARZO", "MASAS", "MATIZ",
    "MAYOR", "MEDIA", "MEDIO", "MEJOR", "MELON", "MENOR", "MENOS", "MENTE", "MESAS", "METAL",
    "METRO", "MIEDO", "MINAS", "MIRAR", "MITAD", "MODAS", "MOLDE", "MONJE", "MONTE", "MORAL",
    "MOSCA", "MOTOR", "MOVIL", "MUCHO", "MUELA", "MUJER", "MUNDO", "MUROS", "MUSEO", "MUSGO",
    "NACER", "NADAR", "NAIPE", "NARIZ", "NATAL", "NAVES", "NEGRO", "NERVIO", "NIEVE", "NIÑOS",
    "NIVEL", "NOBLE", "NOCHE", "NORMA", "NORTE", "NOTAS", "NOVIA", "NOVIO", "NUBES", "NUDO",
    "NUEVA", "NUEVE", "NUEVO", "OASIS", "OBRAS", "OCASO", "OESTE", "OJERA", "OLIVA", "OLIVO",
    "ONDAS", "OPERA", "ORDEN", "OREJA", "ORO", "ORUGA", "OTOÑO", "OVEJA", "OXIDO", "PADRE",
    "PAGAR", "PASEO", "PASTA", "PATIO", "PAUSA", "PECHO", "PEDAL", "PEDIR", "PEINE", "PELO",
    "PENAL", "PERAS", "PERRO", "PESCA", "PIANO", "PIEZA", "PILAR", "PILAS", "PINOS", "PINTA",
    "PISTA", "PLACA", "PLANA", "PLANO", "PLATA", "PLATO", "PLAYA", "PLAZA", "PLAZO", "PLENO",
    "PLOMO", "PLUMA", "POBRE", "PODER", "POEMA", "POETA", "POLAR", "POLVO", "PONER", "PORTA",
    "POZOS", "PRADO", "PRESA", "PRIMO", "PRISA", "PROSA", "PUENTE", "PUERTA", "PULGA", "PULPO",
    "PULSO", "PUNTA", "PUNTO", "PUÑOS", "QUEJA", "QUESO", "QUIEN", "QUIMICA", "RABIA", "RADIO",
    "RAMAS", "RANGO", "RAPAZ", "RASGO", "RATON", "RAYOS", "RAZON", "REINA", "RELOJ", "REMO",
    "RENTA", "RESTO", "RETO", "REYES", "RIEGO", "RIFLE", "RIMA", "RIÑON", "RITMO", "RIVAL",
    "ROBLE", "ROCAS", "ROCIO", "RODAR", "RODEO", "ROGAR", "ROLLO", "ROMBO", "RONDA", "ROPAS",
    "ROSAS", "RUBIO", "RUEDA", "RUEGO", "RUIDO", "RUINA", "RUMBO", "RUMOR", "RURAL", "RUTAS",
    "SABER", "SABIO", "SABOR", "SACAR", "SALAS", "SALDO", "SALIR", "SALON", "SALSA", "SALTO",
    "SALUD", "SANTO", "SAPOS", "SAUCE", "SECAR", "SELVA", "SELLO", "SENDA", "SEÑAL", "SEÑOR",
    "SERIE", "SERIO", "SIETE", "SIGLO", "SIGNO", "SILLA", "SILVA", "SIMIO", "SITIO", "SOBRE",
    "SOCIO", "SOLAR", "SOLOS", "SOMBRA", "SONAR", "SOPAS", "SOPLO", "SORDO", "SUAVE", "SUBIR",
    "SUCIO", "SUDOR", "SUELA", "SUELO", "SUEÑO", "SUERTE", "SUITE", "SURCO", "SUSTO", "SUTIL",
    "TABLA", "TACON", "TALLO", "TALON", "TANGO", "TAPAS", "TARDE", "TAREA", "TARRO", "TARTA",
    "TASAS", "TAZAS", "TEATRO", "TECHO", "TECLA", "TEJER", "TELAS", "TELON", "TEMAS", "TEMOR",
    "TEMPLO", "TENAZ", "TENER", "TENIS", "TENSO", "TERCO", "TERMO", "TEXTO", "TIBIO", "TIEMPO",
    "TIERRA", "TIGRE", "TIMON", "TINTA", "TIPOS", "TIRAR", "TITAN", "TOCAR", "TODOS", "TOLDO",
    "TOMAR", "TONOS", "TONTO", "TOQUE", "TOREO", "TORNO", "TOROS", "TORPE", "TORRE", "TORTA",
    "TOTAL", "TRAGO", "TRAJE", "TRAMO", "TRATO", "TRAZO", "TRECE", "TRENO", "TRIBU", "TRIGO",
    "TRINO", "TRISTE", "TROPA", "TROTE", "TROZO", "TRUCO", "TRUENO", "TUBOS", "TUMBA", "TUNEL",
    "TURNO", "UNION", "UNTAR", "USADO", "USUAL", "UTILES", "VACAS", "VACIO", "VAGAR", "VAGON",
    "VALLE", "VALOR", "VAPOR", "VARON", "VASOS", "VECINO", "VELAS", "VELOZ", "VENAS", "VENDA",
    "VENIR", "VENTA", "VERDE", "VERSO", "VIAJE", "VICIO", "VIDAS", "VIDEO", "VIEJO", "VIENTO",
    "VIGOR", "VILLA", "VINOS", "VIOLA", "VIRUS", "VISOR", "VISTA", "VIUDA", "VIVIR", "VIVOS",
    "VOCAL", "VOLAR", "VOTAR", "VOTOS", "VUELO", "YEGUA", "YEMAS", "YERBA", "YERNO", "ZAFAR",
    "ZANJA", "ZARPA", "ZORRO", "ZUECO", "ZUMOS", "ZURDO"
}

# Comprensión de conjuntos (Set Comprehension - Lab 02):
# Recorre PALABRAS_BASE, convierte cada palabra a mayúsculas (.upper()) y filtra SOLO las que tienen exactamente 5 letras (CONFIG_JUEGO[0]) y son puramente alfabéticas (.isalpha())
PALABRAS_RESPALDO: Set[str] = {p.upper() for p in PALABRAS_BASE if len(p) == CONFIG_JUEGO[0] and p.isalpha()}

# ==========================================
# LAB 02: ESTRUCTURAS DE DATOS - DICCIONARIOS (Dicts)
# ==========================================
# Diccionario que mapea vocales con tilde o diéresis a su vocal equivalente sin tilde para normalizar las jugadas del usuario
MAPA_ACENTOS: Dict[str, str] = {
    "Á": "A",
    "É": "E",
    "Í": "I",
    "Ó": "O",
    "Ú": "U",
    "Ü": "U"
}
