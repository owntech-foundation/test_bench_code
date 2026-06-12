import os
import ast
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import glob
import re

# Project Structure:
# (voir description plus haut)

# Directory configuration
simulations_folder = "PhaseShift"
excel_folder = "excel"
os.makedirs(excel_folder, exist_ok=True)

def traiter_dossier(path, folder):
    print(f"\n[Conversion] Folder {folder}")
    fichier_tension, fichier_courant = None, None

    for file in os.listdir(path):
        lf = file.lower()
        if "-voltage" in lf and file.endswith(".csv"):
            fichier_tension = os.path.join(path, file)
        elif "-current" in lf and file.endswith(".csv"):
            fichier_courant = os.path.join(path, file)

    if fichier_tension:
        try:
            with open(fichier_tension) as f:
                raw_str = f.read().strip()
                if raw_str.startswith("["):
                    raw = json.loads(raw_str)
                else:
                    df_tmp = pd.read_csv(fichier_tension, header=None)
                    if df_tmp.shape[0] == 1:
                        raw = json.loads(df_tmp.iloc[0, 0])
                    elif df_tmp.shape[1] == 1:
                        raw = df_tmp.iloc[:, 0].dropna().tolist()
                    else:
                        raise ValueError("Unrecognized format in voltage file")

            df_t = pd.DataFrame({"Voltage (V)": raw})
            out = os.path.join(excel_folder, f"{folder}_tension.xlsx")
            df_t.to_excel(out, index=False)
            print(f"  → Voltage exported: {out}")
        except Exception as e:
            print(f"  [ERROR] voltage {folder}: {e}")
    else:
        print("  [No voltage file found]")

    if fichier_courant:
        try:
            with open(fichier_courant) as f:
                raw_str = f.read().strip()
                if raw_str.startswith("["):
                    raw = json.loads(raw_str)
                else:
                    df_tmp = pd.read_csv(fichier_courant, header=None)
                    if df_tmp.shape[0] == 1:
                        raw = json.loads(df_tmp.iloc[0, 0])
                    elif df_tmp.shape[1] == 1:
                        raw = df_tmp.iloc[:, 0].dropna().tolist()
                    else:
                        raise ValueError("Unrecognized format in current file")

            df_c = pd.DataFrame({"Current (A)": raw})
            out = os.path.join(excel_folder, f"{folder}_courant.xlsx")
            df_c.to_excel(out, index=False)
            print(f"  → Current exported: {out}")
        except Exception as e:
            print(f"  [ERROR] current {folder}: {e}")
    else:
        print("  [No current file found]")

