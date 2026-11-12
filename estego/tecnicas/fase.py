import numpy as np
import soundfile as sf


def texto_a_bits(texto):
    return ''.join(format(ord(c), '08b') for c in texto)

def bits_a_texto(binario):
    caracteres = []
    for i in range(0, len(binario), 8):
        byte = binario[i:i+8]
        if len(byte) < 8:
            break
        caracteres.append(chr(int(byte, 2)))
    return ''.join(caracteres)


def _banda(seg, fs, f_min, f_max):
    """Índices de los bins de la FFT que quedan entre f_min y f_max (Hz)."""
    k0 = int(round(f_min * seg / fs))
    k1 = int(round(f_max * seg / fs))
    return k0, k1

def encriptar_fase(texto, ruta_audio_original, ruta_audio_salida,
                   seg=4096, f_min=1000, f_max=3000):
    audio, fs = sf.read(ruta_audio_original, dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]

    bits = texto_a_bits(texto + "###END###")
    if len(bits) * seg > len(audio):
        raise ValueError(f"Audio muy corto: necesitas {len(bits)*seg} muestras y hay {len(audio)}.")

    k0, k1 = _banda(seg, fs, f_min, f_max)
    audio_stego = np.copy(audio)

    for i, bit in enumerate(bits):
        s = audio[i*seg:(i+1)*seg]
        X = np.fft.rfft(s)

        magnitud = np.abs(X[k0:k1])
        fase = np.pi/2 if bit == '1' else -np.pi/2

        # misma magnitud, fase nueva
        X[k0:k1] = magnitud * np.exp(1j * fase)

        audio_stego[i*seg:(i+1)*seg] = np.fft.irfft(X, n=seg)

    audio_stego /= max(1.0, np.max(np.abs(audio_stego)))
    sf.write(ruta_audio_salida, audio_stego, fs)
    print(f"Mensaje de {len(texto)} caracteres ocultado por fase en '{ruta_audio_salida}'.")

def extraer_bits_fase(audio, n_bits, seg, fs, f_min, f_max):
    k0, k1 = _banda(seg, fs, f_min, f_max)
    bits = []
    for i in range(n_bits):
        s = audio[i*seg:(i+1)*seg]
        fases = np.angle(np.fft.rfft(s)[k0:k1])
        votos = np.sum(np.sign(fases))        # votación mayoritaria entre todos los bins
        bits.append('1' if votos > 0 else '0')
    return ''.join(bits)

def desencriptar_fase(ruta_audio_stego, seg=4096, f_min=1000, f_max=3000):
    audio, fs = sf.read(ruta_audio_stego, dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]

    n_bits = len(audio) // seg
    bits = extraer_bits_fase(audio, n_bits, seg, fs, f_min, f_max)

    texto = bits_a_texto(bits)
    if "###END###" in texto:
        return texto.split("###END###")[0]
    return texto

encriptar_fase("ki onda", "pruebas/audio_final.wav", "pruebas/Prueba1_fase.wav")
print(desencriptar_fase("pruebas/Prueba1_fase.wav"))