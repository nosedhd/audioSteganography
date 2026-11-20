"""Script para evaluar automáticamente todos los audios en pruebas/audios."""

from pathlib import Path
import soundfile as sf
import numpy as np

from estego.tecnicas import eco, espectro, fase, lsb
from estego.utils import texto_a_bits, normalizar_portador, normalizar_lsb
from estego.metricas import evaluar_prueba, normalizar_y_alinear

CONFIGURACION_CANALES = [
    ("mp3", "mp3", "stego_{tec}_mp3.mp3"),
    ("whatsapp", "whatsapp", "stego_{tec}_whatsapp.ogg"),
    ("microfono", "microfono", "stego_{tec}_micro.ogg"),
]

TECNICAS = {
    "lsb": (lsb, 1),
    "eco": (eco, eco.SEGMENTO),
    "espectro": (espectro, espectro.SEGMENTO),
    "fase": (fase, fase.SEGMENTO),
}

MENSAJES = {
    "lsb": texto_a_bits("ki ondá"),
    "eco": "01010101",
    "espectro": "01010101",
    "fase": "01010101",
}


def evaluar_todos(canales=None) -> list[dict]:
    canales_a_evaluar = [
        conf for conf in CONFIGURACION_CANALES
        if canales is None or conf[0] in canales
    ]
    resultados = []

    print("\n" + "=" * 115)
    print(f"{'Canal':<12} | {'Técnica':<10} | {'BER':<8} | {'IC 95% Wilson':<18} | {'Accuracy':<8} | {'Exacta':<7} | {'SNR (dB)':<9} | {'Cap (bps)':<10} | {'Tasa Ef (bps)'}")
    print("-" * 115)

    for canal, subcarpeta, patron in canales_a_evaluar:
        for tec_nombre, (tecnica, muestras_por_bit) in TECNICAS.items():
            bits = MENSAJES[tec_nombre]
            dtype = "int16" if tec_nombre == "lsb" else "float32"

            orig_path = Path("pruebas/audios/original.wav")
            stego_path = Path(f"pruebas/audios/stego_{tec_nombre}.wav")
            rec_path = Path(f"pruebas/audios/{subcarpeta}") / patron.format(tec=tec_nombre)

            if not rec_path.exists():
                print(f"Advertencia: No se encontró {rec_path}")
                continue

            orig_ref, fs = sf.read(orig_path, dtype=dtype)
            stego, fs_s = sf.read(stego_path, dtype=dtype)
            rec, fs_r = sf.read(rec_path, dtype=dtype)

            # Normalizar referencia para SNR exacto
            if tec_nombre == "lsb":
                orig_ref = normalizar_lsb(orig_ref)
            else:
                orig_ref = normalizar_portador(orig_ref)

            # Alinear audio
            rec_al = normalizar_y_alinear(stego, rec, fs, fs_r)
            if tec_nombre == "lsb":
                info = np.iinfo(np.int16)
                rec_al = np.clip(np.rint(rec_al), info.min, info.max).astype(np.int16)
            else:
                rec_al = rec_al.astype(np.float32)

            # Extraer bits según técnica
            if tec_nombre == "lsb":
                rec_bits = lsb.extraer(rec_al, len(bits))
            elif tec_nombre == "eco":
                rec_bits = eco.extraer(rec_al, len(bits))
            elif tec_nombre == "espectro":
                rec_bits = espectro.extraer(rec_al, len(bits), clave=1234)
            elif tec_nombre == "fase":
                rec_bits = fase.extraer(rec_al, len(bits), fs=fs)

            res = evaluar_prueba(
                bits_originales=bits,
                bits_recuperados=rec_bits,
                audio_original=orig_ref,
                audio_stego=stego,
                fs=fs,
                muestras_por_bit=muestras_por_bit,
            )

            d = {
                "canal": canal,
                "tecnica": tec_nombre,
                "ber": res.ber,
                "accuracy_bits": res.accuracy_bits,
                "recuperacion_exacta": res.recuperacion_exacta,
                "snr_db": res.snr_db,
                "capacidad_bps": res.capacidad_bps,
                "tasa_informacion_efectiva_bps": res.tasa_informacion_efectiva_bps,
            }
            resultados.append(d)

            print(
                f"{canal:<12} | {tec_nombre:<10} | {res.ber:<8.4f} | {res.ber_ci_str:<18} | {res.accuracy_bits:<8.4f} | "
                f"{str(res.recuperacion_exacta):<7} | {res.snr_db:<9.2f} | {res.capacidad_bps:<10.1f} | "
                f"{res.tasa_informacion_efectiva_bps:<.2f}"
            )

    print("=" * 115 + "\n")
    return resultados


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evalúa todas las combinaciones de canales y técnicas.")
    parser.add_argument("--canal", choices=("mp3", "whatsapp", "microfono"), default=None, help="Evaluar un solo canal.")
    args = parser.parse_args()
    evaluar_todos(canales=[args.canal] if args.canal else None)
