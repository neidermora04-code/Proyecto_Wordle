#!/usr/bin/env python3
"""
Script de Diagnóstico, Vinculación e Inicialización Automática de Google Sheets.

¿QUÉ NECESITA ESTE ARCHIVO PARA FUNCIONAR?
1. Entorno Virtual (.venv) con las librerías de `requirements.txt`:
   - `gspread` (para conectarse a la API de Google Sheets)
   - `google-auth` (para autenticar la cuenta de servicio de Google Cloud)
   - `python-dotenv` (para leer las variables ocultas del archivo `.env`)
2. Credenciales de conexión (funciona de 2 formas automáticas):
   - FORMA A (Administrador con `.env` o `credentials.json`): Lee las claves privadas de la
     Service Account desde el archivo local `.env` (que no se sube a GitHub por seguridad)
     y requiere haber compartido la hoja de Google Sheets con el correo `GCP_CLIENT_EMAIL` como Editor.
   - FORMA B (Compañeros que clonan desde GitHub sin `.env`): Utiliza automáticamente la
     `URL_WEBAPP_SHEETS` configurada en `config.py` mediante `urllib.request`, permitiendo
     verificar y sincronizar las 3 pestañas (`Palabras`, `Puntajes`, `Jugadores`) sin necesitar claves locales.
"""

# Importamos json para leer archivos de credenciales, sys para salir con códigos de estado y Path para rutas
import json
import sys
from pathlib import Path

# Importamos la configuración de Google Sheets definida en config.py
from config import (
    RUTA_CREDENCIALES_DEFAULT,
    NOMBRE_DOCUMENTO_SHEETS,
    ID_DOCUMENTO_SHEETS,
    URL_DOCUMENTO_SHEETS,
    URL_WEBAPP_SHEETS,
    HOJAS_GOOGLE_SHEETS,
    PALABRAS_RESPALDO,
    obtener_credenciales_desde_env
)
# Importamos GestorGoogleSheets para respaldar la verificación vía WebApp cuando no hay archivo .env
from persistencia import GestorGoogleSheets


