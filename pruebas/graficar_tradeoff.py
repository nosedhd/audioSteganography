"""Genera la gráfica de compromiso (Trade-off) entre Imperceptibilidad (SNR)
y Robustez (BER) frente al factor de inserción (alfa) sobre MP3 a 64 kbps.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

from estego.canales import simular_canal_mp3
from estego.metricas import evaluar_prueba, normalizar_y_alinear
from estego.tecnicas import eco, espectro
from estego.utils import normalizar_portador


def generar_grafica_tradeoff(
    n_bits: int = 256,
    salida_png: Path = Path("Resultados/grafica_ber_vs_alfa.png"),
) -> None:
    salida_png.parent.mkdir(parents=True, exist_ok=True)
    fs = 48000
    orig_path = Path("pruebas/audios/original.wav")
    if not orig_path.exists():
        raise FileNotFoundError(f"No se encontró {orig_path}")

    orig_f, _ = sf.read(orig_path, dtype="float32")

    # Asegurar que el audio tenga capacidad suficiente para n_bits * 4096 muestras
    needed = n_bits * 4096
    repeats = int(np.ceil(needed / len(orig_f)))
    orig_long = np.tile(orig_f, (repeats, 1))[: needed + 4096]
    orig_norm = normalizar_portador(orig_long)

    # Secuencia reproducible de bits
    bits = "".join(str(b) for b in np.random.default_rng(2026).integers(0, 2, size=n_bits))

    # Valores de alfa a evaluar
    alfas_espectro = [0.005, 0.01, 0.02, 0.03, 0.05, 0.08]
    alfas_eco = [0.02, 0.05, 0.08, 0.10, 0.15, 0.20]

    # Datos para Espectro
    ber_esp = []
    ber_ci_esp = []  # [[low_err, high_err], ...]
    snr_esp = []

    print("\n" + "=" * 80)
    print("EJECUTANDO BARRIDO DE ALFA EN MP3 A 64 kbps (CANAL AGRESIVO)")
    print("=" * 80)
    print("\n--- 1. Espectro Ensanchado (DSSS) ---")
    for a in alfas_espectro:
        stego = espectro.ocultar(orig_long, bits, clave=1234, alfa=a)
        rec, fs_r = simular_canal_mp3(stego, fs, bitrate_kbps=64)
        rec_al = normalizar_y_alinear(stego, rec, fs, fs_r).astype(np.float32)
        rec_bits = espectro.extraer(rec_al, n_bits, clave=1234)
        res = evaluar_prueba(bits, rec_bits, orig_norm, stego, fs, muestras_por_bit=4096)

        ber_esp.append(res.ber)
        err_low = res.ber - res.ber_ci_low
        err_high = res.ber_ci_high - res.ber
        ber_ci_esp.append((err_low, err_high))
        snr_esp.append(res.snr_db)
        print(f"alfa={a:<5.3f} | BER={res.ber:.4f} {res.ber_ci_str} | SNR={res.snr_db:.2f} dB")

    # Datos para Eco
    ber_eco_val = []
    ber_ci_eco = []
    snr_eco_val = []

    print("\n--- 2. Eco Hiding ---")
    for a in alfas_eco:
        stego = eco.ocultar(orig_long, bits, alfa=a)
        rec, fs_r = simular_canal_mp3(stego, fs, bitrate_kbps=64)
        rec_al = normalizar_y_alinear(stego, rec, fs, fs_r).astype(np.float32)
        rec_bits = eco.extraer(rec_al, n_bits)
        res = evaluar_prueba(bits, rec_bits, orig_norm, stego, fs, muestras_por_bit=4096)

        ber_eco_val.append(res.ber)
        err_low = res.ber - res.ber_ci_low
        err_high = res.ber_ci_high - res.ber
        ber_ci_eco.append((err_low, err_high))
        snr_eco_val.append(res.snr_db)
        print(f"alfa={a:<5.3f} | BER={res.ber:.4f} {res.ber_ci_str} | SNR={res.snr_db:.2f} dB")

    # Configuración gráfica con Matplotlib
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Panel 1: Espectro Ensanchado
    color_ber = "#d9534f"  # Rojo
    color_snr = "#0275d8"  # Azul

    yerr_esp = np.array(ber_ci_esp).T
    ax1.errorbar(
        alfas_espectro, ber_esp, yerr=yerr_esp, fmt="o-", color=color_ber,
        capsize=4, capthick=1.5, linewidth=2, label="BER (Wilson 95%)"
    )
    ax1.set_xlabel("Factor de Inserción (alfa)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Bit Error Rate (BER)", color=color_ber, fontsize=11, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor=color_ber)
    ax1.set_ylim(-0.02, 0.45)
    ax1.set_title("A. Espectro Ensanchado (DSSS) en MP3 64 kbps", fontsize=12, fontweight="bold")

    ax1_twin = ax1.twinx()
    ax1_twin.plot(alfas_espectro, snr_esp, "s--", color=color_snr, linewidth=2, label="SNR (dB)")
    ax1_twin.set_ylabel("SNR (dB - Fidelidad)", color=color_snr, fontsize=11, fontweight="bold")
    ax1_twin.tick_params(axis="y", labelcolor=color_snr)
    ax1_twin.set_ylim(0, 35)
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Panel 2: Eco Hiding
    yerr_eco = np.array(ber_ci_eco).T
    ax2.errorbar(
        alfas_eco, ber_eco_val, yerr=yerr_eco, fmt="o-", color=color_ber,
        capsize=4, capthick=1.5, linewidth=2, label="BER (Wilson 95%)"
    )
    ax2.set_xlabel("Amplitud de Eco (alfa)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Bit Error Rate (BER)", color=color_ber, fontsize=11, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor=color_ber)
    ax2.set_ylim(-0.02, 0.55)
    ax2.set_title("B. Eco Hiding en MP3 64 kbps", fontsize=12, fontweight="bold")

    ax2_twin = ax2.twinx()
    ax2_twin.plot(alfas_eco, snr_eco_val, "s--", color=color_snr, linewidth=2, label="SNR (dB)")
    ax2_twin.set_ylabel("SNR (dB - Fidelidad)", color=color_snr, fontsize=11, fontweight="bold")
    ax2_twin.tick_params(axis="y", labelcolor=color_snr)
    ax2_twin.set_ylim(0, 40)
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.suptitle(
        "Compromiso de Esteganografía (Trade-off): Robustez (BER) vs Imperceptibilidad (SNR)",
        fontsize=14, fontweight="bold", y=1.02
    )
    plt.tight_layout()
    plt.savefig(str(salida_png), bbox_inches="tight")
    plt.close()

    print("\n" + "=" * 80)
    print(f"[OK] Gráfica generada exitosamente en: {salida_png.resolve()}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    generar_grafica_tradeoff()