def process_voltage(vlevel, freq, all_data):
    print(f"\n========== PROCESSING {vlevel}V @ {freq}Hz ==========")
    base = os.path.dirname(os.path.abspath(__file__))

    cfg = json.load(open(os.path.join(base, "base-config.json")))
    TotalR, L = cfg["TotalR"], cfg["InductorL"]

    courant_file = os.path.join(excel_folder, f"Voltage_{vlevel}_{freq//1000}kHz_courant.xlsx")
    tension_file = os.path.join(excel_folder, f"Voltage_{vlevel}_{freq//1000}kHz_tension.xlsx")

    cour = pd.to_numeric(pd.read_excel(courant_file).iloc[:, 0], errors='coerce').dropna().reset_index(drop=True)
    tens = pd.to_numeric(pd.read_excel(tension_file).iloc[:, 0], errors='coerce').dropna().reset_index(drop=True)

    folder_name_with_freq = f"Voltage_{vlevel}_{freq//1000}kHz"
    base_phase_folder = os.path.join(base, "PhaseShift")

    folder_path = os.path.join(base_phase_folder, folder_name_with_freq)
    if not os.path.isdir(folder_path):
        print(f"  [ERROR] Folder {folder_name_with_freq} does not exist")
        return

    pattern = f"PhaseShift_Voltage_{vlevel}V_Freq{freq//1000}kHz.json"
    matches = glob.glob(os.path.join(folder_path, pattern))
    if not matches:
        print(f"  [ERROR] No PhaseShift file matching freq {freq}Hz found in {folder_path}")
        return

    phase_file = matches[0]
    result_file = os.path.join(folder_path, "results.json")

    pcfg = json.load(open(phase_file))
    nbI = pcfg["nbPointsI"]

    phases = pcfg.get("PhaseTab")
    if phases is None:
        phases = list(range(pcfg["PhaseInit"], pcfg["PhaseFinal"] + 1, pcfg["PhaseStep"]))

    if len(phases) < nbI:
        print(f"  [Warning] PhaseTab length {len(phases)} < nbPointsI {nbI}, adjusting nbI.")
        nbI = len(phases)
    else:
        phases = phases[:nbI]

    rdata = json.load(open(result_file))
    I_peak_list = [rdata.get(f"Data{i+1}", {}).get("2", {}).get("value", float("nan")) for i in range(nbI)]

    pts = min(len(cour), len(tens))
    valid = (pts // nbI) * nbI
    if valid == 0:
        print("  [ERROR] Not enough data")
        return

    cour, tens = cour[:valid], tens[:valid]
    seg = valid // nbI

    rows = []
    for i in range(nbI):
        I_vals = cour.iloc[i*seg:(i+1)*seg].values
        V_vals = tens.iloc[i*seg:(i+1)*seg].values
        I_moy = (I_vals * V_vals).sum() / V_vals.sum() if V_vals.sum() != 0 else float('nan')
        V_moy = V_vals.mean()
        P = I_moy * V_moy
        I_lim = (phases[i] / 180 * vlevel) / ((L * 1e-3) * 4 * freq)
        E_off = 0.25 * (P - I_lim**2 * TotalR) / freq
        rows.append({
            "Step": i+1,
            "Phase (°)": phases[i],
            "I_exp_avg (A)": I_moy,
            "V_avg (V)": V_moy,
            "P (W)": P,
            "E_off (J)": E_off,
            "I_peak (A)": I_peak_list[i]
        })

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    all_data.append((vlevel, df, freq))

    # === Sauvegarde CSV ===
    outdir = "sauvegarde"
    os.makedirs(outdir, exist_ok=True)
    excel_filename = os.path.join(outdir, f"data_{vlevel}V_{freq//1000}kHz.xlsx")
    df.to_excel(excel_filename, index=False)
    print(f"  → Données sauvegardées dans: {excel_filename}")


def plot_all_graphs(all_data, freq, ts):
    outdir = "sauvegarde"
    os.makedirs(outdir, exist_ok=True)
    print(f"\n[Graph] E_off vs I_peak")
    plt.figure(figsize=(10, 6))
    for v, df, _ in all_data:
        plt.plot(df["I_peak (A)"], df["E_off (J)"], marker='o', label=f"{v}V")
    plt.title(f"E_off vs I_peak @ {freq}Hz")
    plt.xlabel("I_peak (A)")
    plt.ylabel("E_off (J)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    fn = os.path.join(outdir, f"graph_Eoff_vs_Ipeak_{freq}Hz_{ts}.pdf")
    plt.savefig(fn)
    print(f"  → Saved: {fn}")

def plot_graphs_without_last_point(all_data, freq, ts):
    outdir = "sauvegarde"
    print(f"\n[Graph] E_off vs I_peak (excluding last point)")
    plt.figure(figsize=(10, 6))
    for v, df, _ in all_data:
        df2 = df.iloc[:-1]
        plt.plot(df2["I_peak (A)"], df2["E_off (J)"], marker='s', linestyle='--', label=f"{v}V")
    plt.title(f"E_off vs I_peak (trimmed) @ {freq}Hz")
    plt.xlabel("I_peak (A)")
    plt.ylabel("E_off (J)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    fn = os.path.join("sauvegarde", f"graph_Eoff_vs_Ipeak_trimmed_{freq}Hz_{ts}.pdf")
    plt.savefig(fn)
    print(f"  → Saved: {fn}")

def calculer_puissances_point_par_point(all_data, freq, ts):
    outdir = "sauvegarde"
    print(f"\n[Graph] Instantaneous Power P = V × I")
    plt.figure(figsize=(10, 6))
    for v, _, _ in all_data:
        cf = pd.read_excel(os.path.join(excel_folder, f"Voltage_{v}_{freq//1000}kHz_courant.xlsx")).iloc[:, 0]
        tf = pd.read_excel(os.path.join(excel_folder, f"Voltage_{v}_{freq//1000}kHz_tension.xlsx")).iloc[:, 0]
        c = pd.to_numeric(cf, errors="coerce").dropna().reset_index(drop=True)
        t = pd.to_numeric(tf, errors="coerce").dropna().reset_index(drop=True)
        n = min(len(c), len(t))
        plt.plot(range(1, n+1), c[:n] * t[:n], label=f"{v}V")
    plt.title(f"P = V × I @ {freq}Hz")
    plt.xlabel("Sample")
    plt.ylabel("Power (W)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    fn = os.path.join(outdir, f"graph_P_vs_sample_{freq}Hz_{ts}.pdf")
    plt.savefig(fn)
    print(f"  → Saved: {fn}")

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    freq_dict = {}

    for folder in os.listdir(simulations_folder):
        if folder.startswith("Voltage_"):
            traiter_dossier(os.path.join(simulations_folder, folder), folder)

            all_phase_files = glob.glob(os.path.join(simulations_folder, folder, "PhaseShift_*.json"))
            for phase_file in all_phase_files:
                match = re.search(r"Freq(\d+)kHz", phase_file)
                if match:
                    freq_khz = int(match.group(1))
                    freq_hz = freq_khz * 1000
                    if freq_hz not in freq_dict:
                        freq_dict[freq_hz] = []
                    freq_dict[freq_hz].append((int(folder.split("_")[1]), folder))

    for freq_hz, voltages in sorted(freq_dict.items()):
        print(f"\n\n================= GLOBAL PROCESSING {freq_hz//1000}kHz =================")
        all_data = []
        for v, folder in voltages:
            process_voltage(v, freq_hz, all_data)

        if all_data:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_all_graphs(all_data, freq_hz, ts)
            plot_graphs_without_last_point(all_data, freq_hz, ts)
            calculer_puissances_point_par_point(all_data, freq_hz, ts)

    plt.show()
