"""
Módulo de Modelos y Entidades del Dominio (Lab 03 y Lab 04).
Demuestra explícitamente:
- Herencia (Clase base `Participante` -> Subclases `JugadorRegistrado`, `JugadorInvitado`).
- Sobrescritura de métodos (`calcular_bonificacion`, `obtener_tipo`, `__str__`).
- Polimorfismo (tratamiento uniforme de distintos tipos de participantes).
- Composición (`RegistroPartida` compuesta por datos del jugador y métricas del turno).
- Encapsulamiento y Propiedades (`@property` y `@setter`).
"""

from datetime import datetime
from typing import Dict, Any, List


class Participante:
    """
    Clase base (Superclase) que representa a cualquier usuario del sistema.
    Aplica encapsulamiento mediante atributos protegidos y propiedades.
    """

    def __init__(self, alias: str, categoria: str = "General") -> None:
        self._alias: str = alias.strip()
        self._categoria: str = categoria.strip()
        self._activo: bool = True

    @property
    def alias(self) -> str:
        """Propiedad de lectura para el alias del participante."""
        return self._alias

    @alias.setter
    def alias(self, nuevo_alias: str) -> None:
        """Setter con validación e invocación de `raise` (Lab 04)."""
        limpio = nuevo_alias.strip()
        if not limpio or len(limpio) < 2:
            raise ValueError("El alias debe contener al menos 2 caracteres válidos.")
        self._alias = limpio

    @property
    def categoria(self) -> str:
        return self._categoria

    @categoria.setter
    def categoria(self, nueva_categoria: str) -> None:
        if not nueva_categoria.strip():
            raise ValueError("La categoría no puede estar vacía.")
        self._categoria = nueva_categoria.strip()

    @property
    def activo(self) -> bool:
        return self._activo

    def cambiar_estado_activo(self, nuevo_estado: bool) -> None:
        """Operación que modifica el estado interno del objeto."""
        self._activo = bool(nuevo_estado)

    def calcular_bonificacion(self, puntaje_base: int) -> int:
        """
        Método polimórfico que será sobrescrito por las clases hijas.
        Por defecto no otorga bonificación adicional.
        """
        return puntaje_base

    def obtener_tipo(self) -> str:
        """Método sobrescribible para identificar el tipo de entidad."""
        return "Participante Base"

    def a_diccionario(self) -> Dict[str, Any]:
        """Serializa el objeto a un diccionario compatible con JSON."""
        return {
            "alias": self._alias,
            "categoria": self._categoria,
            "activo": self._activo,
            "tipo": self.obtener_tipo()
        }

    def __str__(self) -> str:
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
        super().__init__(alias=alias, categoria=categoria)
        self._partidas_jugadas: int = int(partidas_jugadas)
        self._partidas_ganadas: int = int(partidas_ganadas)
        self._puntaje_acumulado: int = int(puntaje_acumulado)
        self._racha_actual: int = int(racha_actual)
        self._activo = activo

    @property
    def partidas_jugadas(self) -> int:
        return self._partidas_jugadas

    @property
    def partidas_ganadas(self) -> int:
        return self._partidas_ganadas

    @property
    def puntaje_acumulado(self) -> int:
        return self._puntaje_acumulado

    @property
    def racha_actual(self) -> int:
        return self._racha_actual

    @property
    def porcentaje_victorias(self) -> float:
        """Propiedad calculada dinámicamente."""
        if self._partidas_jugadas == 0:
            return 0.0
        return round((self._partidas_ganadas / self._partidas_jugadas) * 100.0, 2)

    def registrar_resultado_partida(self, gano: bool, puntos_obtenidos: int) -> int:
        """
        Modifica el estado del objeto actualizando estadísticas y racha.
        Retorna el puntaje final tras aplicar la bonificación polimórfica.
        """
        self._partidas_jugadas += 1
        if gano:
            self._partidas_ganadas += 1
            self._racha_actual += 1
            puntos_finales = self.calcular_bonificacion(puntos_obtenidos)
        else:
            self._racha_actual = 0
            puntos_finales = 0

        self._puntaje_acumulado += puntos_finales
        return puntos_finales

    # SOBRESCRITURA DE MÉTODO (Override) Y POLIMORFISMO (Lab 04)
    def calcular_bonificacion(self, puntaje_base: int) -> int:
        """
        Sobrescribe el método de la clase padre:
        Otorga +25 puntos extra por cada victoria en la racha actual y un 20% extra si es categoría VIP/Pro.
        """
        if puntaje_base <= 0:
            return 0
        bono_racha = self._racha_actual * 25
        multiplicador_cat = 1.2 if self._categoria.upper() in ("VIP", "PRO", "AVANZADO") else 1.0
        return int((puntaje_base + bono_racha) * multiplicador_cat)

    def obtener_tipo(self) -> str:
        return "Registrado"

    def a_diccionario(self) -> Dict[str, Any]:
        datos = super().a_diccionario()
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
        """Método de fábrica para reconstruir el objeto desde persistencia JSON."""
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
        super().__init__(alias=alias, categoria="Temporal")

    # SOBRESCRITURA DE MÉTODO (Override)
    def calcular_bonificacion(self, puntaje_base: int) -> int:
        """Los invitados reciben el 90% del puntaje base y no acumulan bono de racha."""
        return int(puntaje_base * 0.9)

    def obtener_tipo(self) -> str:
        return "Invitado"


class RegistroPartida:
    """
    Entidad de dominio que modela una partida jugada.
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
        self.id_partida: str = id_partida
        self.jugador: str = jugador
        self.tipo_jugador: str = tipo_jugador
        self.palabra_secreta: str = palabra_secreta.upper()
        self.gano: bool = bool(gano)
        self.intentos_usados: int = int(intentos_usados)
        self.max_intentos: int = int(max_intentos)
        self.dificultad: str = dificultad
        self.puntaje: int = int(puntaje)
        self.palabras_intentadas: List[str] = list(palabras_intentadas)
        self.fecha: str = fecha if fecha else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def estado_texto(self) -> str:
        return "VICTORIA" if self.gano else "DERROTA"

    def a_diccionario(self) -> Dict[str, Any]:
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
        return (
            f"[{self.id_partida}] {self.fecha} | Jugador: {self.jugador:<12} | "
            f"Palabra: {self.palabra_secreta} | {self.estado_texto:<8} | "
            f"Intentos: {self.intentos_usados}/{self.max_intentos} ({self.dificultad}) | "
            f"Pts: {self.puntaje}"
        )
