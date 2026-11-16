from estego.metricas import (
    MetricasFiabilidad,
    alinear,
    evaluar_prueba,
    normalizar_audio,
    normalizar_y_alinear,
    tasa_recuperacion_exacta,
)
from soundfile import SoundFile as sf

__all__ = [
    "MetricasFiabilidad",
    "alinear",
    "evaluar_prueba",
    "normalizar_audio",
    "normalizar_y_alinear",
    "tasa_recuperacion_exacta",
]

audio_original, fs_original = sf.read("pruebas/Prueba1.wav", dtype="int16")
audio_stego, fs_stego = sf.read("pruebas/Prueba1_encriptada.wav", dtype="int16")
audio_recibido, fs_recibido = sf.read("pruebas/Prueba1_recibida.mp3", dtype="int16")


audio_recuperado = normalizar_y_alinear(
    audio_original,
    audio_recibido,
    fs_referencia=44100,
    fs_recibido=44100,
)

resultado = evaluar_prueba(
    bits_originales="01010101",
    bits_recuperados="01000101",
    audio_original=audio_original,
    audio_stego=audio_stego,
    fs=44100,
)

print(resultado.como_dict())