def verificar_y_configurar_sheets() -> None:
    """Ejecuta un diagnóstico de 6 pasos para inicializar las pestañas en Google Sheets."""
    # Convertimos la ruta de credenciales a un objeto Path de pathlib
    ruta_cred = Path(RUTA_CREDENCIALES_DEFAULT)
    # Intentamos cargar el diccionario de credenciales desde el archivo oculto '.env'
    credenciales_env = obtener_credenciales_desde_env()

    print("\n=====================================================================")
    print("   ASISTENTE DE VINCULACIÓN CON GOOGLE SHEETS (.env / WebApp Cloud)")
    print("=====================================================================\n")
    print(f"Documento vinculado: {URL_DOCUMENTO_SHEETS}")
    print(f"ID del documento   : {ID_DOCUMENTO_SHEETS}\n")

    # =========================================================================
    # CASO AUTOMÁTICO PARA QUIENES CLONAN DESDE GITHUB (SIN ARCHIVO .env LOCAL)
    # =========================================================================
    if credenciales_env is None and not ruta_cred.exists() and URL_WEBAPP_SHEETS:
        print("[i] No se detectó archivo '.env' local. Probando conexión directa vía WebApp HTTP...")
        gestor = GestorGoogleSheets(
            ruta_credenciales=RUTA_CREDENCIALES_DEFAULT,
            nombre_documento=NOMBRE_DOCUMENTO_SHEETS
        )
        if gestor.esta_conectado:
            palabras = gestor.obtener_palabras(PALABRAS_RESPALDO)
            partidas = gestor.obtener_partidas_nube()
            jugadores = gestor.obtener_jugadores_nube()
            print(f"[✓] ¡Conexión WebApp exitosa con Google Sheets!")
            print(f"[✓] Pestaña 'Palabras'  : {len(palabras)} palabras sincronizadas.")
            print(f"[✓] Pestaña 'Puntajes'  : {len(partidas)} partidas globales registradas.")
            print(f"[✓] Pestaña 'Jugadores' : {len(jugadores)} jugadores en el ranking competitivo.")
            print("\n=====================================================================")
            print("  \033[1;32m¡CONEXIÓN COMPETITIVA ONLINE LISTA! (Palabras + Puntajes + Jugadores)\033[0m")
            print("  Ejecuta el juego con: python main.py")
            print("=====================================================================\n")
            return

    # =========================================================================
    # PASO 1: Verificar que la librería 'gspread' esté instalada en el entorno
    # =========================================================================
    try:
        import gspread
        from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
        print("[✓] Paso 1: Librerías 'gspread' y 'python-dotenv' detectadas correctamente.")
    except ImportError:
        print("[✗] Error: La librería 'gspread' no está instalada en el entorno actual.")
        print("    Instálala con: pip install -r requirements.txt")
        print("    O ejecuta usando el entorno virtual: ./.venv/bin/python configurar_sheets.py")
        sys.exit(1)

    # =========================================================================
    # PASO 2: Verificar existencia de credenciales en '.env' o en 'credentials.json'
    # =========================================================================
    if credenciales_env is not None:
        client_email = credenciales_env.get("client_email", "NO_ENCONTRADO")
        project_id = credenciales_env.get("project_id", "DESCONOCIDO")
        print(f"[✓] Paso 2: Credenciales cargadas de forma segura desde el archivo '.env' (Proyecto: {project_id}).")
    elif ruta_cred.exists():
        try:
            with ruta_cred.open("r", encoding="utf-8") as f:
                datos_json = json.load(f)
            client_email = datos_json.get("client_email", "NO_ENCONTRADO")
            project_id = datos_json.get("project_id", "DESCONOCIDO")
            print(f"[✓] Paso 2: Credenciales cargadas desde '{ruta_cred.name}' (Proyecto: {project_id}).")
        except Exception as err:
            print(f"[✗] Error leyendo '{ruta_cred.name}': {err}")
            sys.exit(1)
    else:
        print("[✗] Paso 2: No se encontró el archivo '.env' ni 'credentials.json'.")
        print("    Copia el archivo '.env.example' a '.env' y coloca las variables de tu Service Account.")
        sys.exit(1)

    # Mostramos en pantalla el correo del bot (Service Account) al que se le da permiso de Editor en Google Sheets
    print("\n    >>> EMAIL DE TU SERVICE ACCOUNT (Debe tener permiso de Editor en la Hoja): <<<")
    print(f"    \033[1;36m{client_email}\033[0m\n")

    # =========================================================================
    # PASO 3: Autenticar con Google Cloud y abrir el documento de Google Sheets
    # =========================================================================
    print(f"[...] Paso 3: Conectando con tu Google Sheet (ID: {ID_DOCUMENTO_SHEETS})...")
    try:
        if credenciales_env is not None:
            # Autentica usando el diccionario leído desde '.env'
            cliente = gspread.service_account_from_dict(credenciales_env)
        else:
            # Autentica usando el archivo físico 'credentials.json'
            cliente = gspread.service_account(filename=str(ruta_cred))

        try:
            # Abre el documento de Google Sheets por su ID único
            documento = cliente.open_by_key(ID_DOCUMENTO_SHEETS)
        except SpreadsheetNotFound:
            # Si no lo encuentra por ID, intenta abrirlo por su nombre ("Wordle_DB")
            documento = cliente.open(NOMBRE_DOCUMENTO_SHEETS)
        print(f"[✓] ¡Conexión exitosa con '{documento.title}'!")
    except Exception as err_api:
        print(f"\n[✗] No se pudo abrir o editar la hoja: {err_api}")
        sys.exit(1)

    # =========================================================================
    # PASO 4: Verificar o crear la pestaña 'Palabras' y poblarla con el vocabulario inicial
    # =========================================================================
    nombre_hoja_palabras, nombre_hoja_puntajes, nombre_hoja_jugadores = HOJAS_GOOGLE_SHEETS
    print(f"\n[...] Paso 4: Verificando pestaña '{nombre_hoja_palabras}'...")
    try:
        hoja_palabras = documento.worksheet(nombre_hoja_palabras)
        print(f"[✓] La pestaña '{nombre_hoja_palabras}' ya existe.")
    except WorksheetNotFound:
        # Si la pestaña no existe, la crea automáticamente con 600 filas y 5 columnas
        hoja_palabras = documento.add_worksheet(title=nombre_hoja_palabras, rows=600, cols=5)
        print(f"[✓] Pestaña '{nombre_hoja_palabras}' creada automáticamente.")

    # Lee todas las palabras de la columna A (columna 1)
    palabras_actuales = [p.strip().upper() for p in hoja_palabras.col_values(1) if p.strip()]
    if len(palabras_actuales) < 100:
        # Si tiene menos de 100 palabras, sube el catálogo base de más de 320 palabras de 5 letras
        hoja_palabras.clear()
        filas_palabras = [[palabra] for palabra in sorted(list(PALABRAS_RESPALDO))]
        hoja_palabras.update(range_name=f"A1:A{len(filas_palabras)}", values=filas_palabras)
        print(f"[✓] ¡{len(filas_palabras)} palabras en español cargadas en la Columna A!")
    else:
        print(f"[✓] La pestaña '{nombre_hoja_palabras}' cuenta con {len(palabras_actuales)} palabras en español.")

    # =========================================================================
    # PASO 5: Verificar o crear la pestaña 'Puntajes' con sus encabezados
    # =========================================================================
    print(f"\n[...] Paso 5: Verificando pestaña '{nombre_hoja_puntajes}'...")
    try:
        hoja_puntajes = documento.worksheet(nombre_hoja_puntajes)
        print(f"[✓] La pestaña '{nombre_hoja_puntajes}' ya existe.")
    except WorksheetNotFound:
        hoja_puntajes = documento.add_worksheet(title=nombre_hoja_puntajes, rows=500, cols=10)
        print(f"[✓] Pestaña '{nombre_hoja_puntajes}' creada automáticamente.")

    # Verifica que la fila 1 tenga los encabezados de las columnas de Puntajes
    encabezados_actuales = hoja_puntajes.row_values(1)
    if not encabezados_actuales:
        encabezados = [
            "Fecha", "Jugador", "Palabra Secreta", "Resultado",
            "Intentos", "Puntaje", "Dificultad", "Tipo Jugador", "ID Partida"
        ]
        hoja_puntajes.append_row(encabezados, value_input_option="USER_ENTERED")
        print(f"[✓] Encabezados insertados en '{nombre_hoja_puntajes}' con append_row().")

    # =========================================================================
    # PASO 6: Verificar o crear la pestaña 'Jugadores' (Ranking Competitivo Global)
    # =========================================================================
    print(f"\n[...] Paso 6: Verificando pestaña competitiva '{nombre_hoja_jugadores}'...")
    try:
        hoja_jugadores = documento.worksheet(nombre_hoja_jugadores)
        print(f"[✓] La pestaña '{nombre_hoja_jugadores}' ya existe.")
    except WorksheetNotFound:
        hoja_jugadores = documento.add_worksheet(title=nombre_hoja_jugadores, rows=200, cols=10)
        print(f"[✓] Pestaña '{nombre_hoja_jugadores}' creada automáticamente.")

    # Verifica que la fila 1 tenga los encabezados de la tabla de Ranking de Jugadores
    encabezados_jug = hoja_jugadores.row_values(1)
    if not encabezados_jug:
        encabezados_ranking = [
            "Posición", "Alias", "Categoría", "Estado",
            "Partidas Jugadas", "Partidas Ganadas", "% Victorias", "Racha Actual", "Puntaje Total"
        ]
        hoja_jugadores.append_row(encabezados_ranking, value_input_option="USER_ENTERED")
        print(f"[✓] Encabezados insertados en '{nombre_hoja_jugadores}'.")

    print("\n=====================================================================")
    print("  \033[1;32m¡CONEXIÓN COMPETITIVA ONLINE LISTA! (Palabras + Puntajes + Jugadores)\033[0m")
    print("  Ejecuta el juego con: ./.venv/bin/python main.py")
    print("=====================================================================\n")


if __name__ == "__main__":
    verificar_y_configurar_sheets()
