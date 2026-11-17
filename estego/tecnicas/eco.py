"""Esteganografía por eco y análisis cepstral."""

from collections.abc import Iterable

import numpy as np

from estego.utils import a_mono, bits_array, normalizar_portador, recortar

SEGMENTO = 4096


def ocultar(
    audio: np.ndarray,
    bits: Iterable[int] | str,
    *,
    seg: int = SEGMENTO,
    d0: int = 100,
    d1: int = 150,
    alfa: float = 0.1,
) -> np.ndarray:
    """Oculta un bit por segmento usando uno de dos retardos de eco."""
    if seg <= max(d0, d1) or alfa < 0:
        raise ValueError("Parámetros de eco inválidos.")
    muestras = normalizar_portador(audio)
    bits_vector = bits_array(bits)
    if bits_vector.size * seg > muestras.size:
        raise ValueError("El audio no tiene capacidad para el mensaje.")
    for i, bit in enumerate(bits_vector):
        inicio = i * seg
        segmento = muestras[inicio : inicio + seg].copy()
        delay = d1 if bit else d0
        eco = np.zeros_like(segmento)
        eco[delay:] = segmento[:-delay] * alfa
        muestras[inicio : inicio + seg] = segmento + eco
    return recortar(muestras)


def extraer(
    audio: np.ndarray,
    n_bits: int,
    *,
    seg: int = SEGMENTO,
    d0: int = 100,
    d1: int = 150,
) -> str:
    """Extrae exactamente ``n_bits`` mediante el pico cepstral."""
    muestras = a_mono(audio)
    if n_bits < 0 or n_bits * seg > muestras.size:
        raise ValueError("n_bits excede la capacidad del audio.")
    bits = []
    for i in range(n_bits):
        segmento = muestras[i * seg : (i + 1) * seg]
        ventana = segmento * np.hanning(len(segmento))
        cepstrum = np.fft.irfft(np.log(np.abs(np.fft.rfft(ventana)) + 1e-10))
        cepstrum -= np.convolve(cepstrum, np.ones(31) / 31, mode="same")
        bits.append("0" if cepstrum[d0] > cepstrum[d1] else "1")
    return "".join(bits)


if __name__ == "__main__":
    import soundfile as sf

    audio, fs = sf.read("pruebas/audios/original.wav", dtype="float32")
    bits = "01010101"
    audio_stego = ocultar(audio, bits)
    sf.write("pruebas/audios/stego_eco.wav", audio_stego, fs)
    print(extraer(audio_stego, len(bits)))
