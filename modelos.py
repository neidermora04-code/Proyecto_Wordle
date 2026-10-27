"""
Módulo de Modelos y Entidades del Dominio (Lab 03 y Lab 04).
Demuestra explícitamente:
- Herencia (Clase base `Participante` -> Subclases `JugadorRegistrado`, `JugadorInvitado`).
- Sobrescritura de métodos (`calcular_bonificacion`, `obtener_tipo`, `__str__`).
- Polimorfismo (tratamiento uniforme de distintos tipos de participantes).
- Composición (`RegistroPartida` compuesta por datos del jugador y métricas del turno).
- Encapsulamiento y Propiedades (`@property` y `@setter`).
"""

# Importamos 'datetime' para generar la fecha y hora exacta en que se juega cada partida
from datetime import datetime
# Importamos anotaciones de tipos para documentar diccionarios y listas
from typing import Dict, Any, List


class Participante:
    """
    Clase base (Superclase) que representa a cualquier usuario del sistema.
    Aplica encapsulamiento mediante atributos protegidos y propiedades.
    """

    def __init__(self, alias: str, categoria: str = "General") -> None:
        # Constructor de la clase padre: inicializa atributos protegidos (con guion bajo '_')
        # Guardamos el alias quitando espacios al inicio y al final con .strip()
        self._alias: str = alias.strip()
        # Guardamos la categoría del participante quitando espacios sobrantes
        self._categoria: str = categoria.strip()
        # Todo participante inicia por defecto con estado activo (True)
        self._activo: bool = True

    @property
    def alias(self) -> str:
        """Propiedad de lectura (Getter) para consultar el alias protegido '_alias'."""
        return self._alias

    @alias.setter
    def alias(self, nuevo_alias: str) -> None:
        """Propiedad de escritura (Setter) con validación e invocación de `raise` (Lab 04)."""
        # Limpiamos espacios en blanco del nuevo alias recibido
        limpio = nuevo_alias.strip()
        # Si quedó vacío o tiene menos de 2 letras, lanzamos un error ValueError con 'raise'
        if not limpio or len(limpio) < 2:
            raise ValueError("El alias debe contener al menos 2 caracteres válidos.")
        # Si pasó la validación, actualizamos el atributo protegido
        self._alias = limpio

    @property
    def categoria(self) -> str:
        """Propiedad de lectura (Getter) para obtener la categoría del participante."""
        return self._categoria

    @categoria.setter
    def categoria(self, nueva_categoria: str) -> None:
        """Setter que valida que la nueva categoría no sea una cadena vacía."""
        if not nueva_categoria.strip():
            raise ValueError("La categoría no puede estar vacía.")
        # Actualiza el atributo protegido con el texto limpio
        self._categoria = nueva_categoria.strip()

    @property
    def activo(self) -> bool:
        """Propiedad de lectura que indica si el participante está habilitado (True) o deshabilitado (False)."""
        return self._activo

    def cambiar_estado_activo(self, nuevo_estado: bool) -> None:
        """Operación que modifica el estado interno del objeto (activar o desactivar jugador)."""
        self._activo = bool(nuevo_estado)

    def calcular_bonificacion(self, puntaje_base: int) -> int:
        """
        Método polimórfico que será sobrescrito por las clases hijas.
        Por defecto en la clase padre no otorga bonificación adicional y devuelve el mismo puntaje.
        """
        return puntaje_base

    def obtener_tipo(self) -> str:
        """Método sobrescribible para identificar qué tipo de participante es."""
        return "Participante Base"

    def a_diccionario(self) -> Dict[str, Any]:
        """Serializa (convierte) el objeto a un diccionario de Python para poder guardarlo en JSON."""
        return {
            "alias": self._alias,
            "categoria": self._categoria,
            "activo": self._activo,
            "tipo": self.obtener_tipo()
        }

    def __str__(self) -> str:
        """Método especial que define cómo se muestra el objeto cuando hacemos print(objeto)."""
        # Operador ternario: muestra "Activo" si self._activo es True, de lo contrario "Inactivo"
        estado_str = "Activo" if self._activo else "Inactivo"
        return f"[{self.obtener_tipo()}] {self._alias} ({self._categoria}) - {estado_str}"


