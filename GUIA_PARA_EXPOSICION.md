# 🎤 Guía Completa para tu Exposición — Proyecto Wordle CLI

Esta guía está diseñada para que puedas estudiar y explicar **para qué sirve toda la carpeta del proyecto**, **qué hace cada subcarpeta (`datos/`, `exportaciones/`)**, **qué hace cada archivo `.py`** y **cómo responder a las preguntas del profesor**.

---

## 1. ¿Para qué es esta carpeta del proyecto y cómo está organizada?

La carpeta raíz (`Proyecto N,T,N,Y`) contiene el **Proyecto Integrador de Programación en Python: Sistema Gestor y Juego Wordle CLI**.
En lugar de tener todo el código amontonado en un solo archivo, aplicamos **Arquitectura Modular por Responsabilidades** (Separación de Intereses):

### 📁 Subcarpetas del Proyecto (Se crean automáticamente con `pathlib.Path`)

1. **`datos/` (Carpeta de Persistencia Local y Auditoría)**
   - **¿Para qué sirve?**: Guarda toda la memoria del sistema en el computador para que cuando cierres y vuelvas a abrir el programa no se pierda nada, incluso si no hay internet.
   - **`datos/partidas_y_jugadores.json`**: Es la base de datos local en formato JSON. Guarda el diccionario de todos los jugadores registrados (con sus rachas, victorias y puntajes) y la lista histórica de todas las partidas jugadas.
   - **`datos/diccionario_personalizado.json`**: Guarda en formato JSON el catálogo activo de más de 320 palabras de 5 letras en español. Si agregas o eliminas una palabra en el menú 3, se actualiza aquí.
   - **`datos/bitacora_eventos.txt`**: Es un archivo de texto plano (`.txt`) que funciona como registro de auditoría (*log*). Cada vez que se guarda el estado, se registra un jugador o se exporta un CSV, escribe una línea con la fecha y hora exacta (`[YYYY-MM-DD HH:MM:SS] Evento...`).

2. **`exportaciones/` (Carpeta de Reportes para Excel / Analítica)**
   - **¿Para qué sirve?**: Almacena los reportes tabulares generados desde la **Opción 6** del menú principal en formato `.csv` (Valores Separados por Comas), listos para abrirse en Excel o LibreOffice Calc.
   - **`exportaciones/reporte_partidas.csv`**: Tabla con todas las partidas jugadas (ID, Fecha, Jugador, Palabra Secreta, Resultado, Intentos, Dificultad, Puntaje y la secuencia de palabras intentadas).
   - **`exportaciones/ranking_jugadores.csv`**: Tabla de posiciones ordenada del 1° al último puesto según el puntaje acumulado y porcentaje de victorias.

3. **`.venv/` (Carpeta oculta del Entorno Virtual de Python)**
   - **¿Para qué sirve?**: Aísla las librerías instaladas (`gspread`, `google-auth`, `python-dotenv`) para que no entren en conflicto con el sistema operativo Linux.

---

## 2. Explicación Archivo por Archivo (Los 9 Módulos Python)

### 1️⃣ `config.py` — Configuración y Constantes Globales
- **Propósito**: Centraliza todas las rutas de archivos, constantes del juego y estructuras de datos base.
- **Qué destacar en la exposición**:
  - Usa `pathlib.Path(__file__).resolve().parent` (Lab 04) para construir rutas compatibles con Linux, Windows y Mac sin escribir barras `/` manuales.
  - Define **Tuplas inmutables** (Lab 02) como `CONFIG_JUEGO = (5, 6)` (5 letras, 6 intentos) y `NIVELES_DIFICULTAD` (Fácil: 7 intentos x0.8, Normal: 6 intentos x1.0, Experto: 4 intentos x1.5).
  - Define un **Conjunto (`Set`)** llamado `PALABRAS_BASE` y aplica una **Comprensión de Conjuntos (*Set Comprehension*)** en `PALABRAS_RESPALDO` para filtrar automáticamente palabras de 5 letras sin duplicados.
  - Define el **Diccionario** `MAPA_ACENTOS` para quitar tildes (`Á -> A`).

