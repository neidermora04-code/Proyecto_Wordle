"""
Módulo de Validación de Datos y Excepciones Personalizadas (Lab 01, 02, 03 y 04).
Separa la responsabilidad de validación de entradas y aplica:
- Herencia de `Exception` para errores de negocio propios.
- Uso explícito de `raise`, `try`, `except`, `else`, `finally`.
- Operadores lógicos (`and`, `or`, `not`), comparaciones y condicionales compuestos.
"""

from typing import Tuple, Set
from config import CONFIG_JUEGO, MAPA_ACENTOS


class ErrorValidacionWordle(Exception):
    """Excepción personalizada del dominio para errores de validación de negocio."""
    pass


class ValidadorDatos:
    """
    Clase utilitaria encargada de validar y sanitizar todas las entradas del usuario
    tanto en los menús administrativos como durante las partidas de Wordle.
    """

    @staticmethod
    def normalizar_palabra(texto: str) -> str:
        """Convierte a mayúsculas, recorta espacios y reemplaza vocales acentuadas."""
        limpio = texto.strip().upper()
        for con_tilde, sin_tilde in MAPA_ACENTOS.items():
            limpio = limpio.replace(con_tilde, sin_tilde)
        return limpio

    @classmethod
    def validar_palabra_catalogo(cls, palabra_cruda: str, longitud_esperada: int = CONFIG_JUEGO[0]) -> str:
        """
        Valida que una palabra candidata para el catálogo cumpla las reglas del dominio.
        Utiliza `raise ErrorValidacionWordle` cuando no se cumplen las condiciones (Lab 04).
        """
        palabra = cls.normalizar_palabra(palabra_cruda)

        if not palabra:
            raise ErrorValidacionWordle("La palabra no puede estar vacía.")
        elif not palabra.isalpha():
            raise ErrorValidacionWordle("La palabra solo debe contener letras del alfabeto (sin números ni espacios).")
        elif len(palabra) != longitud_esperada:
            raise ErrorValidacionWordle(
                f"La palabra '{palabra}' tiene {len(palabra)} letras, pero debe tener exactamente {longitud_esperada}."
            )
        return palabra

    @classmethod
    def validar_intento_juego(
        cls,
        intento_crudo: str,
        longitud_palabra: int,
        palabras_validas: Set[str],
        exigir_en_diccionario: bool = False
    ) -> Tuple[bool, str]:
        """
        Valida un intento dentro de una partida utilizando condicionales compuestos
        (`if`, `elif`, `else`) y pertenencia en conjuntos (`set`).
        Retorna una tupla `(es_valido, mensaje_o_palabra_normalizada)`.
        """
        intento = cls.normalizar_palabra(intento_crudo)

        if not intento:
            return (False, "La entrada está vacía. Por favor escribe una palabra.")
        elif not intento.isalpha():
            return (False, "La palabra solo puede contener letras (sin números ni símbolos).")
        elif len(intento) < longitud_palabra:
            return (False, f"Palabra muy corta ({len(intento)} letras). Debe tener exactamente {longitud_palabra}.")
        elif len(intento) > longitud_palabra:
            return (False, f"Palabra muy larga ({len(intento)} letras). Debe tener exactamente {longitud_palabra}.")
        elif exigir_en_diccionario and (intento not in palabras_validas):
            return (False, "La palabra no se encuentra registrada en el catálogo de palabras válidas.")
        else:
            return (True, intento)

    @staticmethod
    def validar_entero_rango(valor_texto: str, minimo: int, maximo: int, nombre_campo: str = "Valor") -> int:
        """
        Demuestra conversión de tipos (`int()`), bloques `try / except / else / finally`
        y lanzamiento de excepciones con `raise` (Lab 01 y Lab 04).
        """
        operacion_verificada = False
        try:
            numero = int(valor_texto.strip())
        except ValueError as err:
            raise ErrorValidacionWordle(f"{nombre_campo} inválido: '{valor_texto}' no es un número entero.") from err
        else:
            if numero < minimo or numero > maximo:
                raise ErrorValidacionWordle(
                    f"{nombre_campo} fuera de rango: debe estar entre {minimo} y {maximo}."
                )
            operacion_verificada = True
            return numero
        finally:
            # El bloque finally se ejecuta siempre, garantizando trazabilidad de la validación
            _ = operacion_verificada

    @staticmethod
    def validar_alias(alias_crudo: str) -> str:
        """Valida el nombre o alias de un jugador."""
        alias = alias_crudo.strip()
        if not alias:
            raise ErrorValidacionWordle("El alias del jugador no puede estar vacío.")
        elif len(alias) < 2 or len(alias) > 20:
            raise ErrorValidacionWordle("El alias debe tener entre 2 y 20 caracteres.")
        return alias

    @staticmethod
    def validar_categoria(categoria_cruda: str) -> str:
        """Valida la categoría de un jugador registrado."""
        categoria = categoria_cruda.strip()
        if not categoria:
            return "Estándar"
        if len(categoria) < 2 or len(categoria) > 15:
            raise ErrorValidacionWordle("La categoría debe tener entre 2 y 15 caracteres (ej. Estándar, VIP, Pro).")
        return categoria

