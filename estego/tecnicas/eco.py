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

def encriptar_eco(texto, ruta_audio_original, ruta_audio_salida, d0=100, d1=150, alfa=0.1):
    # Cargar audio
    audio, fs = sf.read(ruta_audio_original, dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]  # Mono
    
    # Agregar delimitador al mensaje
    mensaje_completo = texto + "###END###"
    bits = texto_a_bits(mensaje_completo)
    num_bits = len(bits)
    
    # Definir tamaño de segmento por bit
    segment_size = len(audio) // num_bits
    if segment_size <= max(d0, d1):
        raise ValueError("El audio es demasiado corto para albergar este mensaje con los retrasos configurados.")
    
    audio_stego = np.copy(audio)
    
    for i, bit in enumerate(bits):
        inicio = i * segment_size
        fin = (i + 1) * segment_size
        segmento = audio[inicio:fin]
        
        # Crear el eco según el bit (0 o 1)
        delay = d0 if bit == '0' else d1
        eco = np.zeros_like(segmento)
        eco[delay:] = segmento[:-delay] * alfa
        
        # Mezclar el segmento original con el eco
        audio_stego[inicio:fin] = segmento + eco
        
    sf.write(ruta_audio_salida, audio_stego, fs)
    print(f"Mensaje de {len(texto)} caracteres ocultado mediante eco con éxito en '{ruta_audio_salida}'.")


def extraer_bits_eco(audio, n_bits, seg, d0, d1):
    bits = []
    for i in range(n_bits):
        s = audio[i*seg:(i+1)*seg]
        s = s * np.hanning(len(s))
        c = np.fft.irfft(np.log(np.abs(np.fft.rfft(s)) + 1e-10))
        # quitar la tendencia suave del cepstrum
        c = c - np.convolve(c, np.ones(31)/31, mode="same")
        bits.append('0' if c[d0] > c[d1] else '1')
    return ''.join(bits)

def desencriptar_eco(ruta_audio_stego, d0=100, d1=150):
    audio, fs = sf.read(ruta_audio_stego, dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]

    mensaje_prueba = "ki onda###END###"
    num_bits = len(mensaje_prueba) * 8
    seg = len(audio) // num_bits

    bits_recuperados = extraer_bits_eco(audio, num_bits, seg, d0, d1)

    texto_completo = bits_a_texto(bits_recuperados)
    if "###END###" in texto_completo:
        return texto_completo.split("###END###")[0]
    return texto_completo

# Prueba de funcionamiento
encriptar_eco("ki onda", "pruebas/Prueba1.wav", "pruebas/Prueba1_eco.wav",alfa=0.5)
mensaje_recuperado = desencriptar_eco("pruebas/Prueba1_eco.wav")
print("Texto recuperado por Eco (Cepstrum Adaptativo):", mensaje_recuperado)