### 2️⃣ `modelos.py` — Programación Orientada a Objetos (Herencia, Polimorfismo y Composición)
- **Propósito**: Modela las entidades del mundo real en clases de Python (Lab 03 y Lab 04).
- **Qué destacar en la exposición**:
  - **Superclase `Participante`**: Clase padre con atributos protegidos (`_alias`, `_categoria`, `_activo`) y encapsulamiento mediante `@property` (getters) y `@alias.setter` (setters con validación `raise ValueError`).
  - **Subclase `JugadorRegistrado(Participante)`**: Aplica **Herencia** (`super().__init__()`). Lleva cuenta de partidas jugadas, ganadas, racha actual y puntaje acumulado. **Sobrescribe (`Override`)** el método `calcular_bonificacion()` para sumar +25 puntos por cada victoria en racha y +20% extra si es categoría `VIP` o `Pro`.
  - **Subclase `JugadorInvitado(Participante)`**: Segunda clase hija que demuestra **Polimorfismo**: también tiene el método `calcular_bonificacion()`, pero en vez de dar bono de racha, otorga el 90% del puntaje base (`puntaje_base * 0.9`).
  - **Clase `RegistroPartida`**: Demuestra **Composición**, ya que combina los datos de un `Participante` con las métricas técnicas del turno jugado (palabra secreta, intentos usados, lista de palabras intentadas y fecha).

### 3️⃣ `validaciones.py` — Sanitización y Excepciones Personalizadas
- **Propósito**: Evitar que el programa se rompa si el usuario ingresa números donde van letras, textos vacíos o palabras de longitud incorrecta.
- **Qué destacar en la exposición**:
  - Crea la excepción propia `ErrorValidacionWordle(Exception)` heredando de `Exception` (Lab 04).
  - El método `validar_entero_rango()` demuestra el bloque completo **`try / except / else / finally`** junto con lanzamiento explícito de errores mediante **`raise`**.

### 4️⃣ `logica_juego.py` — Motor Algorítmico de Wordle (`MotorWordle`)
- **Propósito**: Contiene exclusivamente las reglas del juego Wordle (sin mezclar `input()` ni `print()`).
- **Qué destacar en la exposición (¡Pregunta fija de examen!)**:
  - **¿Cómo funciona el algoritmo de evaluación de letras (`registrar_intento`)?**:
    Usa un **algoritmo en dos pasadas con un diccionario de frecuencias** (`frecuencia_restante`):
    1. **Conteo**: Cuenta cuántas veces aparece cada letra en la palabra secreta (ej. en `"MOTOR"`, la `'O'` vale `2`).
    2. **Primera pasada (VERDE)**: Recorre las 5 posiciones buscando coincidencias exactas (`palabra[i] == secreta[i]`). Si coincide, la marca `VERDE` y resta `1` en el diccionario de frecuencias.
    3. **Segunda pasada (AMARILLO)**: Recorre las casillas que no fueron verdes. Si la letra aún tiene frecuencia disponible `> 0` en el diccionario, la marca `AMARILLO` y resta `1`. Si ya está en `0` o no existe, queda `GRIS`.
    - *¿Por qué en dos pasadas?* Porque si la palabra secreta tiene una sola `'A'` y el jugador escribe dos `'A'`, la que está en la posición correcta (Verde) debe tener prioridad sobre la que está desubicada.

### 5️⃣ `persistencia.py` — Persistencia Híbrida (Local JSON/CSV/TXT + Google Sheets)
- **Propósito**: Guardar y leer toda la información tanto en archivos locales como en la nube.
- **Qué destacar en la exposición**:
  - **`GestorArchivosLocales`**: Usa `pathlib.Path.open()` con bloques `with` y `try/except/else/finally` para escribir:
    - Archivos `.json` (`json.dump` y `json.load`).
    - Archivos `.csv` (`csv.writer` y `writerow`).
    - Archivo `.txt` (`mode="a"` para agregar eventos al final de la bitácora).
  - **`GestorGoogleSheets`**: Sincroniza en tiempo real 3 hojas en la nube (`Palabras`, `Puntajes` y `Jugadores`). Usa **`append_row()`** para insertar cada nueva partida jugada en la hoja `Puntajes` y actualiza el ranking global en `Jugadores`. Además, si no hay internet, pasa automáticamente a **Modo Local (Offline)** sin que el juego falle.

