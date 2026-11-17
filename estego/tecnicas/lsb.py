"""Esteganografía LSB sobre audio PCM entero."""

from collections.abc import Iterable

import numpy as np

from estego.utils import a_mono, bits_array, normalizar_lsb


def ocultar(audio: np.ndarray, bits: Iterable[int] | str) -> np.ndarray:
    """Oculta bits en las muestras menos significativas del portador."""
    muestras = normalizar_lsb(audio)
    bits_vector = bits_array(bits)
    if bits_vector.size > muestras.size:
        raise ValueError("El audio no tiene capacidad para el mensaje.")
    if not np.issubdtype(muestras.dtype, np.integer):
        raise TypeError("LSB requiere muestras de audio enteras.")
    resultado = muestras.copy()
    resultado[: bits_vector.size] = (
        resultado[: bits_vector.size] & ~np.array(1, dtype=muestras.dtype)
    ) | bits_vector.astype(muestras.dtype)
    return resultado


def extraer(audio: np.ndarray, n_bits: int) -> str:
    """Extrae exactamente ``n_bits`` bits de las muestras del portador."""
    muestras = a_mono(audio)
    if n_bits < 0 or n_bits > muestras.size:
        raise ValueError("n_bits excede la capacidad del audio.")
    if not np.issubdtype(muestras.dtype, np.integer):
        raise TypeError("LSB requiere muestras de audio enteras.")
    return "".join(str(int(muestra) & 1) for muestra in muestras[:n_bits])


if __name__ == "__main__":
    import soundfile as sf

    audio, fs = sf.read("pruebas/audios/original.wav", dtype="int16")
    mensaje = "ki ondá"
    bits = "".join(format(byte, "08b") for byte in mensaje.encode("utf-8"))
    audio_stego = ocultar(audio, bits)
    sf.write("pruebas/audios/stego_lsb.wav", audio_stego, fs)
    print(bits_array(extraer(audio_stego, len(bits))).tolist())
    


