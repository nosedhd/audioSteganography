"""Esteganografía mediante codificación de fase."""

from collections.abc import Iterable

import numpy as np

from estego.utils import a_mono, bits_array, normalizar_portador, recortar

SEGMENTO = 4096


def _banda(seg: int, fs: int, f_min: int, f_max: int) -> tuple[int, int]:
    k0 = int(round(f_min * seg / fs))
    k1 = int(round(f_max * seg / fs))
    if not 0 <= k0 < k1 <= seg // 2 + 1:
        raise ValueError("La banda de frecuencias no es válida.")
    return k0, k1


def ocultar(
    audio: np.ndarray,
    bits: Iterable[int] | str,
    *,
    fs: int = 44100,
    seg: int = SEGMENTO,
    f_min: int = 1000,
    f_max: int = 3000,
) -> np.ndarray:
    """Oculta un bit por segmento modificando la fase de una banda."""
    if fs <= 0 or seg <= 0:
        raise ValueError("fs y seg deben ser positivos.")
    muestras = normalizar_portador(audio)
    bits_vector = bits_array(bits)
    if bits_vector.size * seg > muestras.size:
        raise ValueError("El audio no tiene capacidad para el mensaje.")
    k0, k1 = _banda(seg, fs, f_min, f_max)
    for i, bit in enumerate(bits_vector):
        inicio = i * seg
        bloque = muestras[inicio : inicio + seg]
        espectro = np.fft.rfft(bloque)
        fase = np.pi / 2 if bit else -np.pi / 2
        espectro[k0:k1] = np.abs(espectro[k0:k1]) * np.exp(1j * fase)
        muestras[inicio : inicio + seg] = np.fft.irfft(espectro, n=seg)
    return recortar(muestras)


def extraer(
    audio: np.ndarray,
    n_bits: int,
    *,
    fs: int = 44100,
    seg: int = SEGMENTO,
    f_min: int = 1000,
    f_max: int = 3000,
) -> str:
    """Extrae exactamente ``n_bits`` por votación de fase."""
    muestras = a_mono(audio)
    if n_bits < 0 or n_bits * seg > muestras.size:
        raise ValueError("n_bits excede la capacidad del audio.")
    k0, k1 = _banda(seg, fs, f_min, f_max)
    bits = []
    for i in range(n_bits):
        bloque = muestras[i * seg : (i + 1) * seg]
        fases = np.angle(np.fft.rfft(bloque)[k0:k1])
        bits.append("1" if np.sum(np.sign(fases)) > 0 else "0")
    return "".join(bits)


if __name__ == "__main__":
    import soundfile as sf

    audio, fs = sf.read("pruebas/audios/original.wav", dtype="float32")
    bits = "01010101"
    audio_stego = ocultar(audio, bits, fs=fs)
    sf.write("pruebas/audios/stego_fase.wav", audio_stego, fs)
    print(extraer(audio_stego, len(bits), fs=fs))