class JugadorRegistrado(Participante):
    """
    Subclase que hereda de `Participante` (Herencia - Lab 04).
    Representa a un jugador registrado (sin pedir correo electrónico) con seguimiento
    de racha, partidas y bonificaciones.
    """

    def __init__(
        self,
        alias: str,
        categoria: str = "Estándar",
        partidas_jugadas: int = 0,
        partidas_ganadas: int = 0,
        puntaje_acumulado: int = 0,
        racha_actual: int = 0,
        activo: bool = True
    ) -> None:
        # Llamamos a super().__init__() para reutilizar el constructor de la clase padre (Participante)
        super().__init__(alias=alias, categoria=categoria)
        # Inicializamos los atributos propios de un JugadorRegistrado convirtiéndolos a entero (int)
        self._partidas_jugadas: int = int(partidas_jugadas)
        self._partidas_ganadas: int = int(partidas_ganadas)
        self._puntaje_acumulado: int = int(puntaje_acumulado)
        self._racha_actual: int = int(racha_actual)
        self._activo = activo

    @property
    def partidas_jugadas(self) -> int:
        """Getter del total de partidas jugadas por este jugador."""
        return self._partidas_jugadas

    @property
    def partidas_ganadas(self) -> int:
        """Getter del total de victorias acumuladas."""
        return self._partidas_ganadas

    @property
    def puntaje_acumulado(self) -> int:
        """Getter del puntaje histórico total en el ranking."""
        return self._puntaje_acumulado

    @property
    def racha_actual(self) -> int:
        """Getter de cuántas victorias seguidas lleva actualmente sin perder."""
        return self._racha_actual

    @property
    def porcentaje_victorias(self) -> float:
        """Propiedad calculada dinámicamente: calcula el % de efectividad (victorias / jugadas * 100)."""
        # Evitamos el error de división por cero (ZeroDivisionError) si aún no ha jugado partidas
        if self._partidas_jugadas == 0:
            return 0.0
        # Redondeamos a 2 decimales con round()
        return round((self._partidas_ganadas / self._partidas_jugadas) * 100.0, 2)

    def registrar_resultado_partida(self, gano: bool, puntos_obtenidos: int) -> int:
        """
        Modifica el estado del objeto actualizando estadísticas y racha al terminar un juego.
        Retorna el puntaje final tras aplicar la bonificación polimórfica.
        """
        # Incrementa en 1 el contador de partidas jugadas
        self._partidas_jugadas += 1
        if gano:
            # Si ganó la partida: suma 1 victoria, suma 1 a la racha y calcula su bono de puntos
            self._partidas_ganadas += 1
            self._racha_actual += 1
            puntos_finales = self.calcular_bonificacion(puntos_obtenidos)
        else:
            # Si perdió: la racha de victorias consecutivas se reinicia a 0 y gana 0 puntos
            self._racha_actual = 0
            puntos_finales = 0

        # Suma los puntos obtenidos al puntaje total histórico del jugador
        self._puntaje_acumulado += puntos_finales
        return puntos_finales

    # SOBRESCRITURA DE MÉTODO (Override) Y POLIMORFISMO (Lab 04)
    def calcular_bonificacion(self, puntaje_base: int) -> int:
        """
        Sobrescribe el método de la clase padre `Participante`:
        Otorga +25 puntos extra por cada victoria en la racha actual y un 20% extra si es categoría VIP/Pro.
        """
        # Si no obtuvo puntos base, retorna 0 directamente
        if puntaje_base <= 0:
            return 0
        # Por cada partida en racha suma 25 puntos adicionales
        bono_racha = self._racha_actual * 25
        # Si pertenece a categoría VIP, PRO o AVANZADO, multiplica todo por 1.2 (+20% extra)
        multiplicador_cat = 1.2 if self._categoria.upper() in ("VIP", "PRO", "AVANZADO") else 1.0
        # Retorna el resultado convertido a número entero
        return int((puntaje_base + bono_racha) * multiplicador_cat)

    def obtener_tipo(self) -> str:
        """Sobrescribe obtener_tipo() para identificar a esta subclase como 'Registrado'."""
        return "Registrado"

    def a_diccionario(self) -> Dict[str, Any]:
        """Extiende el diccionario de la clase padre agregando las métricas competitivas del jugador."""
        # Primero obtiene el diccionario básico desde Participante usando super()
        datos = super().a_diccionario()
        # Agrega las claves específicas del jugador registrado con .update()
        datos.update({
            "partidas_jugadas": self._partidas_jugadas,
            "partidas_ganadas": self._partidas_ganadas,
            "puntaje_acumulado": self._puntaje_acumulado,
            "racha_actual": self._racha_actual,
            "porcentaje_victorias": self.porcentaje_victorias
        })
        return datos

    @classmethod
    def desde_diccionario(cls, datos: Dict[str, Any]) -> "JugadorRegistrado":
        """Método de clase (Factory Method) para reconstruir un objeto JugadorRegistrado al leer el JSON."""
        return cls(
            alias=datos.get("alias", "Jugador"),
            categoria=datos.get("categoria", "Estándar"),
            partidas_jugadas=datos.get("partidas_jugadas", 0),
            partidas_ganadas=datos.get("partidas_ganadas", 0),
            puntaje_acumulado=datos.get("puntaje_acumulado", 0),
            racha_actual=datos.get("racha_actual", 0),
            activo=datos.get("activo", True)
        )

    def __str__(self) -> str:
        """Sobrescribe la representación en texto para incluir PJ, PG, %, Racha y Puntaje."""
        base = super().__str__()
        return (
            f"{base} | PJ: {self._partidas_jugadas} | PG: {self._partidas_ganadas} ({self.porcentaje_victorias}%) | "
            f"Racha: {self._racha_actual} | Pts: {self._puntaje_acumulado}"
        )


