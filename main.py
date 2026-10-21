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

import sys
from typing import Tuple

from config import (
    RUTA_CREDENCIALES_DEFAULT,
    NOMBRE_DOCUMENTO_SHEETS,
    CONFIG_JUEGO,
    NIVELES_DIFICULTAD
)
from validaciones import ValidadorDatos, ErrorValidacionWordle
from persistencia import GestorArchivosLocales, GestorGoogleSheets
from gestion_datos import GestorColecciones, GeneradorReportes
from logica_juego import MotorWordle
from interfaz_cli import InterfazConsola
from tests_wordle import ejecutar_suite_pruebas


class AplicacionWordle:
    """
    Controlador principal que coordina la interacción con el usuario,
    las colecciones de dominio, el motor del juego y la persistencia híbrida.
    """

    def __init__(self) -> None:
        print("Inicializando Sistema Wordle CLI... Cargando persistencia JSON y Google Sheets...")
        self._gestor_local = GestorArchivosLocales()
        self._gestor_nube = GestorGoogleSheets(
            ruta_credenciales=RUTA_CREDENCIALES_DEFAULT,
            nombre_documento=NOMBRE_DOCUMENTO_SHEETS
        )
        self._colecciones = GestorColecciones(
            gestor_local=self._gestor_local,
            gestor_nube=self._gestor_nube
        )

    def _pausar(self) -> None:
        """Espera a que el usuario presione Enter para continuar."""
        try:
            input("\nPresiona [ENTER] para volver al menú...")
        except (KeyboardInterrupt, EOFError):
            print()

    def _seleccionar_dificultad(self) -> Tuple[str, int, float]:
        """Permite elegir el nivel de dificultad retornando una tupla (nombre, intentos, multiplicador)."""
        print("\n--- SELECCIONA EL NIVEL DE DIFICULTAD ---")
        for codigo, nombre, intentos, mult in NIVELES_DIFICULTAD:
            print(f"  [{codigo}] {nombre} (Multiplicador puntaje: x{mult})")

        opcion = input("Elige una opción (por defecto 2 - Normal): ").strip() or "2"
        for codigo, nombre, intentos, mult in NIVELES_DIFICULTAD:
            if opcion == codigo:
                return (nombre, intentos, mult)

        InterfazConsola.mostrar_mensaje_info("Opción no reconocida. Se aplicará dificultad Normal (6 intentos).")
        return (NIVELES_DIFICULTAD[1][1], NIVELES_DIFICULTAD[1][2], NIVELES_DIFICULTAD[1][3])

    # =========================================================================
    # OPCIÓN 1: JUGAR PARTIDA DE WORDLE
    # =========================================================================
    def iniciar_flujo_juego(self) -> None:
        """Configura el jugador, la dificultad y ejecuta el bucle interactivo de Wordle."""
        try:
            alias_input = input("\nIngresa tu alias de jugador (o deja vacío para 'Invitado'): ").strip()
            if not alias_input:
                participante = self._colecciones.obtener_o_crear_participante("Invitado", como_invitado=True)
            else:
                participante = self._colecciones.obtener_o_crear_participante(alias_input, como_invitado=False)
                if not participante.activo:
                    InterfazConsola.mostrar_mensaje_error(
                        f"El perfil '{participante.alias}' está marcado como Inactivo. Actívalo en Gestión de Jugadores."
                    )
                    self._pausar()
                    return
        except ErrorValidacionWordle as err:
            InterfazConsola.mostrar_mensaje_error(str(err))
            self._pausar()
            return

        nombre_dif, max_intentos, mult_dif = self._seleccionar_dificultad()

        motor = MotorWordle(
            catalogo_palabras=self._colecciones.catalogo_palabras,
            max_intentos=max_intentos,
            multiplicador_dificultad=mult_dif,
            nombre_dificultad=nombre_dif
        )

        longitud_palabra = CONFIG_JUEGO[0]
        ultimo_error: str = ""

        while not motor.juego_terminado:
            InterfazConsola.renderizar_tablero(
                historial=motor.historial,
                estado_teclado=motor.estado_teclado,
                modo_online=self._gestor_nube.esta_conectado,
                max_intentos=motor.max_intentos,
                dificultad=motor.nombre_dificultad
            )

            if ultimo_error:
                InterfazConsola.mostrar_mensaje_error(ultimo_error)
                ultimo_error = ""

            turno_actual = motor.intentos_realizados + 1
            prompt = (
                f"[{participante.alias} - {participante.obtener_tipo()}] "
                f"Intento ({turno_actual}/{motor.max_intentos}) - Palabra de {longitud_palabra} letras (o 'SALIR'): "
            )

            intento_usuario = input(prompt).strip()
            if intento_usuario.upper() == "SALIR":
                InterfazConsola.mostrar_mensaje_info("Partida abortada por el jugador.")
                self._pausar()
                return

            es_valido, resultado_validacion = motor.validar_intento(intento_usuario)
            if not es_valido:
                ultimo_error = resultado_validacion
                continue

            motor.registrar_intento(resultado_validacion)

        # Renderizado final del tablero al terminar la partida
        InterfazConsola.renderizar_tablero(
            historial=motor.historial,
            estado_teclado=motor.estado_teclado,
            modo_online=self._gestor_nube.esta_conectado,
            max_intentos=motor.max_intentos,
            dificultad=motor.nombre_dificultad
        )

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
        """Submenú para registrar, consultar y actualizar jugadores (sin pedir correo)."""
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
        """Submenú para consultar, buscar, agregar o eliminar palabras del conjunto."""
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
        """Permite consultar el historial global aplicando filtros combinados."""
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
        """Descarga los últimos datos de Google Sheets y muestra el ranking competitivo global."""
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
        """Exporta tanto el historial de partidas como el ranking de jugadores a archivos CSV."""
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
        """Ciclo principal del menú interactivo con manejo robusto de errores."""
        while True:
            try:
                InterfazConsola.mostrar_menu_principal(
                    modo_online=self._gestor_nube.esta_conectado,
                    total_jugadores=self._colecciones.total_jugadores,
                    total_palabras=len(self._colecciones.catalogo_palabras)
                )
                entrada_opcion = input("Selecciona una opción [0-7]: ").strip()
                opcion = ValidadorDatos.validar_entero_rango(entrada_opcion, 0, 7, "Opción de menú")

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
                InterfazConsola.mostrar_mensaje_error(str(err_val))
            except (KeyboardInterrupt, EOFError):
                print("\n\n[!] Interrupción detectada. Guardando estado antes de salir...")
                self._colecciones.guardar_cambios()
                break
            except Exception as err_inesperado:
                InterfazConsola.mostrar_mensaje_error(f"Error controlado en el menú: {err_inesperado}")


if __name__ == "__main__":
    app = AplicacionWordle()
    app.ejecutar()
