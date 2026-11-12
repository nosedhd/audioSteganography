import soundfile as sf
import numpy as np

audio, fs = sf.read("pruebas/Prueba1.wav", dtype="int16")

def estereo_a_mono(audio):
    if audio.ndim > 1:          # si es estéreo, quedarse con un canal
        print("El audio es estéreo, se convertirá a mono.")
        audio = audio[:, 0]
    return audio

# Primero usamos texto

def encriptar_texto(texto, audio):
    texto_completo = texto + "###END###"
    # Convertir el texto a binario
    binario = ''.join(format(ord(c), '08b') for c in texto_completo)
    # Asegurarse de que el audio tenga suficiente capacidad para ocultar el mensaje
    if len(binario) > len(audio):
        raise ValueError("El audio no tiene suficiente capacidad para ocultar el mensaje.")
    # Crear una copia del audio para modificarlo
    audio_modificado = np.copy(estereo_a_mono(audio))
    print(audio_modificado)
    print("la nada misma")
    # Modificar los bits menos significativos del audio con los bits del mensaje
    for i in range(len(binario)):
        audio_modificado[i] = (audio_modificado[i] & ~1) | int(binario[i])
    sf.write("pruebas/Prueba1_encriptada.wav", audio_modificado, fs)


def desencriptar_texto(audio):
    # Extraer los bits menos significativos del audio
    audio = estereo_a_mono(audio)
    
    caracteres = []
    # Recorrer el audio en bloques de 8 bits para reconstruir los caracteres
    for i in range(0, len(audio), 8):
        if i + 8 > len(audio):
            break
        # Extraer el LSB de cada uno de los 8 elementos de audio
        byte_bits = ''.join(str(audio[i + j] & 1) for j in range(8))
        char = chr(int(byte_bits, 2))
        caracteres.append(char)
        
        # Comprobar si hemos alcanzado el final marcado por el delimitador
        texto_actual = ''.join(caracteres)
        if "###END###" in texto_actual:
            return texto_actual.split("###END###")[0]
            
    return ''.join(caracteres)

mensaje = "ki ondá"
encriptar_texto(mensaje, audio)

audio_encriptado, fs = sf.read("pruebas/Prueba1_encriptada.wav", dtype="int16")
texto_desencriptado = desencriptar_texto(audio_encriptado)
print("Texto desencriptado: " + texto_desencriptado)