"""
Módulo de configuración y constantes globales del proyecto Wordle CLI.
Integra:
- Lab 01: Constantes por convención, tipos de datos primitivos.
- Lab 02: Tuplas (inmutabilidad), Conjuntos (sets), Diccionarios y Comprensiones.
- Lab 04: Uso de `pathlib.Path` y carga segura de variables de entorno desde `.env` (`python-dotenv`).
"""

import os
from pathlib import Path
from typing import Tuple, Set, Dict, Optional

try:
    from dotenv import load_dotenv
    DOTENV_DISPONIBLE = True
except ImportError:
    DOTENV_DISPONIBLE = False

# ==========================================
# LAB 04: USO DE PATHLIB Y CARGA DE .ENV
# ==========================================
DIRECTORIO_BASE: Path = Path(__file__).resolve().parent
ARCHIVO_ENV: Path = DIRECTORIO_BASE / ".env"

if DOTENV_DISPONIBLE and ARCHIVO_ENV.exists():
    load_dotenv(dotenv_path=ARCHIVO_ENV)

DIRECTORIO_DATOS: Path = DIRECTORIO_BASE / "datos"
DIRECTORIO_EXPORTACIONES: Path = DIRECTORIO_BASE / "exportaciones"

# Rutas de archivos locales (JSON, TXT, CSV)
ARCHIVO_HISTORIAL_JSON: Path = DIRECTORIO_DATOS / "partidas_y_jugadores.json"
ARCHIVO_PALABRAS_JSON: Path = DIRECTORIO_DATOS / "diccionario_personalizado.json"
ARCHIVO_BITACORA_TXT: Path = DIRECTORIO_DATOS / "bitacora_eventos.txt"
ARCHIVO_REPORTE_CSV: Path = DIRECTORIO_EXPORTACIONES / "reporte_partidas.csv"
ARCHIVO_RANKING_CSV: Path = DIRECTORIO_EXPORTACIONES / "ranking_jugadores.csv"

# Configuración de Google Sheets leída desde variables de entorno (.env)
RUTA_CREDENCIALES_DEFAULT: str = os.getenv(
    "GOOGLE_CREDENTIALS_PATH",
    str(DIRECTORIO_BASE / "credentials.json")
)
NOMBRE_DOCUMENTO_SHEETS: str = os.getenv("GOOGLE_SHEET_NAME", "Wordle_DB")
ID_DOCUMENTO_SHEETS: str = os.getenv(
    "GOOGLE_SHEET_ID",
    "17_TzEIOid9tCwlmm0NzOPqM2sIY6pix9Z_raB41usOc"
)
URL_DOCUMENTO_SHEETS: str = f"https://docs.google.com/spreadsheets/d/{ID_DOCUMENTO_SHEETS}/edit"
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
    private_key = os.getenv("GCP_PRIVATE_KEY")
    client_email = os.getenv("GCP_CLIENT_EMAIL")
    project_id = os.getenv("GCP_PROJECT_ID")

    if not private_key or not client_email or not project_id:
        return None

    clave_formateada = private_key.replace("\\n", "\n")

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
CONFIG_JUEGO: Tuple[int, int] = (5, 6)

NIVELES_DIFICULTAD: Tuple[Tuple[str, str, int, float], ...] = (
    ("1", "Fácil (7 intentos)", 7, 0.8),
    ("2", "Normal (6 intentos)", 6, 1.0),
    ("3", "Experto (4 intentos)", 4, 1.5),
)

HOJAS_GOOGLE_SHEETS: Tuple[str, str, str] = ("Palabras", "Puntajes", "Jugadores")

# ==========================================
# LAB 02: ESTRUCTURAS DE DATOS - CONJUNTOS (Sets) y COMPRENSIONES
# ==========================================
# Catálogo de 150 palabras 100% en español de exactamente 5 letras
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

# Comprensión de conjuntos: filtra automáticamente solo aquellas de exactamente 5 letras en mayúsculas
PALABRAS_RESPALDO: Set[str] = {p.upper() for p in PALABRAS_BASE if len(p) == CONFIG_JUEGO[0] and p.isalpha()}

# ==========================================
# LAB 02: ESTRUCTURAS DE DATOS - DICCIONARIOS (Dicts)
# ==========================================
MAPA_ACENTOS: Dict[str, str] = {
    "Á": "A",
    "É": "E",
    "Í": "I",
    "Ó": "O",
    "Ú": "U",
    "Ü": "U"
}
