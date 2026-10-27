"""
Módulo de Reglas de Negocio del juego Wordle (Lab 02 y Lab 03).
Implementa el algoritmo de evaluación de letras en dos pasadas, soporte de niveles
de dificultad, uso de listas, tuplas, conjuntos (`set`) y diccionarios.
"""

# Importamos 'random' para elegir al azar la palabra secreta de la partida
import random
# Importamos los tipos de colecciones para documentar firmas de métodos y atributos
from typing import Set, List, Tuple, Dict
# Importamos la tupla de configuración (5 letras, 6 intentos)
from config import CONFIG_JUEGO
# Importamos el validador de datos para sanitizar los intentos del jugador
from validaciones import ValidadorDatos


class MotorWordle:
    """
    Clase que encapsula las reglas de negocio, el estado de una partida activa
    y la evaluación de intentos del juego Wordle.
    """

    # Constantes de clase que representan los 3 estados posibles de cada letra al jugar
    ESTADO_CORRECTO: str = "VERDE"       # Letra acertada en la posición exacta
    ESTADO_PRESENTE: str = "AMARILLO"    # Letra existe en la palabra secreta, pero en otra posición
    ESTADO_AUSENTE: str = "GRIS"         # Letra que NO existe en la palabra secreta (o ya se agotó su frecuencia)

    def __init__(
        self,
        catalogo_palabras: Set[str],
        max_intentos: int = CONFIG_JUEGO[1],
        multiplicador_dificultad: float = 1.0,
        nombre_dificultad: str = "Normal (6 intentos)",
        exigir_en_diccionario: bool = False
    ) -> None:
        # Validamos que el conjunto de palabras no esté vacío antes de iniciar el juego
        if not catalogo_palabras:
            raise ValueError("El catálogo de palabras no puede estar vacío.")

        # Cantidad de letras por palabra (5 letras según CONFIG_JUEGO[0])
        self._longitud_palabra: int = CONFIG_JUEGO[0]
        # Límite de intentos según la dificultad elegida (7 en Fácil, 6 en Normal, 4 en Experto)
        self._max_intentos: int = max_intentos
        # Factor por el cual se multiplica el puntaje en caso de ganar (0.8, 1.0 o 1.5)
        self._multiplicador_dificultad: float = multiplicador_dificultad
        # Etiqueta descriptiva de la dificultad actual
        self._nombre_dificultad: str = nombre_dificultad

        # Comprensión de conjunto (Set): asegura que todas las palabras del catálogo estén en mayúsculas
        self._palabras_validas: Set[str] = {p.upper() for p in catalogo_palabras}
        # Convierte el conjunto en tupla y elige aleatoriamente una palabra secreta con random.choice()
        self._palabra_secreta: str = random.choice(tuple(self._palabras_validas))
        # Define si solo se permiten palabras que existan dentro del diccionario
        self._exigir_en_diccionario: bool = exigir_en_diccionario

        # Lista anidada de tuplas: guarda cada turno como una lista de 5 pares (letra, color)
        # Ejemplo: [[('A', 'VERDE'), ('R', 'GRIS'), ...], ...]
        self._historial_intentos: List[List[Tuple[str, str]]] = []
        # Lista simple con las palabras en texto que el usuario ha intentado en esta partida
        self._palabras_intentadas: List[str] = []

        # Diccionario por comprensión (Dict Comprehension - Lab 02):
        # Inicializa las 27 letras del abecedario español con el estado "SIN_USAR" para pintar el teclado en pantalla
        self._estado_teclado: Dict[str, str] = {
            letra: "SIN_USAR" for letra in "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
        }

        # Banderas booleanas que controlan cuándo termina el ciclo while de la partida y si el jugador ganó
        self._juego_terminado: bool = False
        self._victoria: bool = False

    @property
    def palabra_secreta(self) -> str:
        """Devuelve la palabra secreta sorteada para esta partida."""
        return self._palabra_secreta

    @property
    def max_intentos(self) -> int:
        """Devuelve el número máximo de intentos permitidos."""
        return self._max_intentos

    @property
    def nombre_dificultad(self) -> str:
        """Devuelve el nombre del nivel de dificultad actual."""
        return self._nombre_dificultad

    @property
    def intentos_realizados(self) -> int:
        """Calcula cuántos intentos lleva el jugador contando los elementos de _historial_intentos."""
        return len(self._historial_intentos)

    @property
    def intentos_restantes(self) -> int:
        """Calcula cuántos intentos le quedan disponibles al jugador."""
        return self._max_intentos - self.intentos_realizados

    @property
    def historial(self) -> List[List[Tuple[str, str]]]:
        """Retorna una copia de la lista de intentos evaluados para proteger el atributo interno."""
        return list(self._historial_intentos)

    @property
    def palabras_intentadas(self) -> List[str]:
        """Retorna una copia de la lista de palabras jugadas."""
        return list(self._palabras_intentadas)

    @property
    def estado_teclado(self) -> Dict[str, str]:
        """Retorna una copia del diccionario con los colores actuales de cada tecla del abecedario."""
        return self._estado_teclado.copy()

    @property
    def juego_terminado(self) -> bool:
        """Indica si la partida ya concluyó (por victoria o por agotar intentos)."""
        return self._juego_terminado

    @property
    def victoria(self) -> bool:
        """Indica si el jugador logró adivinar la palabra secreta."""
        return self._victoria

    def validar_intento(self, intento_crudo: str) -> Tuple[bool, str]:
        """Delega la validación de formato y longitud al módulo `ValidadorDatos`."""
        return ValidadorDatos.validar_intento_juego(
            intento_crudo=intento_crudo,
            longitud_palabra=self._longitud_palabra,
            palabras_validas=self._palabras_validas,
            exigir_en_diccionario=self._exigir_en_diccionario
        )

    def registrar_intento(self, palabra_intento: str) -> List[Tuple[str, str]]:
        """
        Evalúa una palabra validada contra la palabra secreta utilizando el
        algoritmo oficial de Wordle de DOS PASADAS con diccionario de frecuencias.
        Esto resuelve correctamente el caso de letras repetidas.
        """
        # Si la partida ya había terminado, impide seguir jugando lanzando RuntimeError
        if self._juego_terminado:
            raise RuntimeError("No se pueden registrar más intentos: la partida ya finalizó.")

        # Normalizamos la palabra jugada y la guardamos en la lista de palabras intentadas
        palabra = ValidadorDatos.normalizar_palabra(palabra_intento)
        self._palabras_intentadas.append(palabra)

        # PASO 1: Conteo de frecuencias de cada letra en la palabra secreta usando un Diccionario
        # Ejemplo: si la palabra secreta es "MOTOR", frecuencia_restante será {'M': 1, 'O': 2, 'T': 1, 'R': 1}
        frecuencia_restante: Dict[str, int] = {}
        for letra in self._palabra_secreta:
            frecuencia_restante[letra] = frecuencia_restante.get(letra, 0) + 1

        # Inicializamos las 5 posiciones del resultado en estado GRIS (ESTADO_AUSENTE) por defecto
        estados_posicion: List[str] = [self.ESTADO_AUSENTE] * self._longitud_palabra

        # PASO 2 (PRIMERA PASADA): Buscar primero TODOS los aciertos exactos (VERDE)
        # Se hace primero para que las letras verdes consuman disponibilidad antes de evaluar las amarillas
        for indice in range(self._longitud_palabra):
            letra_intento = palabra[indice]
            # Si la letra en esta posición coincide exactamente con la misma posición de la palabra secreta:
            if letra_intento == self._palabra_secreta[indice]:
                estados_posicion[indice] = self.ESTADO_CORRECTO
                # Restamos 1 a la cantidad disponible de esa letra en el diccionario
                frecuencia_restante[letra_intento] -= 1

        # PASO 3 (SEGUNDA PASADA): Evaluar letras presentes en otra posición (AMARILLO)
        for indice in range(self._longitud_palabra):
            # Si esta casilla ya fue marcada como VERDE en la primera pasada, la saltamos con 'continue'
            if estados_posicion[indice] == self.ESTADO_CORRECTO:
                continue

            letra_intento = palabra[indice]
            # Si la letra aún tiene apariciones disponibles (> 0) en la palabra secreta:
            if frecuencia_restante.get(letra_intento, 0) > 0:
                estados_posicion[indice] = self.ESTADO_PRESENTE
                # Descontamos 1 aparición para no pintar amarillos de más si el usuario repitió la letra
                frecuencia_restante[letra_intento] -= 1

        # PASO 4: Construir la lista de tuplas (letra, estado) del turno y actualizar los colores del teclado
        resultado_turno: List[Tuple[str, str]] = []
        for indice in range(self._longitud_palabra):
            letra = palabra[indice]
            estado = estados_posicion[indice]
            resultado_turno.append((letra, estado))
            # Actualiza el color de la tecla en el teclado virtual respetando la jerarquía de colores
            self._actualizar_prioridad_teclado(letra, estado)

        # Agregamos el resultado de este turno a la matriz de historial del tablero
        self._historial_intentos.append(resultado_turno)

        # PASO 5: Verificar condición de parada (Victoria si las palabras son iguales, o Derrota si agotó intentos)
        if palabra == self._palabra_secreta:
            self._victoria = True
            self._juego_terminado = True
        elif self.intentos_realizados >= self._max_intentos:
            self._victoria = False
            self._juego_terminado = True

        return resultado_turno

    def _actualizar_prioridad_teclado(self, letra: str, nuevo_estado: str) -> None:
        """
        Actualiza el estado visual de una tecla en el teclado virtual solo si el nuevo color
        tiene mayor prioridad (VERDE > AMARILLO > GRIS > SIN_USAR).
        Así una letra que ya fue VERDE nunca baja a AMARILLO o GRIS en turnos siguientes.
        """
        jerarquia: Dict[str, int] = {
            "SIN_USAR": 0,
            self.ESTADO_AUSENTE: 1,
            self.ESTADO_PRESENTE: 2,
            self.ESTADO_CORRECTO: 3
        }
        estado_actual = self._estado_teclado.get(letra, "SIN_USAR")
        # Solo sobreescribe el color en el diccionario si la nueva prioridad es mayor a la que ya tenía
        if jerarquia[nuevo_estado] > jerarquia[estado_actual]:
            self._estado_teclado[letra] = nuevo_estado

    def calcular_puntaje_base(self) -> int:
        """
        Calcula el puntaje base de la partida:
        Da 100 puntos por el turno ganador más 100 puntos por cada intento que le sobró,
        multiplicado por el factor de dificultad (0.8, 1.0 o 1.5). Si perdió, retorna 0.
        """
        if not self._victoria:
            return 0
        puntos_brutos = (self.intentos_restantes + 1) * 100
        return int(puntos_brutos * self._multiplicador_dificultad)
