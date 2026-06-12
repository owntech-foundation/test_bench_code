#! python3

# Original authors: Nicolas Rouger, Luiz Villa
# Revised by Leijnen Lorenzo
# V1_3 Mar 2025
# To bulk generate Json config
# For opposition test bench
# GPL v3

import numpy as np
import json
import os

# -----------------------------
# Defenitions
# -----------------------------
def autoGenerateJson(Commonparameters, dest_path: str, matrix, voltageRange, frequencyList, mode: str) -> int:
    """Génère un fichier JSON par couple (voltage, fréquence) dans des dossiers nommés Voltage_XX_YYYkHz"""

    for freq in frequencyList:
        freq_khz = int(freq * 1e-3)

        for i in range(matrix.shape[1]):
            column_data = matrix[:, i]
            step = np.mean(np.diff(np.sort(column_data)))
            min_val = int(np.min(column_data))
            max_val = np.max(column_data)
            voltage = int(voltageRange[i])

            # Création du dossier Voltage_XX_YYYkHz
            subfolder_name = f"Voltage_{voltage}_{freq_khz}kHz"
            subfolder_path = os.path.join(dest_path, subfolder_name)
            os.makedirs(subfolder_path, exist_ok=True)

            # Paramètres spécifiques selon le mode
            phase_info = {
                "dataOutputFolder": subfolder_path.replace('\\', '/'),
                "VoltageWrite": voltage,
                "frequencyPWM": freq,
                "InitialPhaseShiftPWM": Commonparameters["InitialPhaseShiftPWM"],  # << Valeur fixée
                "PhaseInit": min_val,
                "PhaseFinal": int(step * (nbPointsI - 1) + min_val) + 1,
                "PhaseStep": int(np.round(step)),
                "DutyInit": 0,
                "DutyFinal": 0,
                "DutyStep": 0
            }

            duty_info = {
                "dataOutputFolder": subfolder_path.replace('\\', '/'),
                "VoltageWrite": voltage,
                "frequencyPWM": freq,
                "DutyInit": min_val,
                "DutyFinal": max_val,
                "DutyStep": step,
            }

            match mode:
                case "Phase":
                    combined_parameters = {**Commonparameters, **phase_info}
                case "Duty":
                    combined_parameters = {**Commonparameters, **duty_info}
                case _:
                    return -1

            # Nom du fichier dans le bon format
            filename = f"{mode}Shift_Voltage_{voltage}V_Freq{freq_khz}kHz.json"
            file_path = os.path.join(subfolder_path, filename)

            # Sauvegarde
            with open(file_path, 'w') as f:
                json.dump(combined_parameters, f, indent=4)

            print(f"Fichier généré : {file_path}")

    return 1

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__": 
    # Load base config
    base_config_path = "base-config.json"
    with open(base_config_path, 'r') as f:
        base_config = json.load(f)
    
    frequency_list = base_config['frequencyPWM']
    InductorL = base_config['InductorL']
    TotalR = base_config['TotalR']
    Imin = base_config['Imin']
    Imax = base_config['Imax']
    Vmin = base_config['Vmin']
    Vmax = base_config['Vmax']
    nbPointsV = base_config['nbPointsV']
    nbPointsI = base_config['nbPointsI']
    InitialPhaseShiftPWM = base_config['InitialPhaseShiftPWM']

    Vdc = np.linspace(Vmin, Vmax, nbPointsV)
    print(f"Voltage steps:\n{Vdc}")

    Ipeak = np.linspace(Imin, Imax, nbPointsI)
    print(f"Current steps:\n{Ipeak}")

    for freq in frequency_list:
        freq_khz = int(freq / 1000)
        print(f"\n=== Génération pour {freq_khz} kHz ===")

        # Phase Shift Mode
        delta_I = Ipeak[:, None]*2  # phi is calculated with delta I, but we set the peak current that is switched
        Phi = np.round(360 * delta_I * InductorL * freq * 1e-6 / Vdc, decimals=0)  # in degrees
        print(f"\nPhase shift steps for {freq_khz} kHz:\n{Phi}")
        folder1_path = 'PhaseShift'
        autoGenerateJson(base_config, folder1_path, Phi, Vdc, [freq], mode="Phase")

        # Delta Alpha Mode
        DeltaAlpha = Ipeak[:, None] * TotalR / Vdc
        DeltaAlpha1000 = np.floor(1000 * DeltaAlpha)
        print(f"\nDelta Alpha steps x1000 for {freq_khz} kHz:\n{DeltaAlpha1000}")
        folder2_path = 'DutyShift'
        autoGenerateJson(base_config, folder2_path, DeltaAlpha1000, Vdc, [freq], mode="Duty")
