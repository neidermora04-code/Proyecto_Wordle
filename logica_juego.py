"""
Módulo de Reglas de Negocio del juego Wordle (Lab 02 y Lab 03).
Implementa el algoritmo de evaluación de letras en dos pasadas, soporte de niveles
de dificultad, uso de listas, tuplas, conjuntos (`set`) y diccionarios.
"""

import random
from typing import Set, List, Tuple, Dict, Any
from config import CONFIG_JUEGO
from validaciones import ValidadorDatos


class MotorWordle:
    """
    Clase que encapsula las reglas de negocio, el estado de una partida activa
    y la evaluación de intentos del juego Wordle.
    """

    ESTADO_CORRECTO: str = "VERDE"       # Letra en la posición exacta
    ESTADO_PRESENTE: str = "AMARILLO"    # Letra en la palabra, pero en otra posición
    ESTADO_AUSENTE: str = "GRIS"         # Letra que no está en la palabra

    def __init__(
        self,
        catalogo_palabras: Set[str],
        max_intentos: int = CONFIG_JUEGO[1],
        multiplicador_dificultad: float = 1.0,
        nombre_dificultad: str = "Normal (6 intentos)",
        exigir_en_diccionario: bool = False
    ) -> None:
        if not catalogo_palabras:
            raise ValueError("El catálogo de palabras no puede estar vacío.")

        self._longitud_palabra: int = CONFIG_JUEGO[0]
        self._max_intentos: int = max_intentos
        self._multiplicador_dificultad: float = multiplicador_dificultad
        self._nombre_dificultad: str = nombre_dificultad

        # Conjunto (Set) para validación instantánea O(1)
        self._palabras_validas: Set[str] = {p.upper() for p in catalogo_palabras}
        self._palabra_secreta: str = random.choice(tuple(self._palabras_validas))
        self._exigir_en_diccionario: bool = exigir_en_diccionario

        # Lista anidada de tuplas: [[(letra, estado), ...], ...]
        self._historial_intentos: List[List[Tuple[str, str]]] = []
        self._palabras_intentadas: List[str] = []

        # Diccionario por comprensión para el estado de las teclas
        self._estado_teclado: Dict[str, str] = {
            letra: "SIN_USAR" for letra in "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
        }

        self._juego_terminado: bool = False
        self._victoria: bool = False

    @property
    def palabra_secreta(self) -> str:
        return self._palabra_secreta

    @property
    def max_intentos(self) -> int:
        return self._max_intentos

    @property
    def nombre_dificultad(self) -> str:
        return self._nombre_dificultad

    @property
    def intentos_realizados(self) -> int:
        return len(self._historial_intentos)

    @property
    def intentos_restantes(self) -> int:
        return self._max_intentos - self.intentos_realizados

    @property
    def historial(self) -> List[List[Tuple[str, str]]]:
        return list(self._historial_intentos)

    @property
    def palabras_intentadas(self) -> List[str]:
        return list(self._palabras_intentadas)

    @property
    def estado_teclado(self) -> Dict[str, str]:
        return self._estado_teclado.copy()

    @property
    def juego_terminado(self) -> bool:
        return self._juego_terminado

    @property
    def victoria(self) -> bool:
        return self._victoria

    def validar_intento(self, intento_crudo: str) -> Tuple[bool, str]:
        """Delega la validación de formato y pertenencia al módulo `ValidadorDatos`."""
        return ValidadorDatos.validar_intento_juego(
            intento_crudo=intento_crudo,
            longitud_palabra=self._longitud_palabra,
            palabras_validas=self._palabras_validas,
            exigir_en_diccionario=self._exigir_en_diccionario
        )

    def registrar_intento(self, palabra_intento: str) -> List[Tuple[str, str]]:
        """
        Evalúa una palabra validada contra la palabra secreta utilizando el
        algoritmo oficial de dos pasadas con diccionario de frecuencias.
        """
        if self._juego_terminado:
            raise RuntimeError("No se pueden registrar más intentos: la partida ya finalizó.")

        palabra = ValidadorDatos.normalizar_palabra(palabra_intento)
        self._palabras_intentadas.append(palabra)

        # 1. Conteo de frecuencias de la palabra secreta usando un Diccionario
        frecuencia_restante: Dict[str, int] = {}
        for letra in self._palabra_secreta:
            frecuencia_restante[letra] = frecuencia_restante.get(letra, 0) + 1

        estados_posicion: List[str] = [self.ESTADO_AUSENTE] * self._longitud_palabra

        # 2. PRIMERA PASADA: Aciertos exactos (VERDE)
        for indice in range(self._longitud_palabra):
            letra_intento = palabra[indice]
            if letra_intento == self._palabra_secreta[indice]:
                estados_posicion[indice] = self.ESTADO_CORRECTO
                frecuencia_restante[letra_intento] -= 1

        # 3. SEGUNDA PASADA: Letras presentes en otra posición (AMARILLO)
        for indice in range(self._longitud_palabra):
            if estados_posicion[indice] == self.ESTADO_CORRECTO:
                continue

            letra_intento = palabra[indice]
            if frecuencia_restante.get(letra_intento, 0) > 0:
                estados_posicion[indice] = self.ESTADO_PRESENTE
                frecuencia_restante[letra_intento] -= 1

        resultado_turno: List[Tuple[str, str]] = []
        for indice in range(self._longitud_palabra):
            letra = palabra[indice]
            estado = estados_posicion[indice]
            resultado_turno.append((letra, estado))
            self._actualizar_prioridad_teclado(letra, estado)

        self._historial_intentos.append(resultado_turno)

        if palabra == self._palabra_secreta:
            self._victoria = True
            self._juego_terminado = True
        elif self.intentos_realizados >= self._max_intentos:
            self._victoria = False
            self._juego_terminado = True

        return resultado_turno

    def _actualizar_prioridad_teclado(self, letra: str, nuevo_estado: str) -> None:
        jerarquia: Dict[str, int] = {
            "SIN_USAR": 0,
            self.ESTADO_AUSENTE: 1,
            self.ESTADO_PRESENTE: 2,
            self.ESTADO_CORRECTO: 3
        }
        estado_actual = self._estado_teclado.get(letra, "SIN_USAR")
        if jerarquia[nuevo_estado] > jerarquia[estado_actual]:
            self._estado_teclado[letra] = nuevo_estado

    def calcular_puntaje_base(self) -> int:
        """Calcula el puntaje base ponderado por el multiplicador de dificultad."""
        if not self._victoria:
            return 0
        puntos_brutos = (self.intentos_restantes + 1) * 100
        return int(puntos_brutos * self._multiplicador_dificultad)
