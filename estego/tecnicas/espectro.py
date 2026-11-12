import numpy as np
import soundfile as sf

# Se debe hacer un utils para texto a bits o audio mono 


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


def generar_pn(seg, clave):
    """Secuencia pseudoaleatoria de +1/-1. La clave (semilla) es secreta y compartida."""
    return np.random.default_rng(clave).choice([-1.0, 1.0], size=seg)

def encriptar_espectro(texto, ruta_audio_original, ruta_audio_salida,
                       seg=4096, alfa=0.02, clave=1234):
    audio, fs = sf.read(ruta_audio_original, dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]

    bits = texto_a_bits(texto + "###END###")
    if len(bits) * seg > len(audio):
        raise ValueError(f"Audio muy corto: necesitas {len(bits)*seg} muestras y hay {len(audio)}.")

    pn = generar_pn(seg, clave)
    audio_stego = np.copy(audio)

    for i, bit in enumerate(bits):
        signo = 1.0 if bit == '1' else -1.0
        audio_stego[i*seg:(i+1)*seg] += alfa * signo * pn

    audio_stego /= max(1.0, np.max(np.abs(audio_stego)))
    sf.write(ruta_audio_salida, audio_stego, fs)
    print(f"Mensaje de {len(texto)} caracteres ocultado por espectro ensanchado en '{ruta_audio_salida}'.")

def extraer_bits_espectro(audio, n_bits, seg, clave):
    pn = generar_pn(seg, clave)
    bits = []
    for i in range(n_bits):
        s = audio[i*seg:(i+1)*seg]
        correlacion = np.dot(s, pn)          # el "despreading"
        bits.append('1' if correlacion > 0 else '0')
    return ''.join(bits)

def desencriptar_espectro(ruta_audio_stego, seg=4096, clave=1234):
    audio, fs = sf.read(ruta_audio_stego, dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]

    n_bits = len(audio) // seg               # lee todos los segmentos posibles
    bits = extraer_bits_espectro(audio, n_bits, seg, clave)

    texto = bits_a_texto(bits)
    if "###END###" in texto:
        return texto.split("###END###")[0]
    return texto

encriptar_espectro("ki onda", "pruebas/audio_final.wav", "pruebas/Prueba1_ss.wav", alfa=0.02)
print(desencriptar_espectro("pruebas/Prueba1_ss.wav"))