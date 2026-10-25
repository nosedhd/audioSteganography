import soundfile as sf

audio, fs = sf.read("pruebas/Prueba1.wav", dtype="int16")

if audio.ndim > 1:          # si es estéreo, quedarse con un canal
    audio = audio[:, 0]

print(audio)