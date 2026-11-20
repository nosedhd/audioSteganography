"""Simulación y procesamiento de canales de transmisión acústicos y digitales con pérdida."""

import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


def simular_canal_opus(
    audio: np.ndarray,
    fs: int = 48000,
    bitrate_kbps: int = 16,
    dtype: str = "float32",
) -> tuple[np.ndarray, int]:
    """Comprime y descomprime audio usando el códec Opus vía FFmpeg de forma determinista y reproducible.

    Parámetros:
        audio: Arreglo numpy del audio de entrada.
        fs: Frecuencia de muestreo original (default: 48000 Hz).
        bitrate_kbps: Tasa de bits en kbps (ej: 12, 16, 24, 32).
        dtype: Tipo de datos al leer el audio decodificado ('float32' o 'int16').

    Retorna:
        (audio_decodificado, fs_decodificado)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_wav_in = Path(tmpdir) / "in.wav"
        tmp_opus = Path(tmpdir) / "compressed.opus"

        # Guardar audio de entrada
        write_dtype = "int16" if np.issubdtype(audio.dtype, np.integer) else "float32"
        sf.write(str(tmp_wav_in), audio, fs, subtype="PCM_16" if write_dtype == "int16" else "FLOAT")

        # Comprimir con FFmpeg a Opus con la tasa indicada
        cmd = [
            "ffmpeg",
            "-y",
            "-v", "error",
            "-i", str(tmp_wav_in),
            "-c:a", "libopus",
            "-b:a", f"{bitrate_kbps}k",
            "-vbr", "on",
            "-ar", str(fs),
            str(tmp_opus),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Error al codificar en Opus con FFmpeg: {res.stderr}")

        # Leer audio resultante
        audio_rec, fs_rec = sf.read(str(tmp_opus), dtype=dtype)
        return audio_rec, fs_rec


def simular_canal_mp3(
    audio: np.ndarray,
    fs: int = 48000,
    bitrate_kbps: int = 64,
    dtype: str = "float32",
) -> tuple[np.ndarray, int]:
    """Comprime y descomprime audio usando el códec MP3 vía FFmpeg.

    Parámetros:
        audio: Arreglo numpy del audio de entrada.
        fs: Frecuencia de muestreo original (default: 48000 Hz).
        bitrate_kbps: Tasa de bits en kbps (ej: 64, 128, 192, 320).
        dtype: Tipo de datos al leer el audio decodificado ('float32' o 'int16').

    Retorna:
        (audio_decodificado, fs_decodificado)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_wav_in = Path(tmpdir) / "in.wav"
        tmp_mp3 = Path(tmpdir) / "compressed.mp3"

        write_dtype = "int16" if np.issubdtype(audio.dtype, np.integer) else "float32"
        sf.write(str(tmp_wav_in), audio, fs, subtype="PCM_16" if write_dtype == "int16" else "FLOAT")

        cmd = [
            "ffmpeg",
            "-y",
            "-v", "error",
            "-i", str(tmp_wav_in),
            "-c:a", "libmp3lame",
            "-b:a", f"{bitrate_kbps}k",
            "-ar", str(fs),
            str(tmp_mp3),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Error al codificar en MP3 con FFmpeg: {res.stderr}")

        audio_rec, fs_rec = sf.read(str(tmp_mp3), dtype=dtype)
        return audio_rec, fs_rec