class JugadorInvitado(Participante):
    """
    Segunda subclase que hereda de `Participante` (Herencia y Polimorfismo - Lab 04).
    Representa un jugador temporal sin racha acumulada y con penalización leve de puntaje.
    """

    def __init__(self, alias: str) -> None:
        # Llama al constructor de Participante fijando automáticamente la categoría en "Temporal"
        super().__init__(alias=alias, categoria="Temporal")

    # SOBRESCRITURA DE MÉTODO (Override)
    def calcular_bonificacion(self, puntaje_base: int) -> int:
        """
        Polimorfismo: a diferencia de JugadorRegistrado, un JugadorInvitado recibe solo el 90%
        del puntaje base (multiplica por 0.9) y no acumula bono de racha.
        """
        return int(puntaje_base * 0.9)

    def obtener_tipo(self) -> str:
        """Sobrescribe obtener_tipo() para devolver 'Invitado'."""
        return "Invitado"


class RegistroPartida:
    """
    Entidad de dominio que modela una partida jugada completa.
    Demuestra COMPOSICIÓN al asociar la información de un `Participante`
    con los detalles técnicos del turno (palabra, intentos, dificultad, fecha).
    """

    def __init__(
        self,
        id_partida: str,
        jugador: str,
        tipo_jugador: str,
        palabra_secreta: str,
        gano: bool,
        intentos_usados: int,
        max_intentos: int,
        dificultad: str,
        puntaje: int,
        palabras_intentadas: List[str],
        fecha: str = ""
    ) -> None:
        # Código único de la partida (ej. "PART-001")
        self.id_partida: str = id_partida
        # Alias del jugador que jugó la partida
        self.jugador: str = jugador
        # Tipo de participante ("Registrado" o "Invitado")
        self.tipo_jugador: str = tipo_jugador
        # Palabra secreta que debía adivinar (normalizada en mayúsculas)
        self.palabra_secreta: str = palabra_secreta.upper()
        # Booleano: True si adivinó la palabra, False si agotó los intentos
        self.gano: bool = bool(gano)
        # Número de intentos que empleó en la partida
        self.intentos_usados: int = int(intentos_usados)
        # Máximo de intentos permitidos según la dificultad elegida (7, 6 o 4)
        self.max_intentos: int = int(max_intentos)
        # Nombre de la dificultad jugada ("Fácil", "Normal", "Experto")
        self.dificultad: str = dificultad
        # Puntaje definitivo obtenido en esta partida
        self.puntaje: int = int(puntaje)
        # Lista con el historial de palabras que escribió el usuario en cada turno
        self.palabras_intentadas: List[str] = list(palabras_intentadas)
        # Si no se pasa una fecha, toma automáticamente la fecha y hora actual del sistema
        self.fecha: str = fecha if fecha else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def estado_texto(self) -> str:
        """Propiedad que traduce el booleano 'self.gano' a texto legible ('VICTORIA' o 'DERROTA')."""
        return "VICTORIA" if self.gano else "DERROTA"

    def a_diccionario(self) -> Dict[str, Any]:
        """Convierte el registro de la partida a un diccionario para guardarlo en JSON o CSV."""
        return {
            "id_partida": self.id_partida,
            "fecha": self.fecha,
            "jugador": self.jugador,
            "tipo_jugador": self.tipo_jugador,
            "palabra_secreta": self.palabra_secreta,
            "gano": self.gano,
            "estado": self.estado_texto,
            "intentos_usados": self.intentos_usados,
            "max_intentos": self.max_intentos,
            "dificultad": self.dificultad,
            "puntaje": self.puntaje,
            "palabras_intentadas": self.palabras_intentadas
        }

    @classmethod
    def desde_diccionario(cls, datos: Dict[str, Any]) -> "RegistroPartida":
        """Reconstruye un objeto RegistroPartida a partir de un diccionario leído de JSON o Google Sheets."""
        return cls(
            id_partida=datos.get("id_partida", "PART-000"),
            jugador=datos.get("jugador", "Anónimo"),
            tipo_jugador=datos.get("tipo_jugador", "Registrado"),
            palabra_secreta=datos.get("palabra_secreta", "ARBOL"),
            gano=datos.get("gano", False),
            intentos_usados=datos.get("intentos_usados", 0),
            max_intentos=datos.get("max_intentos", 6),
            dificultad=datos.get("dificultad", "Normal"),
            puntaje=datos.get("puntaje", 0),
            palabras_intentadas=datos.get("palabras_intentadas", []),
            fecha=datos.get("fecha", "")
        )

    def __str__(self) -> str:
        """Representación en texto alineada en columnas mediante f-strings."""
        return (
            f"[{self.id_partida}] {self.fecha} | Jugador: {self.jugador:<12} | "
            f"Palabra: {self.palabra_secreta} | {self.estado_texto:<8} | "
            f"Intentos: {self.intentos_usados}/{self.max_intentos} ({self.dificultad}) | "
            f"Pts: {self.puntaje}"
        )
