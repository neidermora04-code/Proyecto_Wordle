#!/usr/bin/env python3
"""
Punto de entrada principal del Sistema Gestor y Juego Wordle CLI (Linux).
Integra los 4 Laboratorios:
- Menú interactivo de consola.
- Operaciones de registro, consulta y actualización (Jugadores y Catálogo de Palabras).
- Juego Wordle con niveles de dificultad y colores ANSI.
- Búsquedas, filtros, reportes estadísticos agrupados.
- Persistencia en JSON, bitácora TXT, exportación CSV y Google Sheets (`gspread` + `append_row`).
"""

# Importamos Tuple de typing para documentar el retorno del selector de dificultad
from typing import Tuple

# Importamos constantes globales desde nuestro módulo config.py
from config import (
    RUTA_CREDENCIALES_DEFAULT,
    NOMBRE_DOCUMENTO_SHEETS,
    CONFIG_JUEGO,
    NIVELES_DIFICULTAD
)
# Importamos el validador de entradas y la excepción de negocio propia
from validaciones import ValidadorDatos, ErrorValidacionWordle
# Importamos los gestores de persistencia local (JSON/CSV/TXT) y nube (Google Sheets)
from persistencia import GestorArchivosLocales, GestorGoogleSheets
# Importamos el administrador de colecciones en memoria y el generador de estadísticas
from gestion_datos import GestorColecciones, GeneradorReportes
# Importamos el motor con las reglas del juego Wordle
from logica_juego import MotorWordle
# Importamos la interfaz visual de consola (colores ANSI y tablas)
from interfaz_cli import InterfazConsola
# Importamos la función que ejecuta las pruebas automatizadas (unittest)
from tests_wordle import ejecutar_suite_pruebas


