"""Métricas de fiabilidad y calidad para experimentos de esteganografía."""

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np
from scipy.signal import correlate, resample_poly


@dataclass(frozen=True)
class MetricasFiabilidad:
    """Resultados de una prueba de ocultación y recuperación."""

    ber: float
    accuracy_bits: float
    recuperacion_exacta: bool
    mensaje_completo: bool
    snr_db: float
    capacidad_bps: float
    tasa_informacion_efectiva_bps: float

    def como_dict(self) -> dict[str, float | bool]:
        """Devuelve las métricas en un formato adecuado para CSV/JSON."""
        return asdict(self)


def _bits(bits: Iterable[int] | str) -> np.ndarray:
    """Convierte una secuencia de bits o una cadena binaria en un vector."""
    if isinstance(bits, str):
        if any(bit not in "01" for bit in bits):
            raise ValueError("La cadena de bits solo puede contener 0 y 1.")
        return np.fromiter((int(bit) for bit in bits), dtype=np.uint8)

    result = np.asarray(list(bits), dtype=np.uint8).reshape(-1)
    if np.any(result > 1):
        raise ValueError("Los bits solo pueden tener los valores 0 o 1.")
    return result


def a_mono(audio: np.ndarray) -> np.ndarray:
    """Convierte audio multicanal a mono usando el promedio de canales."""
    samples = np.asarray(audio, dtype=np.float64)
    if samples.ndim == 1:
        return samples
    if samples.ndim != 2:
        raise ValueError("El audio debe ser un vector o una matriz de canales.")
    return samples.mean(axis=1)


def normalizar_audio(audio: np.ndarray, pico: float = 1.0) -> np.ndarray:
    """Normaliza el pico absoluto del audio, conservando silencio y signo."""
    if pico <= 0:
        raise ValueError("El pico de normalización debe ser positivo.")
    samples = a_mono(audio)
    maximo = np.max(np.abs(samples), initial=0.0)
    if maximo == 0:
        return samples.copy()
    return samples * (pico / maximo)


def alinear(
    ref: np.ndarray,
    rec: np.ndarray,
    fs_ref: int = 44100,
    fs_rec: int = 44100,
) -> np.ndarray:
    """Remuestrea y alinea ``rec`` con ``ref`` mediante correlación cruzada."""
    referencia = a_mono(ref)
    recibido = a_mono(rec)
    if fs_ref <= 0 or fs_rec <= 0:
        raise ValueError("Las frecuencias de muestreo deben ser positivas.")
    if referencia.size == 0 or recibido.size == 0:
        return np.zeros(referencia.size, dtype=np.float64)
    if fs_rec != fs_ref:
        recibido = resample_poly(recibido, fs_ref, fs_rec)

    correlacion = correlate(recibido, referencia, mode="full", method="fft")
    lag = int(np.argmax(np.abs(correlacion)) - (referencia.size - 1))
    if lag > 0:
        recibido = recibido[lag:]
    elif lag < 0:
        recibido = np.pad(recibido, (abs(lag), 0))
    return np.pad(
        recibido[: referencia.size],
        (0, max(0, referencia.size - recibido.size)),
    )


def normalizar_y_alinear(
    referencia: np.ndarray,
    recibido: np.ndarray,
    fs_referencia: int = 44100,
    fs_recibido: int = 44100,
) -> np.ndarray:
    """Prepara un audio recuperado para compararlo con la referencia."""
    referencia_normalizada = normalizar_audio(referencia)
    recibido_normalizado = normalizar_audio(recibido)
    return alinear(
        referencia_normalizada,
        recibido_normalizado,
        fs_ref=fs_referencia,
        fs_rec=fs_recibido,
    )


def snr_db(original: np.ndarray, stego: np.ndarray) -> float:
    """Calcula SNR en dB entre audio original y audio con datos ocultos."""
    original_mono = a_mono(original)
    stego_mono = a_mono(stego)
    if original_mono.shape != stego_mono.shape:
        raise ValueError("Los audios para SNR deben tener la misma longitud.")
    potencia_señal = np.mean(np.square(original_mono))
    potencia_ruido = np.mean(np.square(stego_mono - original_mono))
    if potencia_ruido == 0:
        return float("inf")
    if potencia_señal == 0:
        return float("-inf")
    return float(10 * np.log10(potencia_señal / potencia_ruido))

def _entropia_binaria(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return float(-p * np.log2(p) - (1 - p) * np.log2(1 - p))

def tasa_efectiva(capacidad_bps: float, ber: float) -> float:
    if ber >= 0.5:          # sin información útil (o decodificador invertido)
        return 0.0
    return capacidad_bps * (1.0 - _entropia_binaria(ber))


def evaluar_prueba(
    bits_originales: Iterable[int] | str,
    bits_recuperados: Iterable[int] | str,
    audio_original: np.ndarray,
    audio_stego: np.ndarray,
    fs: int,
) -> MetricasFiabilidad:
    """Calcula fiabilidad, degradación, capacidad y tasa efectiva de una prueba."""
    originales = _bits(bits_originales)
    recuperados = _bits(bits_recuperados)
    if originales.size == 0:
        raise ValueError("El mensaje debe contener al menos un bit.")
    if fs <= 0:
        raise ValueError("La frecuencia de muestreo debe ser positiva.")

    longitud = min(originales.size, recuperados.size)
    errores = np.count_nonzero(originales[:longitud] != recuperados[:longitud])
    errores += abs(originales.size - recuperados.size)
    ber = float(errores / originales.size)
    accuracy = float(1.0 - ber)
    exacta = bool(originales.size == recuperados.size and errores == 0)
    duracion = a_mono(audio_original).size / fs
    if duracion <= 0:
        raise ValueError("El audio original debe tener una duración positiva.")
    capacidad = float(originales.size / duracion)
    return MetricasFiabilidad(
        ber=ber,
        accuracy_bits=accuracy,
        recuperacion_exacta=exacta,
        mensaje_completo=exacta,
        snr_db=snr_db(audio_original, audio_stego),
        capacidad_bps=capacidad,
        tasa_informacion_efectiva_bps=tasa_efectiva(capacidad, ber)
    )


def tasa_recuperacion_exacta(resultados: Iterable[MetricasFiabilidad]) -> float:
    """Calcula la proporción de pruebas cuyo mensaje se recuperó completo."""
    pruebas = list(resultados)
    if not pruebas:
        raise ValueError("Se requiere al menos una prueba.")
    return float(np.mean([resultado.recuperacion_exacta for resultado in pruebas]))