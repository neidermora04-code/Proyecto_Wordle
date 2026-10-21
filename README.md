# 🎮 Proyecto Wordle CLI en Python (Sincronizado con Google Sheets)

Sistema interactivo del juego **Wordle en Español** por consola (CLI) con persistencia híbrida: **Base de Datos en Tiempo Real en Google Sheets (`Wordle_DB`)** + respaldo automático local en archivos **JSON, CSV y TXT**.

---

## 🚀 Requisitos y Dependencias

- **Python 3.8 o superior** instalado.
- **Conexión a Internet** (para sincronizar automáticamente palabras, partidas y el ranking de jugadores con Google Sheets; si no hay internet, funciona en Modo Local).

### Librerías del proyecto (`requirements.txt`)
El proyecto incluye conexión directa mediante la librería estándar de Python (`urllib`), por lo que **funciona de inmediato al clonarlo** sin necesidad de configurar archivos `.env`. Adicionalmente, para el soporte extendido con cuenta de servicio de Google Cloud se listan en `requirements.txt`:

- `gspread>=6.0.0` — Cliente para la API de Google Sheets.
- `google-auth>=2.28.0` — Autenticación con Google Cloud.
- `python-dotenv>=1.0.0` — Carga de variables de entorno (`.env`).

---

## 💻 Cómo descargar y ejecutar el proyecto (Visual Studio Code / Terminal)

Abre la terminal en **Visual Studio Code** (`Ctrl + Ñ`) y sigue estos pasos según tu sistema operativo:

### 1. Clonar el repositorio
```bash
git clone https://github.com/neidermora04-code/Proyecto_Wordle.git
cd Proyecto_Wordle
```

### 2. Instalar dependencias (Opcional / Recomendado)
```bash
pip install -r requirements.txt
```

### 3. Ejecutar el juego
- **En Windows:**
  ```powershell
  python main.py
  ```
- **En Linux / macOS:**
  ```bash
  python3 main.py
  ```

---

## 🔄 Si ya habías clonado el proyecto antes (Actualizar a la última versión)

Si ya tenías la carpeta descargada en tu computador, ejecuta esto dentro de la carpeta `Proyecto_Wordle` para traer los últimos cambios y conectarte a la base de datos:

```bash
git pull
python main.py
```

---

## ☁️ Verificación de Conexión a la Base de Datos

Al iniciar `python main.py`, verás en la parte superior del menú:
- `Persistencia: ● CONECTADO (Google Sheets + JSON Local)` -> **Conectado en tiempo real.** Todas las partidas jugadas, jugadores nuevos y palabras agregadas se guardan automáticamente en la hoja de Google Sheets compartida.
- También puedes ejecutar las pruebas automáticas del sistema con:
  ```bash
  python tests_wordle.py
  ```

---

## 📂 Estructura del Proyecto

- `main.py` — Punto de entrada y menú interactivo principal.
- `config.py` — Constantes globales, configuración de dificultades y enlaces a Google Sheets.
- `logica_juego.py` — Motor algorítmico de validación de intentos de Wordle.
- `modelos.py` — Clases POO (`Persona`, `Jugador`, `JugadorRegistrado`, `JugadorInvitado`, `PartidaWordle`).
- `persistencia.py` — Conexión híbrida a Google Sheets (Web App / `gspread`) y archivos locales (`JSON`, `CSV`, `TXT`).
- `gestion_datos.py` — CRUD de jugadores, palabras, búsquedas, filtros y estadísticas.
- `interfaz_cli.py` — Interfaz gráfica en terminal con colores ANSI y teclado dinámico.
- `validaciones.py` — Sanitización de entradas, acentos y validaciones.
- `tests_wordle.py` — Suite de pruebas unitarias (`unittest`).