class AplicacionWordle:
    """
    Controlador principal que coordina la interacción con el usuario,
    las colecciones de dominio, el motor del juego y la persistencia híbrida.
    """

    def __init__(self) -> None:
        # Mensaje inicial al arrancar el programa
        print("Inicializando Sistema Wordle CLI... Cargando persistencia JSON y Google Sheets...")
        # 1. Instancia el gestor de archivos locales (crea carpetas datos/ y exportaciones/ si no existen)
        self._gestor_local = GestorArchivosLocales()
        # 2. Instancia el gestor de Google Sheets (conecta automáticamente a la nube)
        self._gestor_nube = GestorGoogleSheets(
            ruta_credenciales=RUTA_CREDENCIALES_DEFAULT,
            nombre_documento=NOMBRE_DOCUMENTO_SHEETS
        )
        # 3. Instancia el gestor de colecciones que unifica los datos locales y los de la nube
        self._colecciones = GestorColecciones(
            gestor_local=self._gestor_local,
            gestor_nube=self._gestor_nube
        )

    def _pausar(self) -> None:
        """Espera a que el usuario presione Enter antes de limpiar o volver al menú."""
        try:
            input("\nPresiona [ENTER] para volver al menú...")
        except (KeyboardInterrupt, EOFError):
            # Si el usuario presiona Ctrl+C o Ctrl+D, evita que el programa falle
            print()

    def _seleccionar_dificultad(self) -> Tuple[str, int, float]:
        """Permite elegir el nivel de dificultad retornando una tupla `(nombre, intentos, multiplicador)`."""
        print("\n--- SELECCIONA EL NIVEL DE DIFICULTAD ---")
        # Desempaquetamos cada tupla de NIVELES_DIFICULTAD en sus 4 variables: codigo, nombre, intentos, mult
        for codigo, nombre, intentos, mult in NIVELES_DIFICULTAD:
            print(f"  [{codigo}] {nombre} (Multiplicador puntaje: x{mult})")

        # Si el usuario presiona Enter vacío, usa por defecto la opción "2" (Normal)
        opcion = input("Elige una opción (por defecto 2 - Normal): ").strip() or "2"
        for codigo, nombre, intentos, mult in NIVELES_DIFICULTAD:
            if opcion == codigo:
                return (nombre, intentos, mult)

        # Si escribió algo distinto de 1, 2 o 3, asigna dificultad Normal por defecto
        InterfazConsola.mostrar_mensaje_info("Opción no reconocida. Se aplicará dificultad Normal (6 intentos).")
        return (NIVELES_DIFICULTAD[1][1], NIVELES_DIFICULTAD[1][2], NIVELES_DIFICULTAD[1][3])

    # =========================================================================
    # OPCIÓN 1: JUGAR PARTIDA DE WORDLE
    # =========================================================================
    def iniciar_flujo_juego(self) -> None:
        """Configura el jugador, la dificultad y ejecuta el bucle interactivo de una partida de Wordle."""
        try:
            # Pide el alias del jugador por teclado
            alias_input = input("\nIngresa tu alias de jugador (o deja vacío para 'Invitado'): ").strip()
            if not alias_input:
                # Si no escribió alias, crea un objeto JugadorInvitado (subclase polimórfica)
                participante = self._colecciones.obtener_o_crear_participante("Invitado", como_invitado=True)
            else:
                # Si escribió alias, busca o registra un JugadorRegistrado
                participante = self._colecciones.obtener_o_crear_participante(alias_input, como_invitado=False)
                # Verifica si el jugador está activo antes de permitirle jugar
                if not participante.activo:
                    InterfazConsola.mostrar_mensaje_error(
                        f"El perfil '{participante.alias}' está marcado como Inactivo. Actívalo en Gestión de Jugadores."
                    )
                    self._pausar()
                    return
        except ErrorValidacionWordle as err:
            # Captura errores si el alias tiene menos de 2 letras o más de 20
            InterfazConsola.mostrar_mensaje_error(str(err))
            self._pausar()
            return

        # Solicita el nivel de dificultad (Fácil, Normal o Experto)
        nombre_dif, max_intentos, mult_dif = self._seleccionar_dificultad()

        # Crea una nueva instancia del motor de juego sorteando una palabra secreta del catálogo
        motor = MotorWordle(
            catalogo_palabras=self._colecciones.catalogo_palabras,
            max_intentos=max_intentos,
            multiplicador_dificultad=mult_dif,
            nombre_dificultad=nombre_dif
        )

        longitud_palabra = CONFIG_JUEGO[0]
        ultimo_error: str = ""

        # Bucle principal de la partida: se repite turno a turno mientras no haya ganado ni agotado intentos
        while not motor.juego_terminado:
            # Dibuja el tablero actualizado y el teclado con colores ANSI
            InterfazConsola.renderizar_tablero(
                historial=motor.historial,
                estado_teclado=motor.estado_teclado,
                modo_online=self._gestor_nube.esta_conectado,
                max_intentos=motor.max_intentos,
                dificultad=motor.nombre_dificultad
            )

            # Si en el turno anterior escribió una palabra inválida, muestra el mensaje de error debajo del tablero
            if ultimo_error:
                InterfazConsola.mostrar_mensaje_error(ultimo_error)
                ultimo_error = ""

            turno_actual = motor.intentos_realizados + 1
            prompt = (
                f"[{participante.alias} - {participante.obtener_tipo()}] "
                f"Intento ({turno_actual}/{motor.max_intentos}) - Palabra de {longitud_palabra} letras (o 'SALIR'): "
            )

            # Lee el intento del usuario
            intento_usuario = input(prompt).strip()
            # Permite cancelar la partida escribiendo la palabra SALIR
            if intento_usuario.upper() == "SALIR":
                InterfazConsola.mostrar_mensaje_info("Partida abortada por el jugador.")
                self._pausar()
                return

            # Valida si la entrada tiene 5 letras y solo caracteres alfabéticos
            es_valido, resultado_validacion = motor.validar_intento(intento_usuario)
            if not es_valido:
                # Si no es válido, guarda el motivo del error y repite el ciclo sin descontar intentos
                ultimo_error = resultado_validacion
                continue

            # Si es válido, evalúa las letras con el algoritmo de dos pasadas (Verde, Amarillo, Gris)
            motor.registrar_intento(resultado_validacion)

        # Renderizado final del tablero cuando la partida termina
        InterfazConsola.renderizar_tablero(
            historial=motor.historial,
            estado_teclado=motor.estado_teclado,
            modo_online=self._gestor_nube.esta_conectado,
            max_intentos=motor.max_intentos,
            dificultad=motor.nombre_dificultad
        )

        # Calcula el puntaje base y registra la partida tanto en JSON local como en Google Sheets
        puntaje_base = motor.calcular_puntaje_base()
        registro, subido_nube = self._colecciones.registrar_partida_completada(
            participante=participante,
            palabra_secreta=motor.palabra_secreta,
            gano=motor.victoria,
            intentos_usados=motor.intentos_realizados,
            max_intentos=motor.max_intentos,
            dificultad=motor.nombre_dificultad,
            puntaje_base=puntaje_base,
            palabras_intentadas=motor.palabras_intentadas
        )

        # Muestra felicitación si ganó o revela cuál era la palabra secreta si perdió
        InterfazConsola.mostrar_resultado_final(
            gano=motor.victoria,
            palabra_secreta=motor.palabra_secreta,
            intentos=motor.intentos_realizados,
            puntaje=registro.puntaje
        )

        InterfazConsola.mostrar_mensaje_exito(
            f"Partida {registro.id_partida} guardada en JSON local (`datos/partidas_y_jugadores.json`)."
        )
        if subido_nube:
            InterfazConsola.mostrar_mensaje_exito("Puntaje sincronizado en Google Sheets mediante `append_row()`.")
        self._pausar()

    # =========================================================================
    # OPCIÓN 2: GESTIÓN DE JUGADORES (CRUD Y CAMBIO DE ESTADO)
    # =========================================================================
    def menu_gestion_jugadores(self) -> None:
        """Submenú administrativo para registrar, consultar, actualizar y activar/desactivar jugadores."""
        while True:
            print("\n--- GESTIÓN DE JUGADORES ---")
            print("  [1] Registrar nuevo jugador")
            print("  [2] Consultar todos los jugadores registrados")
            print("  [3] Actualizar alias o categoría de un jugador (Estándar / VIP / Pro)")
            print("  [4] Activar / Desactivar estado de un jugador")
            print("  [0] Volver al menú principal")

            sub = input("Selecciona una opción: ").strip()
            if sub == "0":
                break
            elif sub == "1":
                try:
                    alias = input("Alias del nuevo jugador (2-20 caracteres): ")
                    categoria = input("Categoría (Estándar / VIP / Pro) [Enter = Estándar]: ").strip() or "Estándar"
                    nuevo = self._colecciones.registrar_jugador(alias, categoria)
                    InterfazConsola.mostrar_mensaje_exito(f"Jugador registrado correctamente: {nuevo}")
                except ErrorValidacionWordle as err:
                    InterfazConsola.mostrar_mensaje_error(str(err))
            elif sub == "2":
                # Descarga primero cambios recientes de la nube y muestra la tabla ordenada
                jugadores = self._colecciones.listar_jugadores(solo_activos=False, refrescar_nube=True)
                InterfazConsola.mostrar_tabla_jugadores(jugadores)
            elif sub == "3":
                try:
                    alias = input("Alias actual del jugador a modificar: ")
                    nuevo_alias = input("Nuevo alias (deja vacío para conservar el actual): ")
                    cat = input("Nueva categoría (Estándar / VIP / Pro, vacío para conservar): ")
                    actualizado = self._colecciones.actualizar_jugador(
                        alias_actual=alias,
                        nuevo_alias=nuevo_alias if nuevo_alias.strip() else None,
                        nueva_categoria=cat if cat.strip() else None
                    )
                    InterfazConsola.mostrar_mensaje_exito(f"Datos actualizados y sincronizados en Google Sheets: {actualizado}")
                except ErrorValidacionWordle as err:
                    InterfazConsola.mostrar_mensaje_error(str(err))
            elif sub == "4":
                try:
                    alias = input("Alias del jugador a activar/desactivar: ")
                    jugador = self._colecciones.buscar_jugador(alias)
                    if not jugador:
                        raise ErrorValidacionWordle(f"No existe el jugador '{alias}'.")
                    # Invierte el booleano activo con el operador lógico 'not'
                    nuevo_estado = not jugador.activo
                    self._colecciones.actualizar_jugador(alias, nuevo_estado_activo=nuevo_estado)
                    estado_txt = "ACTIVO" if nuevo_estado else "INACTIVO"
                    InterfazConsola.mostrar_mensaje_exito(f"El estado de '{jugador.alias}' cambió a {estado_txt} (Sincronizado en la nube).")
                except ErrorValidacionWordle as err:
                    InterfazConsola.mostrar_mensaje_error(str(err))
            else:
                InterfazConsola.mostrar_mensaje_error("Opción inválida.")

    # =========================================================================
    # OPCIÓN 3: GESTIÓN DEL CATÁLOGO DE PALABRAS (SETS)
    # =========================================================================
    def menu_gestion_palabras(self) -> None:
        """Submenú para consultar, buscar por subcadena, agregar o eliminar palabras del conjunto."""
        while True:
            catalogo = sorted(list(self._colecciones.catalogo_palabras))
            print(f"\n--- GESTIÓN DEL CATÁLOGO DE PALABRAS ({len(catalogo)} palabras activas) ---")
            print("  [1] Ver todas las palabras del catálogo")
            print("  [2] Buscar palabras por letra o subcadena")
            print("  [3] Agregar nueva palabra de 5 letras")
            print("  [4] Eliminar palabra del catálogo")
            print("  [0] Volver al menú principal")

            sub = input("Selecciona una opción: ").strip()
            if sub == "0":
                break
            elif sub == "1":
                print("\nCatálogo actual:", ", ".join(catalogo))
            elif sub == "2":
                criterio = input("Ingresa la letra o prefijo a buscar: ").strip()
                coincidencias = self._colecciones.buscar_palabras_por_prefijo_o_letra(criterio)
                print(f"Coincidencias ({len(coincidencias)}): {', '.join(coincidencias) if coincidencias else 'Ninguna'}")
            elif sub == "3":
                try:
                    nueva = input("Escribe la nueva palabra de 5 letras: ")
                    agregada = self._colecciones.agregar_palabra_catalogo(nueva)
                    InterfazConsola.mostrar_mensaje_exito(f"Palabra '{agregada}' añadida en JSON y Google Sheets.")
                except ErrorValidacionWordle as err:
                    InterfazConsola.mostrar_mensaje_error(str(err))
            elif sub == "4":
                try:
                    borrar = input("Escribe la palabra de 5 letras que deseas eliminar: ")
                    eliminada = self._colecciones.eliminar_palabra_catalogo(borrar)
                    InterfazConsola.mostrar_mensaje_exito(f"Palabra '{eliminada}' eliminada del catálogo.")
                except ErrorValidacionWordle as err:
                    InterfazConsola.mostrar_mensaje_error(str(err))
            else:
                InterfazConsola.mostrar_mensaje_error("Opción inválida.")

    # =========================================================================
    # OPCIÓN 4: BÚSQUEDAS Y FILTROS DE PARTIDAS
    # =========================================================================
    def menu_busquedas_partidas(self) -> None:
        """Permite consultar el historial global de partidas aplicando hasta 4 filtros combinados."""
        print("\n--- BÚSQUEDA Y FILTRADO DE PARTIDAS GLOBALES ---")
        alias = input("Filtrar por alias de jugador (Enter = Todos): ").strip() or None
        est_input = input("Filtrar por resultado ([V]ictorias / [D]errotas / Enter = Todos): ").strip().upper()
        solo_victorias = True if est_input == "V" else (False if est_input == "D" else None)
        dificultad = input("Filtrar por dificultad (Fácil / Normal / Experto / Enter = Todas): ").strip() or None
        palabra = input("Filtrar por palabra secreta exacta (Enter = Todas): ").strip() or None

        filtradas = self._colecciones.filtrar_partidas(
            alias_jugador=alias,
            solo_victorias=solo_victorias,
            dificultad=dificultad,
            palabra_secreta=palabra,
            refrescar_nube=True
        )
        InterfazConsola.mostrar_tabla_partidas(filtradas)
        self._pausar()

    # =========================================================================
    # OPCIÓN 5: REPORTES ESTADÍSTICOS Y RANKING COMPETITIVO ONLINE
    # =========================================================================
    def mostrar_reportes_y_ranking(self) -> None:
        """Descarga los últimos datos de Google Sheets y muestra el resumen estadístico y el ranking global."""
        partidas = self._colecciones.filtrar_partidas(refrescar_nube=True)
        jugadores = self._colecciones.listar_jugadores(solo_activos=False, refrescar_nube=False)
        reporte = GeneradorReportes.generar_resumen_estadistico(
            partidas=partidas,
            jugadores=jugadores,
            total_palabras=len(self._colecciones.catalogo_palabras)
        )
        InterfazConsola.mostrar_reporte_estadistico(reporte)
        print("\n--- TABLA DE POSICIONES COMPETITIVA GLOBAL (SINCRONIZADA CON GOOGLE SHEETS) ---")
        InterfazConsola.mostrar_tabla_jugadores(jugadores)
        self._pausar()

    # =========================================================================
    # OPCIÓN 6: EXPORTACIÓN A CSV
    # =========================================================================
    def exportar_archivos_csv(self) -> None:
        """Exporta tanto el historial de partidas como el ranking de jugadores a archivos CSV en `exportaciones/`."""
        try:
            partidas_dict = [p.a_diccionario() for p in self._colecciones.filtrar_partidas()]
            jugadores_dict = [j.a_diccionario() for j in self._colecciones.listar_jugadores()]

            ruta_partidas = self._gestor_local.exportar_partidas_csv(partidas_dict)
            ruta_ranking = self._gestor_local.exportar_ranking_csv(jugadores_dict)

            InterfazConsola.mostrar_mensaje_exito(f"Historial de partidas exportado en: {ruta_partidas}")
            InterfazConsola.mostrar_mensaje_exito(f"Ranking de jugadores exportado en : {ruta_ranking}")
        except OSError as err:
            InterfazConsola.mostrar_mensaje_error(str(err))
        self._pausar()

    # =========================================================================
    # CICLO PRINCIPAL DE LA APLICACIÓN
    # =========================================================================
    def ejecutar(self) -> None:
        """Ciclo principal del menú interactivo con manejo robusto de excepciones."""
        while True:
            try:
                # Muestra el menú principal actualizado en cada iteración
                InterfazConsola.mostrar_menu_principal(
                    modo_online=self._gestor_nube.esta_conectado,
                    total_jugadores=self._colecciones.total_jugadores,
                    total_palabras=len(self._colecciones.catalogo_palabras)
                )
                entrada_opcion = input("Selecciona una opción [0-7]: ").strip()
                # Valida que la opción ingresada sea un número entero entre 0 y 7
                opcion = ValidadorDatos.validar_entero_rango(entrada_opcion, 0, 7, "Opción de menú")

                # Despacha la acción correspondiente según el número elegido
                if opcion == 0:
                    self._colecciones.guardar_cambios()
                    InterfazConsola.mostrar_mensaje_exito("Datos guardados en JSON. ¡Hasta pronto!")
                    break
                elif opcion == 1:
                    self.iniciar_flujo_juego()
                elif opcion == 2:
                    self.menu_gestion_jugadores()
                elif opcion == 3:
                    self.menu_gestion_palabras()
                elif opcion == 4:
                    self.menu_busquedas_partidas()
                elif opcion == 5:
                    self.mostrar_reportes_y_ranking()
                elif opcion == 6:
                    self.exportar_archivos_csv()
                elif opcion == 7:
                    ejecutar_suite_pruebas()
                    self._pausar()

            except ErrorValidacionWordle as err_val:
                # Si el usuario escribió una opción fuera de rango o no numérica, muestra el error en rojo
                InterfazConsola.mostrar_mensaje_error(str(err_val))
            except (KeyboardInterrupt, EOFError):
                # Si presiona Ctrl+C para salir rápido, guarda los datos antes de cerrar
                print("\n\n[!] Interrupción detectada. Guardando estado antes de salir...")
                self._colecciones.guardar_cambios()
                break
            except Exception as err_inesperado:
                InterfazConsola.mostrar_mensaje_error(f"Error controlado en el menú: {err_inesperado}")


# Condición estándar de Python: solo ejecuta el programa si este archivo fue invocado directamente (`python main.py`)
if __name__ == "__main__":
    app = AplicacionWordle()
    app.ejecutar()
