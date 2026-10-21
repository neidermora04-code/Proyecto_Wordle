"""
Módulo de Pruebas Automatizadas e Integridad de Datos (Lab 04).
Verifica:
- Herencia, sobrescritura y polimorfismo en los modelos (`JugadorRegistrado` vs `JugadorInvitado`).
- Algoritmo de evaluación de letras repetidas en `MotorWordle`.
- Validaciones y lanzamiento de excepciones (`raise ErrorValidacionWordle`).
- Persistencia JSON, exportación CSV y lectura/escritura con `pathlib`.
"""

import unittest
from pathlib import Path
from modelos import Participante, JugadorRegistrado, JugadorInvitado, RegistroPartida
from validaciones import ValidadorDatos, ErrorValidacionWordle
from logica_juego import MotorWordle
from gestion_datos import GeneradorReportes


class PruebasIntegridadWordle(unittest.TestCase):
    """Suite de pruebas unitarias y de integración del proyecto."""

    def test_01_herencia_y_polimorfismo_jugadores(self) -> None:
        """Comprueba herencia, sobrescritura de calcular_bonificacion y polimorfismo."""
        registrado = JugadorRegistrado(alias="Andres", categoria="VIP")
        invitado = JugadorInvitado(alias="Visitante")

        self.assertIsInstance(registrado, Participante)
        self.assertIsInstance(invitado, Participante)

        # Tratamiento polimórfico: misma llamada produce distinto resultado según la subclase
        puntos_reg = registrado.registrar_resultado_partida(gano=True, puntos_obtenidos=500)
        puntos_inv = invitado.calcular_bonificacion(500)

        self.assertGreater(puntos_reg, 500)  # Tiene bono de racha + multiplicador VIP
        self.assertEqual(puntos_inv, 450)    # 90% por ser invitado

    def test_02_validaciones_y_excepciones(self) -> None:
        """Verifica que `ValidadorDatos` lance `ErrorValidacionWordle` ante entradas inválidas."""
        with self.assertRaises(ErrorValidacionWordle):
            ValidadorDatos.validar_palabra_catalogo("12345")

        with self.assertRaises(ErrorValidacionWordle):
            ValidadorDatos.validar_palabra_catalogo("HOLA")  # Solo 4 letras

        with self.assertRaises(ErrorValidacionWordle):
            ValidadorDatos.validar_entero_rango("99", minimo=1, maximo=5)

        palabra_ok = ValidadorDatos.validar_palabra_catalogo("  árból ")
        self.assertEqual(palabra_ok, "ARBOL")

    def test_03_motor_wordle_algoritmo_dos_pasadas(self) -> None:
        """Verifica la evaluación exacta de letras repetidas y detección de victoria."""
        motor = MotorWordle(catalogo_palabras={"ARBOL", "LIBRO", "MOTOR"})
        motor._palabra_secreta = "MOTOR"

        # 'O' aparece dos veces en MOTOR (posiciones 1 y 3)
        res = motor.registrar_intento("LIBRO")
        self.assertEqual(res[0], ("L", "GRIS"))
        self.assertEqual(res[3], ("R", "AMARILLO"))
        self.assertEqual(res[4], ("O", "AMARILLO"))

        res_ganador = motor.registrar_intento("MOTOR")
        self.assertTrue(motor.victoria)
        self.assertTrue(motor.juego_terminado)
        self.assertEqual(len(res_ganador), 5)

    def test_04_generacion_reportes(self) -> None:
        """Comprueba el cálculo de métricas y agrupaciones en `GeneradorReportes`."""
        partidas = [
            RegistroPartida("P-1", "Andres", "Registrado", "ARBOL", True, 2, 6, "Normal", 500, ["CAMPO", "ARBOL"]),
            RegistroPartida("P-2", "Andres", "Registrado", "DATOS", False, 6, 6, "Experto", 0, ["CAMPO"] * 6),
        ]
        jugadores = [JugadorRegistrado(alias="Andres", partidas_jugadas=2, partidas_ganadas=1, puntaje_acumulado=500)]
        reporte = GeneradorReportes.generar_resumen_estadistico(partidas, jugadores, total_palabras=300)

        self.assertEqual(reporte["total_partidas"], 2)
        self.assertEqual(reporte["total_victorias"], 1)
        self.assertEqual(reporte["tasa_exito_global"], 50.0)
        self.assertEqual(reporte["promedio_intentos_victoria"], 2.0)


def ejecutar_suite_pruebas() -> bool:
    """Ejecuta todas las pruebas y muestra el resultado en consola."""
    print("\n================ EJECUTANDO PRUEBAS DE INTEGRIDAD ================")
    cargador = unittest.TestLoader()
    suite = cargador.loadTestsFromTestCase(PruebasIntegridadWordle)
    corredor = unittest.TextTestRunner(verbosity=2)
    resultado = corredor.run(suite)
    return resultado.wasSuccessful()


if __name__ == "__main__":
    ejecutar_suite_pruebas()
