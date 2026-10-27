#!/usr/bin/env python3
"""
Script de Diagnóstico, Vinculación e Inicialización Automática de Google Sheets.
Prioriza la lectura de credenciales desde el archivo `.env` (para proteger el repositorio GitHub)
o desde `credentials.json` como respaldo.
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
    HOJAS_GOOGLE_SHEETS,
    PALABRAS_RESPALDO,
    obtener_credenciales_desde_env
)#!/usr/bin/env python3
"""
Script de Diagnóstico, Vinculación e Inicialización Automática de Google Sheets.
Prioriza la lectura de credenciales desde el archivo `.env` (para proteger el repositorio GitHub)
o desde `credentials.json` como respaldo.
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
    HOJAS_GOOGLE_SHEETS,
    PALABRAS_RESPALDO,
    obtener_credenciales_desde_env
)


def verificar_y_configurar_sheets() -> None:
    """Ejecuta un diagnóstico de 6 pasos para inicializar las pestañas en Google Sheets."""
    ruta_cred = Path(RUTA_CREDENCIALES_DEFAULT)
    credenciales_env = obtener_credenciales_desde_env()

    print("\n=====================================================================")
    print("   ASISTENTE DE VINCULACIÓN CON GOOGLE SHEETS (.env / Service Account)")
    print("=====================================================================\n")
    print(f"Documento vinculado: {URL_DOCUMENTO_SHEETS}")
    print(f"ID del documento   : {ID_DOCUMENTO_SHEETS}\n")

    # PASO 1: Verificar que la librería 'gspread' esté instalada
    try:
        import gspread
        from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
        print("[✓] Paso 1: Librerías 'gspread' y 'python-dotenv' detectadas correctamente.")
    except ImportError:
        print("[✗] Error: La librería 'gspread' no está instalada en el entorno actual.")
        print("    Ejecuta el comando usando el entorno virtual:")
        print("    ./.venv/bin/python configurar_sheets.py")
        sys.exit(1)

    # PASO 2: Verificar existencia de credenciales en '.env' o en 'credentials.json'
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

    print("\n    >>> EMAIL DE TU SERVICE ACCOUNT: <<<")
    print(f"    \033[1;36m{client_email}\033[0m\n")

    # PASO 3: Autenticar con Google Cloud y abrir el documento de Google Sheets
    print(f"[...] Paso 3: Conectando con tu Google Sheet (ID: {ID_DOCUMENTO_SHEETS})...")
    try:
        if credenciales_env is not None:
            cliente = gspread.service_account_from_dict(credenciales_env)
        else:
            cliente = gspread.service_account(filename=str(ruta_cred))

        try:
            documento = cliente.open_by_key(ID_DOCUMENTO_SHEETS)
        except SpreadsheetNotFound:
            documento = cliente.open(NOMBRE_DOCUMENTO_SHEETS)
        print(f"[✓] ¡Conexión exitosa con '{documento.title}'!")
    except Exception as err_api:
        print(f"\n[✗] No se pudo abrir o editar la hoja: {err_api}")
        sys.exit(1)

    # PASO 4: Verificar o crear la pestaña 'Palabras' y poblarla con el vocabulario inicial
    nombre_hoja_palabras, nombre_hoja_puntajes, nombre_hoja_jugadores = HOJAS_GOOGLE_SHEETS
    print(f"\n[...] Paso 4: Verificando pestaña '{nombre_hoja_palabras}'...")
    try:
        hoja_palabras = documento.worksheet(nombre_hoja_palabras)
        print(f"[✓] La pestaña '{nombre_hoja_palabras}' ya existe.")
    except WorksheetNotFound:
        hoja_palabras = documento.add_worksheet(title=nombre_hoja_palabras, rows=600, cols=5)
        print(f"[✓] Pestaña '{nombre_hoja_palabras}' creada automáticamente.")

    palabras_actuales = [p.strip().upper() for p in hoja_palabras.col_values(1) if p.strip()]
    if len(palabras_actuales) < 100:
        hoja_palabras.clear()
        filas_palabras = [[palabra] for palabra in sorted(list(PALABRAS_RESPALDO))]
        hoja_palabras.update(range_name=f"A1:A{len(filas_palabras)}", values=filas_palabras)
        print(f"[✓] ¡{len(filas_palabras)} palabras en español cargadas en la Columna A!")
    else:
        print(f"[✓] La pestaña '{nombre_hoja_palabras}' cuenta con {len(palabras_actuales)} palabras en español.")

    # PASO 5: Verificar o crear la pestaña 'Puntajes' con sus encabezados
    print(f"\n[...] Paso 5: Verificando pestaña '{nombre_hoja_puntajes}'...")
    try:
        hoja_puntajes = documento.worksheet(nombre_hoja_puntajes)
        print(f"[✓] La pestaña '{nombre_hoja_puntajes}' ya existe.")
    except WorksheetNotFound:
        hoja_puntajes = documento.add_worksheet(title=nombre_hoja_puntajes, rows=500, cols=10)
        print(f"[✓] Pestaña '{nombre_hoja_puntajes}' creada automáticamente.")

    encabezados_actuales = hoja_puntajes.row_values(1)
    if not encabezados_actuales:
        encabezados = [
            "Fecha", "Jugador", "Palabra Secreta", "Resultado",
            "Intentos", "Puntaje", "Dificultad", "Tipo Jugador", "ID Partida"
        ]
        hoja_puntajes.append_row(encabezados, value_input_option="USER_ENTERED")
        print(f"[✓] Encabezados insertados en '{nombre_hoja_puntajes}' con append_row().")

    # PASO 6: Verificar o crear la pestaña 'Jugadores' (Ranking Competitivo Global)
    print(f"\n[...] Paso 6: Verificando pestaña competitiva '{nombre_hoja_jugadores}'...")
    try:
        hoja_jugadores = documento.worksheet(nombre_hoja_jugadores)
        print(f"[✓] La pestaña '{nombre_hoja_jugadores}' ya existe.")
    except WorksheetNotFound:
        hoja_jugadores = documento.add_worksheet(title=nombre_hoja_jugadores, rows=200, cols=10)
        print(f"[✓] Pestaña '{nombre_hoja_jugadores}' creada automáticamente.")

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



