import pyvisa as visa
import time
import traceback
import os
import re
from supervisor_script import runner  # Assure-toi que runner(jsonfile) est la fonction pour exécuter un test JSON
from SinglePoint_SPIN_v1_1 import single_point

tdk_addr = "ASRL/dev/ttyACM0::INSTR"
delay = 0.1

def get_resource_manager():
    return visa.ResourceManager()

def list_instruments(rm, printer=print):
    printer(">> Recherche des instruments disponibles...")
    try:
        instruments = rm.list_resources()
        if not instruments:
            printer("Aucun instrument détecté.")
            return
        for res in instruments:
            printer(f"'{res}': ", end='')
            try:
                device = rm.open_resource(res, query_delay=0.5)
                idn = device.query("*IDN?")
                printer(f"{type(device)} - {idn}")
                device.close()
            except visa.errors.VisaIOError as e:
                printer(f"VisaIOError: {e}")
            except Exception as e:
                printer(f"Erreur : {e}")
    except Exception as e:
        printer(f"Erreur pendant la détection : {e}")
        traceback.print_exc()


def output_change(smu, State):
    smu.write('OUTPut:STATe ' + State)
    time.sleep(delay)

def test_tdk(rm, printer=print):
    printer(">> Testing TDK power supply...")
    try:
        TDKLambda = rm.open_resource(tdk_addr, query_delay=0.5)
        TDKLambda.write('INSTrument:NSELect  1')
        TDKLambda.write('VOLTage:LEV 0')
        output_change(TDKLambda, 'ON')
        time.sleep(2)
        output_change(TDKLambda, 'OFF')
        TDKLambda.close()
        printer("TDK test successful\n")
    except Exception as e:
        printer(f"TDK test failed: {e}")
        traceback.print_exc()

def run_tests(rm, printer=print):
    printer(">> Recherche et exécution des fichiers JSON de test PhaseShift...")

    base_folder = os.path.abspath("PhaseShift")
    folder_pattern = re.compile(r"Voltage_\d+_\d+kHz")
    file_pattern = re.compile(r"PhaseShift_Voltage_\d+V_Freq\d+kHz\.json$")

    matched_files = []

    for root, dirs, files in os.walk(base_folder):
        folder_name = os.path.basename(root)
        printer(f"DEBUG : Exploration du dossier : {root}")

        if not folder_pattern.match(folder_name):
            continue

        for file in files:
            printer(f"DEBUG : Fichier trouvé : {file}")
            if file_pattern.match(file):
                full_path = os.path.join(root, file)
                matched_files.append(full_path)

    if not matched_files:
        printer("Aucun fichier JSON PhaseShift au format attendu trouvé.")
        return

    for jsonfile in matched_files:
        printer(f">> Lancement test pour : {jsonfile}")
        try:
            runner(jsonfile)
            printer("Test terminé\n")
        except Exception as e:
            printer(f"Erreur pendant le test du fichier {jsonfile}: {e}")
            traceback.print_exc()

def single_point_test(rm, printer=print):
    printer(">> Running single point SPIN test...")
    try:
        resources = rm.list_resources()
        printer(f"Ressources disponibles : {resources}")
        if not resources:
            printer("Aucun instrument détecté.", tag="error")
            return

        addr = resources[0]  # à adapter si tu veux un port spécifique
        printer(f"Ouverture de la ressource : {addr}")
        instrument = rm.open_resource(addr)

        try:
            from SinglePoint_SPIN_v1_1 import single_point
            single_point(instrument)
        finally:
            instrument.close()
            printer("Instrument fermé proprement.")

        printer("Single point test done\n")

    except Exception as e:
        printer(f"Single point test failed: {e}")
        traceback.print_exc()



def verify_json_files(printer=print):
    printer(">> Vérification des fichiers JSON PhaseShift...")

    base_folder = os.path.abspath("PhaseShift")
    folder_pattern = re.compile(r"Voltage_\d+_\d+kHz")
    file_pattern = re.compile(r"PhaseShift_Voltage_\d+V_Freq\d+kHz\.json$")

    matched_files = []

    for root, dirs, files in os.walk(base_folder):
        folder_name = os.path.basename(root)
        printer(f"DEBUG : Exploration du dossier : {root}")

        if not folder_pattern.match(folder_name):
            continue

        for file in files:
            printer(f"DEBUG : Fichier trouvé : {file}")
            if file_pattern.match(file):
                matched_files.append(os.path.join(root, file))

    if matched_files:
        printer(f"{len(matched_files)} fichiers JSON valides trouvés.")
    else:
        printer("Aucun fichier JSON valide trouvé.")
