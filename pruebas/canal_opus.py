"""Evaluación automatizada y reproducible del canal Opus vía FFmpeg (12, 16, 24 y 32 kbps)
contrastado con WhatsApp real, con intervalos de confianza de Wilson para la BER (1024 bits).
"""

from pathlib import Path
import argparse
import numpy as np
import soundfile as sf

from estego.canales import simular_canal_opus
from estego.metricas import evaluar_prueba, normalizar_y_alinear
from estego.tecnicas import eco, espectro, fase, lsb
from estego.utils import normalizar_lsb, normalizar_portador

BITRATES_OPUS = [12, 16, 24, 32]
TECNICAS = {
    "lsb": (lsb, 1),
    "eco": (eco, eco.SEGMENTO),
    "espectro": (espectro, espectro.SEGMENTO),
    "fase": (fase, fase.SEGMENTO),
}


def evaluar_opus_benchmark(
    n_bits: int = 1024,
    nivel_ci: float = 0.95,
    metodo_ci: str = "wilson",
    salida_txt: Path = Path("Resultados/comparativa_opus_vs_whatsapp.txt"),
) -> list[dict]:
    salida_txt.parent.mkdir(parents=True, exist_ok=True)
    orig_path = Path("pruebas/audios/original.wav")
    if not orig_path.exists():
        raise FileNotFoundError(f"No se encontró {orig_path}")

    fs = 48000
    orig_f, _ = sf.read(orig_path, dtype="float32")
    orig_i, _ = sf.read(orig_path, dtype="int16")

    # Asegurar que el audio tenga capacidad suficiente para n_bits
    needed = n_bits * 4096
    repeats = int(np.ceil(needed / len(orig_f)))
    orig_f_long = np.tile(orig_f, (repeats, 1))[: needed + 4096]
    orig_i_long = np.tile(orig_i, (repeats, 1))[: needed + 4096]

    orig_f_norm = normalizar_portador(orig_f_long)
    orig_i_norm = normalizar_lsb(orig_i_long)

    # Secuencia binaria reproducible de n_bits (ej: 1024 bits)
    bits = "".join(str(b) for b in np.random.default_rng(2026).integers(0, 2, size=n_bits))

    print("\n" + "=" * 115)
    print(f"BENCHMARK OPUS VÍA FFMPEG (12, 16, 24, 32 kbps) vs WHATSAPP REAL ({n_bits} BITS - IC {int(nivel_ci*100)}% {metodo_ci.upper()})")
    print("=" * 115)
    print(f"{'Canal':<16} | {'Técnica':<10} | {'Tasa (kbps)':<11} | {'BER':<8} | {'IC 95% Wilson':<18} | {'Accuracy':<8} | {'Exacta':<7} | {'SNR (dB)':<9} | {'Tasa Ef (bps)'}")
    print("-" * 115)

    resultados = []
    lineas_txt = [
        "=" * 115,
        f"BENCHMARK COMPARATIVO: CÓDEC OPUS (12, 16, 24, 32 kbps) vs WHATSAPP REAL",
        f"Secuencia de prueba: {n_bits} bits pseudoaleatorios | Intervalo de Confianza: {int(nivel_ci*100)}% {metodo_ci.title()}",
        "=" * 115,
        f"{'Canal':<16} | {'Técnica':<10} | {'Tasa (kbps)':<11} | {'BER':<8} | {'IC 95% Wilson':<18} | {'Accuracy':<8} | {'Exacta':<7} | {'SNR (dB)':<9} | {'Tasa Ef (bps)'}",
        "-" * 115,
    ]

    for tec_nombre, (tecnica, m_bit) in TECNICAS.items():
        es_lsb = (tec_nombre == "lsb")
        audio_carrier = orig_i_long if es_lsb else orig_f_long
        audio_ref_norm = orig_i_norm if es_lsb else orig_f_norm

        # 1. Generar audio estego con los n_bits
        if tec_nombre == "lsb":
            stego = lsb.ocultar(audio_carrier, bits)
        elif tec_nombre == "eco":
            stego = eco.ocultar(audio_carrier, bits, alfa=0.15)
        elif tec_nombre == "espectro":
            stego = espectro.ocultar(audio_carrier, bits, clave=1234, alfa=0.03)
        elif tec_nombre == "fase":
            stego = fase.ocultar(audio_carrier, bits, fs=fs)

        # 2. Evaluar cada bitrate en Opus
        for br in BITRATES_OPUS:
            canal_nombre = f"Opus {br}k"
            dtype_read = "int16" if es_lsb else "float32"
            rec, fs_r = simular_canal_opus(stego, fs=fs, bitrate_kbps=br, dtype=dtype_read)

            rec_al = normalizar_y_alinear(stego, rec, fs, fs_r)
            if es_lsb:
                rec_al = np.clip(np.round(rec_al), -32768, 32767).astype(np.int16)
            else:
                rec_al = rec_al.astype(np.float32)

            if tec_nombre == "lsb":
                rec_bits = lsb.extraer(rec_al, n_bits)
            elif tec_nombre == "eco":
                rec_bits = eco.extraer(rec_al, n_bits)
            elif tec_nombre == "espectro":
                rec_bits = espectro.extraer(rec_al, n_bits, clave=1234)
            elif tec_nombre == "fase":
                rec_bits = fase.extraer(rec_al, n_bits, fs=fs)

            res = evaluar_prueba(
                bits, rec_bits, audio_ref_norm, stego, fs,
                muestras_por_bit=m_bit, nivel_confianza=nivel_ci, metodo_ci=metodo_ci
            )

            d = {
                "canal": canal_nombre,
                "tecnica": tec_nombre,
                "bitrate": f"{br}k",
                "ber": res.ber,
                "ci": res.ber_ci_str,
                "acc": res.accuracy_bits,
                "exacta": res.recuperacion_exacta,
                "snr": res.snr_db,
                "tasa_ef": res.tasa_informacion_efectiva_bps,
            }
            resultados.append(d)

            fila = (
                f"{canal_nombre:<16} | {tec_nombre:<10} | {f'{br} kbps':<11} | {res.ber:<8.4f} | "
                f"{res.ber_ci_str:<18} | {res.accuracy_bits:<8.4f} | {str(res.recuperacion_exacta):<7} | "
                f"{res.snr_db:<9.2f} | {res.tasa_informacion_efectiva_bps:<.2f}"
            )
            print(fila)
            lineas_txt.append(fila)

        # 3. Contraste con WhatsApp real (archivo pregrabado)
        wp_path = Path(f"pruebas/audios/whatsapp/stego_{tec_nombre}_whatsapp.ogg")
        if wp_path.exists():
            canal_nombre = "WhatsApp (Real)"
            dtype_read = "int16" if es_lsb else "float32"
            rec_wp, fs_wp = sf.read(wp_path, dtype=dtype_read)
            rec_wp_al = normalizar_y_alinear(stego, rec_wp, fs, fs_wp)
            if es_lsb:
                rec_wp_al = np.clip(np.round(rec_wp_al), -32768, 32767).astype(np.int16)
            else:
                rec_wp_al = rec_wp_al.astype(np.float32)

            # Para el archivo pregrabado, evaluar con la capacidad que contiene (o n_bits)
            n_eval = min(n_bits, len(rec_wp_al) // m_bit)
            if tec_nombre == "lsb":
                rec_bits = lsb.extraer(rec_wp_al, n_eval)
            elif tec_nombre == "eco":
                rec_bits = eco.extraer(rec_wp_al, n_eval)
            elif tec_nombre == "espectro":
                rec_bits = espectro.extraer(rec_wp_al, n_eval, clave=1234)
            elif tec_nombre == "fase":
                rec_bits = fase.extraer(rec_wp_al, n_eval, fs=fs)

            res = evaluar_prueba(
                bits[:n_eval], rec_bits, audio_ref_norm, stego, fs,
                muestras_por_bit=m_bit, nivel_confianza=nivel_ci, metodo_ci=metodo_ci
            )
            fila = (
                f"{canal_nombre:<16} | {tec_nombre:<10} | {'~20-24k VBR':<11} | {res.ber:<8.4f} | "
                f"{res.ber_ci_str:<18} | {res.accuracy_bits:<8.4f} | {str(res.recuperacion_exacta):<7} | "
                f"{res.snr_db:<9.2f} | {res.tasa_informacion_efectiva_bps:<.2f}"
            )
            print(fila)
            lineas_txt.append(fila)

        print("-" * 115)
        lineas_txt.append("-" * 115)

    print("=" * 115)
    lineas_txt.extend([
        "=" * 115,
        "",
        "NOTAS METODOLÓGICAS PARA LA EXPOSICIÓN:",
        "- Opus es el códec que WhatsApp utiliza internamente para notas de voz a 48 kHz (VBR entre 16 y 24 kbps).",
        "- Las pruebas de Opus con FFmpeg son deterministas y 100% reproducibles en cualquier ordenador.",
        "- WhatsApp Real incluye el procesamiento en la nube de Meta (normalización de volumen AGC y empaquetado OGG).",
        "- El intervalo de confianza de Wilson al 95% garantiza rigor estadístico formal para la BER observada.",
    ])
    salida_txt.write_text("\n".join(lineas_txt), encoding="utf-8")
    print(f"\n[OK] Reporte completo guardado en: {salida_txt.resolve()}\n")
    return resultados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evalúa Opus a diferentes bitrates vs WhatsApp con intervalos de confianza.")
    parser.add_argument("--n-bits", type=int, default=1024, help="Número de bits a evaluar (default: 1024).")
    parser.add_argument("--metodo-ci", choices=("wilson", "clopper-pearson"), default="wilson", help="Método para el IC.")
    args = parser.parse_args()
    evaluar_opus_benchmark(n_bits=args.n_bits, metodo_ci=args.metodo_ci)
