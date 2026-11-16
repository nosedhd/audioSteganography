"""Utilidades compartidas para las técnicas de esteganografía."""

from collections.abc import Iterable

import numpy as np


def texto_a_bits(texto: str) -> str:
    """Codifica texto Unicode en una cadena de bits UTF-8."""
    return "".join(format(byte, "08b") for byte in texto.encode("utf-8"))


def bits_a_texto(bits: str) -> str:
    """Decodifica una cadena de bits UTF-8, ignorando un byte incompleto."""
    bytes_data = bytes(
        int(bits[i : i + 8], 2)
        for i in range(0, len(bits) - 7, 8)
    )
    return bytes_data.decode("utf-8", errors="replace")


def bits_array(bits: Iterable[int] | str) -> np.ndarray:
    """Convierte bits en un vector uint8 validado."""
    if isinstance(bits, str):
        if any(bit not in "01" for bit in bits):
            raise ValueError("Los bits solo pueden contener 0 y 1.")
        return np.fromiter((int(bit) for bit in bits), dtype=np.uint8)
    result = np.asarray(list(bits), dtype=np.uint8).reshape(-1)
    if np.any(result > 1):
        raise ValueError("Los bits solo pueden tener los valores 0 o 1.")
    return result


def a_mono(audio: np.ndarray) -> np.ndarray:
    """Selecciona el primer canal, igual que los codificadores existentes."""
    samples = np.asarray(audio)
    if samples.ndim == 1:
        return samples.copy()
    if samples.ndim != 2 or samples.shape[1] == 0:
        raise ValueError("El audio debe ser un vector o una matriz de canales.")
    return samples[:, 0].copy()


def normalizar_portador(audio: np.ndarray, pico: float = 0.8) -> np.ndarray:
    """Convierte el portador a mono y limita su pico al valor indicado."""
    if pico <= 0 or pico > 1:
        raise ValueError("El pico debe estar entre 0 y 1.")
    samples = a_mono(audio).astype(np.float64, copy=False)
    maximo = np.max(np.abs(samples), initial=0.0)
    if maximo == 0:
        return samples.copy()
    return samples * (pico / maximo)


def normalizar_lsb(audio: np.ndarray, pico: float = 0.8) -> np.ndarray:
    """Normaliza un portador entero al 80 % de su rango sin perder el tipo."""
    samples = a_mono(audio)
    if not np.issubdtype(samples.dtype, np.integer):
        raise TypeError("LSB requiere muestras de audio enteras.")
    info = np.iinfo(samples.dtype)
    maximo = np.max(np.abs(samples.astype(np.float64)), initial=0.0)
    if maximo == 0:
        return samples.astype(samples.dtype, copy=True)
    escala = pico * info.max / maximo
    return np.clip(
        np.rint(samples.astype(np.float64) * escala),
        info.min,
        info.max,
    ).astype(samples.dtype)


def recortar(audio: np.ndarray) -> np.ndarray:
    """Evita saturación sin reescalar la señal."""
    return np.clip(audio, -1.0, 1.0)
