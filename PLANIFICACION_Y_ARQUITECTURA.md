# Documentación del Proyecto Integrador: Sistema Gestor y Juego Wordle CLI (Linux)

---

## 1. Selección y Definición del Proyecto

### Problema Identificado y Propósito de la Aplicación
En entornos de aprendizaje y entrenamiento cognitivo por consola (Linux), los juegos de deducción léxica suelen carecer de un sistema administrativo que gestione perfiles de usuarios, controle catálogos de vocabulario, audite resultados históricos y genere analítica de desempeño tanto en local como en la nube.

**Wordle CLI — Sistema Gestor y Analítico de Partidas** resuelve este problema integrando un motor de juego interactivo en terminal con una plataforma administrativa completa que permite:
1. Gestionar el ciclo de vida de **Jugadores** (altas, bajas lógicas/cambios de estado, actualización de categoría y seguimiento de rachas).
2. Administrar dinámicamente el **Catálogo de Palabras Secretas** (validación, búsqueda, alta y baja de vocabulario).
3. Persistir cada partida y perfil en archivos locales (**JSON** y bitácoras **TXT**), exportar reportes tabulares (**CSV**) y sincronizar en tiempo real con **Google Sheets** mediante una cuenta de servicio (`gspread`).

### Usuarios Principales
- **Jugadores / Estudiantes:** Usuarios que interactúan con el tablero ANSI en consola en distintos niveles de dificultad (*Fácil*, *Normal*, *Experto*).
- **Administradores / Docentes:** Usuarios que administran el diccionario de palabras, auditan el historial de partidas mediante filtros, consultan reportes estadísticos agrupados y exportan clasificaciones en CSV o Google Sheets.

---

## 2. Cumplimiento de Requisitos Técnicos por Laboratorio