### 6️⃣ `gestion_datos.py` — Gestor de Colecciones CRUD y Reportes Estadísticos
- **Propósito**: Conecta los modelos con la persistencia y realiza los cálculos analíticos.
- **Qué destacar en la exposición**:
  - **`GestorColecciones`**: Administra en memoria un **Diccionario** de jugadores (`_jugadores`), una **Lista** de partidas (`_partidas`) y un **Conjunto (`Set`)** de palabras (`_catalogo_palabras`). Implementa todo el CRUD (Crear, Leer, Actualizar, Cambiar estado Activo/Inactivo) y los filtros combinados de partidas.
  - **`GeneradorReportes`**: Calcula el porcentaje de victorias global, el promedio de intentos en partidas ganadas, la palabra más jugada, el desglose agrupado por dificultad y la distribución de victorias por intento (1 al 7).

### 7️⃣ `interfaz_cli.py` — Interfaz Gráfica en Terminal con Colores ANSI
- **Propósito**: Dibujar el menú, el tablero de Wordle, el teclado QWERTY y las tablas de datos.
- **Qué destacar en la exposición**:
  - Usa **secuencias de escape ANSI** (`\033[1;97;42m` para fondo verde, `\033[1;97;43m` para fondo amarillo, `\033[1;97;100m` para fondo gris) y símbolos adicionales (`[A]`, `(A)`, `·A·`) para que sea accesible incluso en terminales sin color.

### 8️⃣ `main.py` — Controlador Principal y Menú Interactivo
- **Propósito**: Es el punto de entrada que se ejecuta con `python3 main.py`.
- **Qué destacar en la exposición**:
  - La clase `AplicacionWordle` une todas las piezas y ejecuta un ciclo `while True` con las 8 opciones del sistema (`[1]` Jugar, `[2]` Gestión de Jugadores, `[3]` Catálogo de Palabras, `[4]` Búsqueda y Filtros de Partidas, `[5]` Reportes y Ranking, `[6]` Exportar CSV, `[7]` Autotest y `[0]` Guardar y Salir).

### 9️⃣ `tests_wordle.py` y `configurar_sheets.py` — Pruebas y Diagnóstico
- **`tests_wordle.py`**: Contiene 4 pruebas unitarias automáticas con `unittest` que verifican herencia/polimorfismo, validaciones/excepciones, el algoritmo de dos pasadas del motor y el cálculo de reportes.
- **`configurar_sheets.py`**: Asistente paso a paso para diagnosticar y preparar las 3 pestañas del documento de Google Sheets.

---

## 3. Posibles Preguntas del Profesor y Cómo Responderlas

1. **¿Dónde aplicaron Herencia y Polimorfismo (Lab 04)?**
   - *"En `modelos.py`: creamos la superclase `Participante` y dos subclases que heredan de ella: `JugadorRegistrado` y `JugadorInvitado`. El polimorfismo se ve en el método `calcular_bonificacion(puntaje_base)`: cuando termina la partida, el sistema llama al mismo método sin importar qué tipo de jugador sea, pero `JugadorRegistrado` suma bonificación por racha y categoría VIP/Pro, mientras que `JugadorInvitado` retorna el 90% del puntaje."*

2. **¿Dónde usaron Listas, Tuplas, Conjuntos (`Set`) y Diccionarios (Lab 02)?**
   - **Tuplas**: En `config.py` para `CONFIG_JUEGO = (5, 6)` y `NIVELES_DIFICULTAD`, porque son configuraciones constantes que no deben modificarse durante la ejecución.
   - **Conjuntos (`Set`)**: Para el catálogo de palabras (`_catalogo_palabras`), porque un `Set` impide automáticamente palabras duplicadas y permite buscar si una palabra existe en tiempo instantáneo $O(1)$.
   - **Diccionarios**: En `_jugadores` (para buscar jugadores por su alias), en `_estado_teclado` (para asociar cada letra `A-Z` con su color) y en el conteo de frecuencias de letras del algoritmo de Wordle.
   - **Listas**: En `_partidas` y `_historial_intentos`, porque necesitamos mantener el orden cronológico exacto en que se jugaron los turnos y las partidas.

3. **¿Qué pasa si se va el internet en plena exposición?**
   - *"El sistema tiene persistencia híbrida tolerante a fallos en `persistencia.py`. Si no hay conexión a Google Sheets, captura la excepción automáticamente y trabaja con los archivos locales `datos/partidas_y_jugadores.json` y `datos/diccionario_personalizado.json` sin detenerse jamás."*
