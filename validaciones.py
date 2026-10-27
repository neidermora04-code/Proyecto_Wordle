"""
Módulo de Validación de Datos y Excepciones Personalizadas (Lab 01, 02, 03 y 04).
Separa la responsabilidad de validación de entradas y aplica:
- Herencia de `Exception` para errores de negocio propios.
- Uso explícito de `raise`, `try`, `except`, `else`, `finally`.
- Operadores lógicos (`and`, `or`, `not`), comparaciones y condicionales compuestos.
"""

# Importamos anotaciones de tipos Tuple y Set
from typing import Tuple, Set
# Importamos las constantes CONFIG_JUEGO y MAPA_ACENTOS desde nuestro módulo config.py
from config import CONFIG_JUEGO, MAPA_ACENTOS


class ErrorValidacionWordle(Exception):
    """
    Excepción personalizada del dominio que hereda de la clase base `Exception` de Python (Lab 04).
    Se lanza cuando el usuario ingresa datos que violan las reglas del juego o del sistema.
    """
    pass


class ValidadorDatos:
    """
    Clase utilitaria encargada de validar y sanitizar todas las entradas del usuario
    tanto en los menús administrativos como durante las partidas de Wordle.
    """

    @staticmethod
    def normalizar_palabra(texto: str) -> str:
        """Convierte a mayúsculas, recorta espacios laterales y reemplaza vocales con tilde."""
        # .strip() elimina espacios al inicio/final y .upper() pasa todo a letras mayúsculas
        limpio = texto.strip().upper()
        # Ciclo for que recorre cada par (vocal_con_tilde, vocal_sin_tilde) del diccionario MAPA_ACENTOS
        for con_tilde, sin_tilde in MAPA_ACENTOS.items():
            # Reemplaza por ejemplo 'Á' por 'A', 'É' por 'E', etc.
            limpio = limpio.replace(con_tilde, sin_tilde)
        # Devuelve la palabra completamente limpia y estandarizada
        return limpio

    @classmethod
    def validar_palabra_catalogo(cls, palabra_cruda: str, longitud_esperada: int = CONFIG_JUEGO[0]) -> str:
        """
        Valida que una palabra candidata para agregarse al catálogo cumpla las reglas del dominio.
        Utiliza `raise ErrorValidacionWordle` cuando no se cumplen las condiciones (Lab 04).
        """
        # Primero normalizamos la palabra (sin espacios, en mayúsculas y sin tildes)
        palabra = cls.normalizar_palabra(palabra_cruda)

        # Condicional compuesto (if / elif) para verificar cada regla:
        if not palabra:
            # Si la cadena está vacía, lanzamos nuestra excepción personalizada
            raise ErrorValidacionWordle("La palabra no puede estar vacía.")
        elif not palabra.isalpha():
            # Si contiene números, símbolos o espacios intermedios (.isalpha() es False)
            raise ErrorValidacionWordle("La palabra solo debe contener letras del alfabeto (sin números ni espacios).")
        elif len(palabra) != longitud_esperada:
            # Si no tiene exactamente 5 letras (longitud_esperada)
            raise ErrorValidacionWordle(
                f"La palabra '{palabra}' tiene {len(palabra)} letras, pero debe tener exactamente {longitud_esperada}."
            )
        # Si pasó todas las validaciones, retorna la palabra limpia
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
        # Normalizamos la entrada escrita por el jugador en el turno
        intento = cls.normalizar_palabra(intento_crudo)

        # Evaluamos en orden las posibles causas de error sin detener el programa:
        if not intento:
            return (False, "La entrada está vacía. Por favor escribe una palabra.")
        elif not intento.isalpha():
            return (False, "La palabra solo puede contener letras (sin números ni símbolos).")
        elif len(intento) < longitud_palabra:
            return (False, f"Palabra muy corta ({len(intento)} letras). Debe tener exactamente {longitud_palabra}.")
        elif len(intento) > longitud_palabra:
            return (False, f"Palabra muy larga ({len(intento)} letras). Debe tener exactamente {longitud_palabra}.")
        elif exigir_en_diccionario and (intento not in palabras_validas):
            # Operador lógico 'and' y búsqueda O(1) en el conjunto (Set) 'palabras_validas'
            return (False, "La palabra no se encuentra registrada en el catálogo de palabras válidas.")
        else:
            # Si cumple todas las reglas, retorna True y la palabra lista para evaluarse
            return (True, intento)

    @staticmethod
    def validar_entero_rango(valor_texto: str, minimo: int, maximo: int, nombre_campo: str = "Valor") -> int:
        """
        Demuestra conversión de tipos (`int()`), bloques completos `try / except / else / finally`
        y lanzamiento de excepciones con `raise` (Lab 01 y Lab 04).
        """
        # Bandera de control para trazabilidad de la validación
        operacion_verificada = False
        try:
            # Intentamos convertir el texto ingresado por teclado a un número entero (int)
            numero = int(valor_texto.strip())
        except ValueError as err:
            # Si el usuario escribió letras en vez de un número, capturamos ValueError y lanzamos ErrorValidacionWordle
            raise ErrorValidacionWordle(f"{nombre_campo} inválido: '{valor_texto}' no es un número entero.") from err
        else:
            # El bloque 'else' se ejecuta SOLO si el bloque 'try' no lanzó ninguna excepción
            # Verificamos con el operador lógico 'or' que el número esté dentro del rango permitido [minimo, maximo]
            if numero < minimo or numero > maximo:
                raise ErrorValidacionWordle(
                    f"{nombre_campo} fuera de rango: debe estar entre {minimo} y {maximo}."
                )
            operacion_verificada = True
            return numero
        finally:
            # El bloque 'finally' se ejecuta SIEMPRE (haya ocurrido error o no)
            _ = operacion_verificada

    @staticmethod
    def validar_alias(alias_crudo: str) -> str:
        """Valida que el nombre o alias de un jugador tenga entre 2 y 20 caracteres."""
        alias = alias_crudo.strip()
        if not alias:
            raise ErrorValidacionWordle("El alias del jugador no puede estar vacío.")
        elif len(alias) < 2 or len(alias) > 20:
            raise ErrorValidacionWordle("El alias debe tener entre 2 y 20 caracteres.")
        return alias

    @staticmethod
    def validar_categoria(categoria_cruda: str) -> str:
        """Valida la categoría de un jugador registrado (por defecto asigna 'Estándar')."""
        categoria = categoria_cruda.strip()
        if not categoria:
            return "Estándar"
        if len(categoria) < 2 or len(categoria) > 15:
            raise ErrorValidacionWordle("La categoría debe tener entre 2 y 15 caracteres (ej. Estándar, VIP, Pro).")
        return categoria