def verificar_y_configurar_sheets() -> None:
    """Ejecuta un diagnóstico de 6 pasos para inicializar las pestañas en Google Sheets."""
    ruta_cred = Path(RUTA_CREDENCIALES_DEFAULT)
    credenciales_env = obtener_credenciales_desde_env()

    print("\n=====================================================================")
    print("   ASISTENTE DE VINCULACIÓN CON GOOGLE SHEETS (.env / Service Account)")
    print("=====================================================================\n")
    print(f"Documento vinculado: {URL_DOCUMENTO_SHEETS}")
    print(f"ID del documento   : {ID_DOCUMENTO_SHEETS}\n")

    # PASO 1: Verificar que la librería 'gspread' esté instalada
    try:
        import gspread
        from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
        print("[✓] Paso 1: Librerías 'gspread' y 'python-dotenv' detectadas correctamente.")
    except ImportError:
        print("[✗] Error: La librería 'gspread' no está instalada en el entorno actual.")
        print("    Ejecuta el comando usando el entorno virtual:")
        print("    ./.venv/bin/python configurar_sheets.py")
        sys.exit(1)

    # PASO 2: Verificar existencia de credenciales en '.env' o en 'credentials.json'
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

    print("\n    >>> EMAIL DE TU SERVICE ACCOUNT: <<<")
    print(f"    \033[1;36m{client_email}\033[0m\n")

    # PASO 3: Autenticar con Google Cloud y abrir el documento de Google Sheets
    print(f"[...] Paso 3: Conectando con tu Google Sheet (ID: {ID_DOCUMENTO_SHEETS})...")
    try:
        if credenciales_env is not None:
            cliente = gspread.service_account_from_dict(credenciales_env)
        else:
            cliente = gspread.service_account(filename=str(ruta_cred))

        try:
            documento = cliente.open_by_key(ID_DOCUMENTO_SHEETS)
        except SpreadsheetNotFound:
            documento = cliente.open(NOMBRE_DOCUMENTO_SHEETS)
        print(f"[✓] ¡Conexión exitosa con '{documento.title}'!")
    except Exception as err_api:
        print(f"\n[✗] No se pudo abrir o editar la hoja: {err_api}")
        sys.exit(1)

    # PASO 4: Verificar o crear la pestaña 'Palabras' y poblarla con el vocabulario inicial
    nombre_hoja_palabras, nombre_hoja_puntajes, nombre_hoja_jugadores = HOJAS_GOOGLE_SHEETS
    print(f"\n[...] Paso 4: Verificando pestaña '{nombre_hoja_palabras}'...")
    try:
        hoja_palabras = documento.worksheet(nombre_hoja_palabras)
        print(f"[✓] La pestaña '{nombre_hoja_palabras}' ya existe.")
    except WorksheetNotFound:
        hoja_palabras = documento.add_worksheet(title=nombre_hoja_palabras, rows=600, cols=5)
        print(f"[✓] Pestaña '{nombre_hoja_palabras}' creada automáticamente.")

    palabras_actuales = [p.strip().upper() for p in hoja_palabras.col_values(1) if p.strip()]
    if len(palabras_actuales) < 100:
        hoja_palabras.clear()
        filas_palabras = [[palabra] for palabra in sorted(list(PALABRAS_RESPALDO))]
        hoja_palabras.update(range_name=f"A1:A{len(filas_palabras)}", values=filas_palabras)
        print(f"[✓] ¡{len(filas_palabras)} palabras en español cargadas en la Columna A!")
    else:
        print(f"[✓] La pestaña '{nombre_hoja_palabras}' cuenta con {len(palabras_actuales)} palabras en español.")

    # PASO 5: Verificar o crear la pestaña 'Puntajes' con sus encabezados
    print(f"\n[...] Paso 5: Verificando pestaña '{nombre_hoja_puntajes}'...")
    try:
        hoja_puntajes = documento.worksheet(nombre_hoja_puntajes)
        print(f"[✓] La pestaña '{nombre_hoja_puntajes}' ya existe.")
    except WorksheetNotFound:
        hoja_puntajes = documento.add_worksheet(title=nombre_hoja_puntajes, rows=500, cols=10)
        print(f"[✓] Pestaña '{nombre_hoja_puntajes}' creada automáticamente.")

    encabezados_actuales = hoja_puntajes.row_values(1)
    if not encabezados_actuales:
        encabezados = [
            "Fecha", "Jugador", "Palabra Secreta", "Resultado",
            "Intentos", "Puntaje", "Dificultad", "Tipo Jugador", "ID Partida"
        ]
        hoja_puntajes.append_row(encabezados, value_input_option="USER_ENTERED")
        print(f"[✓] Encabezados insertados en '{nombre_hoja_puntajes}' con append_row().")

    # PASO 6: Verificar o crear la pestaña 'Jugadores' (Ranking Competitivo Global)
    print(f"\n[...] Paso 6: Verificando pestaña competitiva '{nombre_hoja_jugadores}'...")
    try:
        hoja_jugadores = documento.worksheet(nombre_hoja_jugadores)
        print(f"[✓] La pestaña '{nombre_hoja_jugadores}' ya existe.")
    except WorksheetNotFound:
        hoja_jugadores = documento.add_worksheet(title=nombre_hoja_jugadores, rows=200, cols=10)
        print(f"[✓] Pestaña '{nombre_hoja_jugadores}' creada automáticamente.")

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