| Laboratorio | Temas Técnicos Aplicados en el Código | Archivos Donde se Implementan |
| :--- | :--- | :--- |
| **Lab 01 — Primeros pasos** | Variables tipadas, constantes por convención (`CONFIG_JUEGO`), operadores aritméticos y relacionales, conversiones (`int()`, `float()`, `str()`), `input()`, `print()` y f-strings. | [`config.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/config.py), [`interfaz_cli.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/interfaz_cli.py), [`main.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/main.py) |
| **Lab 02 — Decisiones, ciclos y colecciones** | Condicionales compuestos (`if/elif/else`), operadores lógicos (`and`, `or`, `not`), ciclos `for` y `while`, **listas**, **tuplas**, **conjuntos (`set`)**, **diccionarios**, estructuras anidadas y comprensiones de listas/conjuntos/diccionarios. | [`config.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/config.py), [`logica_juego.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/logica_juego.py), [`gestion_datos.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/gestion_datos.py) |
| **Lab 03 — Funciones, módulos y POO** | Separación en 7 módulos especializados, clases con `__init__`, `self`, atributos protegidos (`_`), `@property` y `@setter`, métodos de instancia/clase/estáticos y colaboración entre objetos. | [`modelos.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/modelos.py), [`logica_juego.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/logica_juego.py), [`gestion_datos.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/gestion_datos.py) |
| **Lab 04 — Excepciones, archivos, persistencia y POO avanzada** | Bloques completos `try / except / else / finally`, lanzamiento con `raise`, excepción propia (`ErrorValidacionWordle`), rutas con `pathlib.Path`, archivos `.txt`, persistencia `.json`, exportación `.csv`, **Google Sheets (`gspread`)**, **herencia** (`Participante` $\rightarrow$ `JugadorRegistrado`, `JugadorInvitado`), **sobrescritura**, **polimorfismo** y **composición**. | [`modelos.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/modelos.py), [`validaciones.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/validaciones.py), [`persistencia.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/persistencia.py), [`tests_wordle.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/tests_wordle.py) |

---

## 3. Arquitectura y Organización Modular del Código

El proyecto evita concentrar la lógica en un solo archivo, separando estrictamente cada responsabilidad:

1. **[`config.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/config.py)**: Constantes globales, rutas con `pathlib.Path`, tuplas de configuración y conjuntos de palabras base.
2. **[`modelos.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/modelos.py)**: Modelos y entidades del dominio (`Participante`, `JugadorRegistrado`, `JugadorInvitado`, `RegistroPartida`) aplicando herencia, polimorfismo y composición.
3. **[`validaciones.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/validaciones.py)**: Validación de datos y excepción de dominio `ErrorValidacionWordle` con uso de `raise` y `try/except/else/finally`.
4. **[`logica_juego.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/logica_juego.py)**: Reglas de negocio de Wordle (`MotorWordle`), algoritmo de evaluación en dos pasadas y cálculo de puntajes.
5. **[`persistencia.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/persistencia.py)**: Persistencia en archivos JSON, exportación CSV, bitácora TXT (`GestorArchivosLocales`) y conexión con Google Sheets (`GestorGoogleSheets`).
6. **[`gestion_datos.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/gestion_datos.py)**: Gestión de colecciones (`GestorColecciones`) y generación de reportes estadísticos (`GeneradorReportes`).
7. **[`interfaz_cli.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/interfaz_cli.py)**: Interacción visual con el usuario por consola mediante secuencias ANSI nativas.
8. **[`tests_wordle.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/tests_wordle.py)**: Suite de pruebas unitarias e integrales con `unittest`.
9. **[`main.py`](file:///home/andres/Escritorio/Proyecto%20N,T,N,Y/main.py)**: Punto de entrada y controlador del menú interactivo.

---

## 4. Planificación y Autogestión del Proyecto (3 Sprints)

### Sprint 1: Núcleo del Dominio, Validaciones y Motor Base (Incremento 1)
- **Alcance y Objetivos:** Construir el motor funcional del juego Wordle en consola, las estructuras de datos base y el módulo de validaciones.
- **Historias de Usuario:**
  - *HU-01:* Como jugador, quiero ingresar palabras de 5 letras y recibir retroalimentación en colores ANSI (Verde, Amarillo, Gris) para deducir la palabra secreta.
  - *HU-02:* Como usuario, quiero que el sistema valide entradas vacías, caracteres no alfabéticos o longitudes incorrectas sin que el programa se cierre abruptamente.
- **Tareas Técnicas:**
  - Definir constantes, tuplas y sets en `config.py`.
  - Implementar `ValidadorDatos` y `ErrorValidacionWordle` en `validaciones.py`.
  - Programar el algoritmo de dos pasadas en `MotorWordle` (`logica_juego.py`) y el renderizado ANSI en `interfaz_cli.py`.
- **Incremento Funcional:** Juego Wordle jugable en consola con validación de entradas.

### Sprint 2: Jerarquía POO, Gestión de Colecciones y Persistencia Local/Nube (Incremento 2)
- **Alcance y Objetivos:** Incorporar la jerarquía de clases con herencia y polimorfismo, el menú administrativo CRUD y la persistencia en JSON, TXT y Google Sheets.
- **Historias de Usuario:**
  - *HU-03:* Como administrador, quiero registrar, consultar, actualizar y activar/desactivar jugadores (`JugadorRegistrado` / `JugadorInvitado`) para llevar el control de rachas y bonificaciones.
  - *HU-04:* Como administrador, quiero agregar y eliminar palabras del catálogo y que todos los cambios persistan automáticamente en archivos JSON y Google Sheets.
- **Tareas Técnicas:**
  - Desarrollar `Participante`, `JugadorRegistrado`, `JugadorInvitado` y `RegistroPartida` en `modelos.py`.
  - Implementar `GestorArchivosLocales` (JSON y TXT con `pathlib`) y `GestorGoogleSheets` (`gspread` y `append_row`) en `persistencia.py`.
  - Construir `GestorColecciones` en `gestion_datos.py`.
- **Incremento Funcional:** Aplicación con menú interactivo, persistencia entre ejecuciones y conexión a Google Sheets.

### Sprint 3: Búsquedas, Reportes Estadísticos, Exportación CSV y Pruebas (Incremento 3 - Entrega Final)
- **Alcance y Objetivos:** Completar las consultas filtradas, el motor de reportes agrupados, la exportación a CSV y la validación de calidad mediante pruebas automatizadas.
- **Historias de Usuario:**
  - *HU-05:* Como analista, quiero filtrar partidas por jugador, resultado o dificultad y visualizar reportes agrupados con histograma de intentos.
  - *HU-06:* Como usuario, quiero exportar el ranking y el historial de partidas a archivos CSV y ejecutar pruebas automatizadas para comprobar la integridad de los datos.
- **Tareas Técnicas:**
  - Implementar `GeneradorReportes` en `gestion_datos.py`.
  - Añadir métodos `exportar_partidas_csv` y `exportar_ranking_csv` en `persistencia.py`.
  - Crear la suite `PruebasIntegridadWordle` en `tests_wordle.py`.
- **Mecanismos de Seguimiento y Revisión:**
  - Tablero Kanban por sprint, revisión de código cruzada entre integrantes, verificación con `unittest` antes de cada cierre de sprint y bitácora automática en `datos/bitacora_eventos.txt`.
