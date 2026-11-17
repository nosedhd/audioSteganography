"""Funciones comunes para evaluar una técnica después de un canal con pérdida."""

import inspect
from collections.abc import Callable, Iterable

import numpy as np

from estego.metricas import MetricasFiabilidad, evaluar_prueba, normalizar_y_alinear


def evaluar_audio_recibido(
    bits_originales: Iterable[int] | str,
    audio_original: np.ndarray,
    audio_stego: np.ndarray,
    audio_recibido: np.ndarray,
    fs: int,
    extraer: Callable[..., str],
    *,
    muestras_por_bit: int | None = None,
    alinear_audio: bool = True,
    fs_recibido: int | None = None,
    **parametros_extraer,
) -> MetricasFiabilidad:
    """Alinea, extrae y calcula métricas para un audio recibido."""
    bits = bits_originales if isinstance(bits_originales, str) else list(bits_originales)
    n_bits = len(bits)
    fs_recibido = fs if fs_recibido is None else fs_recibido
    recibido = audio_recibido

    if alinear_audio:
        recibido = normalizar_y_alinear(
            audio_stego,
            recibido,
            fs_referencia=fs,
            fs_recibido=fs_recibido,
        )
        if np.issubdtype(audio_stego.dtype, np.integer):
            info = np.iinfo(audio_stego.dtype)
            recibido = np.clip(np.rint(recibido), info.min, info.max).astype(audio_stego.dtype)
        elif np.issubdtype(audio_stego.dtype, np.floating):
            recibido = recibido.astype(audio_stego.dtype)

    sig = inspect.signature(extraer)
    if "fs" in sig.parameters and "fs" not in parametros_extraer:
        parametros_extraer["fs"] = fs

    bits_recuperados = extraer(recibido, n_bits, **parametros_extraer)
    return evaluar_prueba(
        bits_originales=bits,
        bits_recuperados=bits_recuperados,
        audio_original=audio_original,
        audio_stego=audio_stego,
        fs=fs,
        muestras_por_bit=muestras_por_bit,
    )


def imprimir_resultado(nombre: str, resultado: MetricasFiabilidad) -> None:
    """Imprime las métricas de una prueba de forma legible."""
    print(f"\n{nombre}")
    for clave, valor in resultado.como_dict().items():
        print(f"{clave}: {valor}")
