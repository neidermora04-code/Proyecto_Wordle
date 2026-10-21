"""
Módulo de Interacción con el Usuario en Consola (CLI) para entornos Linux.
Presenta el menú interactivo principal, el renderizado ANSI del tablero de Wordle,
tablas de consulta y paneles de reportes estadísticos.
"""

from typing import List, Tuple, Dict, Any
from config import CONFIG_JUEGO
from logica_juego import MotorWordle
from modelos import JugadorRegistrado, RegistroPartida


class InterfazConsola:
    """
    Clase encargada de toda la presentación visual en la terminal Linux
    utilizando códigos de escape ANSI estándar y cadenas formateadas (f-strings).
    """

    CODIGOS_ANSI: Dict[str, str] = {
        "RESET": "\033[0m",
        "NEGRITA": "\033[1m",
        MotorWordle.ESTADO_CORRECTO: "\033[1;97;42m",   # Fondo Verde
        MotorWordle.ESTADO_PRESENTE: "\033[1;97;43m",   # Fondo Amarillo
        MotorWordle.ESTADO_AUSENTE: "\033[1;97;100m",   # Fondo Gris Oscuro
        "SIN_USAR": "\033[0;37;40m",
        "TEXTO_VERDE": "\033[1;32m",
        "TEXTO_AMARILLO": "\033[1;33m",
        "TEXTO_ROJO": "\033[1;31m",
        "TEXTO_CIAN": "\033[1;36m",
        "TEXTO_MAGENTA": "\033[1;35m",
    }

    FILAS_TECLADO: Tuple[str, str, str] = (
        "QWERTYUIOP",
        "ASDFGHJKLÑ",
        "ZXCVBNM"
    )

    @staticmethod
    def limpiar_pantalla() -> None:
        """Limpia la terminal de forma nativa con secuencia ANSI."""
        print("\033[H\033[2J", end="", flush=True)

    @classmethod
    def mostrar_menu_principal(cls, modo_online: bool, total_jugadores: int, total_palabras: int) -> None:
        """Presenta el menú interactivo principal del sistema."""
        cian = cls.CODIGOS_ANSI["TEXTO_CIAN"]
        negrita = cls.CODIGOS_ANSI["NEGRITA"]
        verde = cls.CODIGOS_ANSI["TEXTO_VERDE"]
        amarillo = cls.CODIGOS_ANSI["TEXTO_AMARILLO"]
        reset = cls.CODIGOS_ANSI["RESET"]

        estado_nube = (
            f"{verde}● CONECTADO (Google Sheets + JSON Local){reset}"
            if modo_online
            else f"{amarillo}○ MODO LOCAL (Persistencia JSON/CSV Activa){reset}"
        )

        print(f"\n{cian}=================================================================={reset}")
        print(f"   {negrita}SISTEMA GESTOR Y JUEGO WORDLE CLI — PROYECTO INTEGRADOR{reset}")
        print(f"   Persistencia: {estado_nube}")
        print(f"   Jugadores registrados: {total_jugadores} | Palabras en catálogo: {total_palabras}")
        print(f"{cian}=================================================================={reset}")
        print(f"  {negrita}[1]{reset} Jugar una partida de Wordle (Seleccionar Dificultad)")
        print(f"  {negrita}[2]{reset} Gestión de Jugadores (Registrar, Consultar, Actualizar, Estado)")
        print(f"  {negrita}[3]{reset} Gestión del Catálogo de Palabras (Consultar, Agregar, Eliminar)")
        print(f"  {negrita}[4]{reset} Búsquedas y Filtros de Partidas Jugadas")
        print(f"  {negrita}[5]{reset} Reportes Estadísticos y Ranking General")
        print(f"  {negrita}[6]{reset} Exportar Datos a CSV (Partidas y Ranking)")
        print(f"  {negrita}[7]{reset} Ejecutar Suite de Pruebas de Integridad (Autotest)")
        print(f"  {negrita}[0]{reset} Guardar y Salir del Sistema")
        print(f"{cian}------------------------------------------------------------------{reset}")

    @classmethod
    def colorear_celda(cls, letra: str, estado: str, es_tablero: bool = False) -> str:
        """
        Formatea una letra individual con su fondo de color ANSI y marcadores visuales:
        [A] = Verde (Exacta), (A) = Amarillo (Presente), ·A· = Gris (Ausente).
        """
        color = cls.CODIGOS_ANSI.get(estado, cls.CODIGOS_ANSI["RESET"])
        reset = cls.CODIGOS_ANSI["RESET"]
        if not es_tablero:
            return f"{color} {letra} {reset}"

        if estado == MotorWordle.ESTADO_CORRECTO:
            return f"{color}[{letra}]{reset}"
        elif estado == MotorWordle.ESTADO_PRESENTE:
            return f"{color}({letra}){reset}"
        else:
            return f"{color}·{letra}·{reset}"

    @classmethod
    def renderizar_tablero(
        cls,
        historial: List[List[Tuple[str, str]]],
        estado_teclado: Dict[str, str],
        modo_online: bool,
        max_intentos: int = CONFIG_JUEGO[1],
        dificultad: str = "Normal"
    ) -> None:
        """Dibuja en la terminal la cuadrícula de intentos y el teclado virtual."""
        cls.limpiar_pantalla()
        longitud_palabra = CONFIG_JUEGO[0]

        estado_red = (
            f"{cls.CODIGOS_ANSI['TEXTO_VERDE']}● Google Sheets + JSON{cls.CODIGOS_ANSI['RESET']}"
            if modo_online
            else f"{cls.CODIGOS_ANSI['TEXTO_AMARILLO']}○ JSON Local (Offline){cls.CODIGOS_ANSI['RESET']}"
        )

        print(f"{cls.CODIGOS_ANSI['TEXTO_CIAN']}================================================={cls.CODIGOS_ANSI['RESET']}")
        print(f"          {cls.CODIGOS_ANSI['NEGRITA']}W O R D L E   C L I   (Linux){cls.CODIGOS_ANSI['RESET']}")
        print(f"  BD: {estado_red} | Dificultad: {dificultad}")
        print(f"  Leyenda: {cls.colorear_celda('V', MotorWordle.ESTADO_CORRECTO, True)} Exacta  "
              f"{cls.colorear_celda('A', MotorWordle.ESTADO_PRESENTE, True)} Otra pos.  "
              f"{cls.colorear_celda('G', MotorWordle.ESTADO_AUSENTE, True)} No está")
        print(f"{cls.CODIGOS_ANSI['TEXTO_CIAN']}================================================={cls.CODIGOS_ANSI['RESET']}\n")

        for intento in historial:
            fila_renderizada = " ".join(cls.colorear_celda(letra, estado, True) for letra, estado in intento)
            print(f"              {fila_renderizada}")

        filas_restantes = max_intentos - len(historial)
        for _ in range(filas_restantes):
            celdas_vacias = " ".join("[ ]" for _ in range(longitud_palabra))
            print(f"              {celdas_vacias}")

        print("\n-------------------------------------------------")
        print("               TECLADO DE CONTROL")
        for indice, fila_letras in enumerate(cls.FILAS_TECLADO):
            sangria = "  " * (indice + 2)
            teclas = " ".join(
                cls.colorear_celda(letra, estado_teclado.get(letra, "SIN_USAR"))
                for letra in fila_letras
            )
            print(f"{sangria}{teclas}")
        print("-------------------------------------------------\n")

    @classmethod
    def mostrar_tabla_jugadores(cls, jugadores: List[JugadorRegistrado]) -> None:
        """Imprime una tabla formateada con el listado o ranking de jugadores."""
        if not jugadores:
            cls.mostrar_mensaje_info("No hay jugadores registrados que coincidan con la consulta.")
            return

        print("\n" + "=" * 95)
        print(f"{'#':<4} {'ALIAS':<15} {'CATEGORÍA':<12} {'ESTADO':<10} {'PJ':<5} {'PG':<5} {'% VICT':<9} {'RACHA':<7} {'PUNTAJE':<10}")
        print("-" * 95)
        for idx, j in enumerate(jugadores, start=1):
            estado = "Activo" if j.activo else "Inactivo"
            print(
                f"{idx:<4} {j.alias:<15} {j.categoria:<12} {estado:<10} "
                f"{j.partidas_jugadas:<5} {j.partidas_ganadas:<5} "
                f"{j.porcentaje_victorias:<8}% {j.racha_actual:<7} {j.puntaje_acumulado:<10}"
            )
        print("=" * 95)

    @classmethod
    def mostrar_tabla_partidas(cls, partidas: List[RegistroPartida]) -> None:
        """Imprime el listado de partidas filtradas."""
        if not partidas:
            cls.mostrar_mensaje_info("No se encontraron partidas con los filtros especificados.")
            return

        print("\n" + "=" * 100)
        print(f"{'ID':<10} {'FECHA':<20} {'JUGADOR':<14} {'PALABRA':<9} {'RESULTADO':<10} {'INTENTOS':<10} {'DIFICULTAD':<14} {'PTS':<6}")
        print("-" * 100)
        for p in partidas:
            intentos_str = f"{p.intentos_usados}/{p.max_intentos}"
            print(
                f"{p.id_partida:<10} {p.fecha:<20} {p.jugador:<14} {p.palabra_secreta:<9} "
                f"{p.estado_texto:<10} {intentos_str:<10} {p.dificultad[:13]:<14} {p.puntaje:<6}"
            )
        print("=" * 100)

    @classmethod
    def mostrar_reporte_estadistico(cls, reporte: Dict[str, Any]) -> None:
        """Renderiza el panel de métricas calculadas, agrupadas y el histograma de intentos."""
        cian = cls.CODIGOS_ANSI["TEXTO_CIAN"]
        verde = cls.CODIGOS_ANSI["TEXTO_VERDE"]
        negrita = cls.CODIGOS_ANSI["NEGRITA"]
        reset = cls.CODIGOS_ANSI["RESET"]

        print(f"\n{cian}================ REPORTE ESTADÍSTICO GENERAL ================ {reset}")
        print(f"  • Total de Partidas Jugadas    : {negrita}{reporte['total_partidas']}{reset}")
        print(f"  • Victorias / Derrotas         : {verde}{reporte['total_victorias']} V{reset} / {reporte['total_derrotas']} D")
        print(f"  • Tasa de Éxito Global         : {negrita}{reporte['tasa_exito_global']}%{reset}")
        print(f"  • Promedio Intentos (Victorias): {reporte['promedio_intentos_victoria']} intentos")
        print(f"  • Récord de Puntaje en Partida : {reporte['puntaje_maximo_partida']} pts")
        print(f"  • Palabra Secreta más frecuente: {reporte['palabra_mas_jugada']}")
        print(f"  • Jugadores Registrados        : {reporte['total_jugadores_registrados']}")
        print(f"  • Palabras en Catálogo Activo  : {reporte['total_palabras_catalogo']}")

        print(f"\n{negrita}--- Desglose Agrupado por Nivel de Dificultad ---{reset}")
        agrupado = reporte.get("agrupado_por_dificultad", {})
        if not agrupado:
            print("  (Sin partidas registradas aún)")
        else:
            for dif, metricas in agrupado.items():
                print(
                    f"  [{dif:<22}] -> Jugadas: {metricas['jugadas']:<3} | "
                    f"Victorias: {metricas['victorias']:<3} | Puntos Totales: {metricas['puntos_totales']}"
                )

        print(f"\n{negrita}--- Distribución de Victorias por Número de Intento ---{reset}")
        distribucion: Dict[int, int] = reporte.get("distribucion_intentos", {})
        for num_intento, cantidad in sorted(distribucion.items()):
            barra = "█" * cantidad
            print(f"  Intento {num_intento}: {barra} ({cantidad})")
        print(f"{cian}============================================================={reset}")

    @classmethod
    def mostrar_mensaje_error(cls, mensaje: str) -> None:
        rojo = cls.CODIGOS_ANSI["TEXTO_ROJO"]
        reset = cls.CODIGOS_ANSI["RESET"]
        print(f"{rojo}[!] {mensaje}{reset}")

    @classmethod
    def mostrar_mensaje_exito(cls, mensaje: str) -> None:
        verde = cls.CODIGOS_ANSI["TEXTO_VERDE"]
        reset = cls.CODIGOS_ANSI["RESET"]
        print(f"{verde}[✓] {mensaje}{reset}")

    @classmethod
    def mostrar_mensaje_info(cls, mensaje: str) -> None:
        amarillo = cls.CODIGOS_ANSI["TEXTO_AMARILLO"]
        reset = cls.CODIGOS_ANSI["RESET"]
        print(f"{amarillo}[i] {mensaje}{reset}")

    @classmethod
    def mostrar_resultado_final(cls, gano: bool, palabra_secreta: str, intentos: int, puntaje: int) -> None:
        reset = cls.CODIGOS_ANSI["RESET"]
        if gano:
            verde = cls.CODIGOS_ANSI["TEXTO_VERDE"]
            print(f"{verde}¡FELICIDADES! Has adivinado la palabra '{palabra_secreta}' en {intentos} intento(s).{reset}")
            print(f"{verde}Puntaje total obtenido (con bonificación de jugador/dificultad): {puntaje} pts.{reset}")
        else:
            rojo = cls.CODIGOS_ANSI["TEXTO_ROJO"]
            print(f"{rojo}¡Fin del juego! Se han agotado tus intentos.{reset}")
            print(f"La palabra secreta era: {cls.CODIGOS_ANSI['NEGRITA']}{palabra_secreta}{reset}")
