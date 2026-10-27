"""
Módulo de Pruebas Automatizadas e Integridad de Datos (Lab 04).
Verifica:
- Herencia, sobrescritura y polimorfismo en los modelos (`JugadorRegistrado` vs `JugadorInvitado`).
- Algoritmo de evaluación de letras repetidas en `MotorWordle`.
- Validaciones y lanzamiento de excepciones (`raise ErrorValidacionWordle`).
- Generación de reportes y métricas estadísticas.
"""

# Importamos el framework 'unittest' incluido en la librería estándar de Python
import unittest
# Importamos las clases del modelo de dominio para probar herencia y polimorfismo
from modelos import Participante, JugadorRegistrado, JugadorInvitado, RegistroPartida
# Importamos el validador y la excepción personalizada para probar el manejo de errores
from validaciones import ValidadorDatos, ErrorValidacionWordle
# Importamos el motor del juego para comprobar el algoritmo de dos pasadas
from logica_juego import MotorWordle
# Importamos el generador de reportes para verificar los cálculos matemáticos
from gestion_datos import GeneradorReportes


class PruebasIntegridadWordle(unittest.TestCase):
    """Suite de pruebas unitarias y de integración del proyecto que hereda de `unittest.TestCase`."""

    def test_01_herencia_y_polimorfismo_jugadores(self) -> None:
        """Comprueba herencia, sobrescritura de `calcular_bonificacion` y polimorfismo."""
        # Instanciamos un objeto de cada subclase
        registrado = JugadorRegistrado(alias="Andres", categoria="VIP")
        invitado = JugadorInvitado(alias="Visitante")

        # Verificamos con assertIsInstance que ambas subclases heredan de la superclase Participante
        self.assertIsInstance(registrado, Participante)
        self.assertIsInstance(invitado, Participante)

        # Tratamiento polimórfico: ante un mismo puntaje base (500), cada clase calcula distinto resultado
        puntos_reg = registrado.registrar_resultado_partida(gano=True, puntos_obtenidos=500)
        puntos_inv = invitado.calcular_bonificacion(500)

        # El jugador registrado VIP debe recibir más de 500 puntos (500 + 25 de racha * 1.2 = 630)
        self.assertGreater(puntos_reg, 500)
        # El jugador invitado recibe exactamente el 90% de 500 (450 puntos)
        self.assertEqual(puntos_inv, 450)

    def test_02_validaciones_y_excepciones(self) -> None:
        """Verifica que `ValidadorDatos` lance `ErrorValidacionWordle` ante entradas inválidas."""
        # Verifica que una palabra con números lance ErrorValidacionWordle
        with self.assertRaises(ErrorValidacionWordle):
            ValidadorDatos.validar_palabra_catalogo("12345")

        # Verifica que una palabra de 4 letras (en vez de 5) lance ErrorValidacionWordle
        with self.assertRaises(ErrorValidacionWordle):
            ValidadorDatos.validar_palabra_catalogo("HOLA")

        # Verifica que un número fuera del rango [1, 5] lance ErrorValidacionWordle
        with self.assertRaises(ErrorValidacionWordle):
            ValidadorDatos.validar_entero_rango("99", minimo=1, maximo=5)

        # Verifica que una palabra con espacios y tildes se normalice correctamente a "ARBOL"
        palabra_ok = ValidadorDatos.validar_palabra_catalogo("  árból ")
        self.assertEqual(palabra_ok, "ARBOL")

    def test_03_motor_wordle_algoritmo_dos_pasadas(self) -> None:
        """Verifica la evaluación exacta de letras repetidas y detección de victoria."""
        # Inicializamos el motor y forzamos la palabra secreta a "MOTOR" para la prueba
        motor = MotorWordle(catalogo_palabras={"ARBOL", "LIBRO", "MOTOR"})
        motor._palabra_secreta = "MOTOR"

        # Probamos con "LIBRO": la 'L', 'I', 'B' no están (GRIS), mientras que 'R' y 'O' están en otra posición (AMARILLO)
        res = motor.registrar_intento("LIBRO")
        self.assertEqual(res[0], ("L", "GRIS"))
        self.assertEqual(res[3], ("R", "AMARILLO"))
        self.assertEqual(res[4], ("O", "AMARILLO"))

        # Probamos adivinando "MOTOR": debe marcar victoria y juego terminado en True
        res_ganador = motor.registrar_intento("MOTOR")
        self.assertTrue(motor.victoria)
        self.assertTrue(motor.juego_terminado)
        self.assertEqual(len(res_ganador), 5)

    def test_04_generacion_reportes(self) -> None:
        """Comprueba el cálculo de métricas y agrupaciones en `GeneradorReportes`."""
        # Creamos 2 partidas de prueba (1 victoria en 2 intentos y 1 derrota)
        partidas = [
            RegistroPartida("P-1", "Andres", "Registrado", "ARBOL", True, 2, 6, "Normal", 500, ["CAMPO", "ARBOL"]),
            RegistroPartida("P-2", "Andres", "Registrado", "DATOS", False, 6, 6, "Experto", 0, ["CAMPO"] * 6),
        ]
        jugadores = [JugadorRegistrado(alias="Andres", partidas_jugadas=2, partidas_ganadas=1, puntaje_acumulado=500)]
        reporte = GeneradorReportes.generar_resumen_estadistico(partidas, jugadores, total_palabras=300)

        # Comprobamos que el total sea 2, victorias sea 1, tasa de éxito sea 50.0% y promedio de intentos sea 2.0
        self.assertEqual(reporte["total_partidas"], 2)
        self.assertEqual(reporte["total_victorias"], 1)
        self.assertEqual(reporte["tasa_exito_global"], 50.0)
        self.assertEqual(reporte["promedio_intentos_victoria"], 2.0)


def ejecutar_suite_pruebas() -> bool:
    """Carga y ejecuta todas las pruebas unitarias mostrando el detalle en consola."""
    print("\n================ EJECUTANDO PRUEBAS DE INTEGRIDAD ================")
    cargador = unittest.TestLoader()
    suite = cargador.loadTestsFromTestCase(PruebasIntegridadWordle)
    corredor = unittest.TextTestRunner(verbosity=2)
    resultado = corredor.run(suite)
    return resultado.wasSuccessful()


if __name__ == "__main__":
    ejecutar_suite_pruebas()
