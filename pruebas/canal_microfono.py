"""Evaluación de una grabación acústica ya existente."""

from pathlib import Path

import numpy as np
import soundfile as sf

from estego.metricas import MetricasFiabilidad
if __package__:
    from .evaluar import evaluar_audio_recibido, imprimir_resultado
else:
    from evaluar import evaluar_audio_recibido, imprimir_resultado


def evaluar_microfono(
    bits_originales: str,
    audio_original: np.ndarray,
    audio_stego: np.ndarray,
    fs: int,
    extraer,
    *,
    ruta_audio_recibido: str | Path,
    dtype: str = "float32",
    muestras_por_bit: int | None = None,
    alinear_audio: bool = True,
    **parametros_extraer,
) -> MetricasFiabilidad:
    """Lee una grabación de parlante/micrófono y evalúa los bits recuperados."""
    recibido, fs_recibido = sf.read(ruta_audio_recibido, dtype=dtype)
    resultado = evaluar_audio_recibido(
        bits_originales,
        audio_original,
        audio_stego,
        recibido,
        fs,
        extraer,
        muestras_por_bit=muestras_por_bit,
        alinear_audio=alinear_audio,
        fs_recibido=fs_recibido,
        **parametros_extraer,
    )
    imprimir_resultado("Micrófono/parlante", resultado)
    return resultado
