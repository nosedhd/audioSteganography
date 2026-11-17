"""Esteganografía por espectro ensanchado."""

from collections.abc import Iterable

import numpy as np

from estego.utils import a_mono, bits_array, normalizar_portador, recortar

SEGMENTO = 4096


def generar_pn(seg: int, clave: int) -> np.ndarray:
    """Genera una secuencia pseudoaleatoria reproducible de +1/-1."""
    return np.random.default_rng(clave).choice([-1.0, 1.0], size=seg)


def ocultar(
    audio: np.ndarray,
    bits: Iterable[int] | str,
    *,
    seg: int = SEGMENTO,
    alfa: float = 0.02,
    clave: int = 1234,
) -> np.ndarray:
    """Oculta un bit por segmento mediante modulación PN."""
    if seg <= 0 or alfa < 0:
        raise ValueError("Parámetros de espectro inválidos.")
    muestras = normalizar_portador(audio)
    bits_vector = bits_array(bits)
    if bits_vector.size * seg > muestras.size:
        raise ValueError("El audio no tiene capacidad para el mensaje.")
    pn = generar_pn(seg, clave)
    for i, bit in enumerate(bits_vector):
        signo = 1.0 if bit else -1.0
        inicio = i * seg
        muestras[inicio : inicio + seg] += alfa * signo * pn
    return recortar(muestras)


def extraer(
    audio: np.ndarray,
    n_bits: int,
    *,
    seg: int = SEGMENTO,
    clave: int = 1234,
) -> str:
    """Extrae exactamente ``n_bits`` por correlación con la secuencia PN."""
    muestras = a_mono(audio)
    if n_bits < 0 or n_bits * seg > muestras.size:
        raise ValueError("n_bits excede la capacidad del audio.")
    pn = generar_pn(seg, clave)
    return "".join(
        "1" if np.dot(muestras[i * seg : (i + 1) * seg], pn) > 0 else "0"
        for i in range(n_bits)
    )


if __name__ == "__main__":
    import soundfile as sf

    audio, fs = sf.read("pruebas/audios/original.wav", dtype="float32")
    bits = "01010101"
    audio_stego = ocultar(audio, bits)
    sf.write("pruebas/audios/stego_espectro.wav", audio_stego, fs)
    print(extraer(audio_stego, len(bits)))
