import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import os
import json

from InitZplus_V5 import (
    get_resource_manager,
    list_instruments,
    test_tdk,
    single_point_test,
    verify_json_files,
)

rm = get_resource_manager()

def gui_printer(*args, end="\n", sep=" ", tag=None):
    try:
        text = sep.join(str(arg) for arg in args) + end
        if tag is None:
            lower_text = text.lower()
            if any(x in lower_text for x in ["error", "fail", "exception", "traceback"]):
                tag = "error"
            elif any(x in lower_text for x in ["success", "done", "ok"]):
                tag = "success"
            else:
                tag = "info"
        output_text.insert(tk.END, text, tag)
        output_text.see(tk.END)
    except Exception as e:
        print("Erreur affichage GUI:", e)

def run_in_thread(func):
    threading.Thread(target=func, daemon=True).start()

def list_instr_gui():
    run_in_thread(lambda: list_instruments(rm, printer=gui_printer))

def test_tdk_gui():
    run_in_thread(lambda: test_tdk(rm, printer=gui_printer))

def single_point_gui():
    run_in_thread(lambda: single_point_test(rm, printer=gui_printer))

def verify_json_files_gui():
    run_in_thread(lambda: verify_json_files(printer=gui_printer))

def run_script(script_name):
    def _run():
        try:
            gui_printer(f"[INFO] Lancement de {script_name}...")
            process = subprocess.Popen(
                ["python", script_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            for line in process.stdout:
                gui_printer(line.strip(), tag="info")
            for line in process.stderr:
                gui_printer(line.strip(), tag="error")
            process.wait()
            gui_printer(f"[INFO] {script_name} terminé avec code {process.returncode}", 
                        tag="success" if process.returncode == 0 else "error")
        except Exception as e:
            gui_printer(f"[ERROR] Impossible de lancer {script_name}: {e}", tag="error")

    run_in_thread(_run)

def launch_supervisor():
    run_script("supervisor_script_v1_2.py")

def launch_generate_json():
    run_script("Opposition_GenerateJson_v1_4.py")

def launch_traitement():
    run_script("TraitementV10.py")

def load_base_config():
    base_path = "base-config.json"
    try:
        with open(base_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        gui_printer(f"[ERREUR] Impossible de lire {base_path}: {e}", tag="error")
        return

    for widget in config_display.winfo_children():
        widget.destroy()

    for key, value in config.items():
        row = tk.Frame(config_display, bg="#1e1e2f")
        row.pack(anchor="w", fill="x", pady=1)
        tk.Label(row, text=f"{key}:", width=25, anchor="w", fg="white", bg="#1e1e2f",
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Label(row, text=str(value), anchor="w", fg="#5dade2", bg="#1e1e2f",
                 font=("Segoe UI", 10)).pack(side="left")

# === Fenêtre principale ===
root = tk.Tk()
root.title("Interface HACKATHON")
root.geometry("1150x750")
root.configure(bg="#1e1e2f")

# === Style
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton",
                font=("Segoe UI", 10),
                padding=6,
                relief="flat",
                background="#3498db",
                foreground="white")
style.map("TButton",
          background=[("active", "#2980b9")],
          foreground=[("active", "white")])

# === Titre
tk.Label(root, text="Interface HACKATHON", font=("Segoe UI", 18, "bold"),
         bg="#1e1e2f", fg="#e0e0e0").pack(pady=10)

# === Ligne de boutons principaux
top_buttons = tk.Frame(root, bg="#1e1e2f")
top_buttons.pack(pady=10)

ttk.Button(top_buttons, text="Lister Instruments", command=list_instr_gui).grid(row=0, column=0, padx=5, pady=5)
ttk.Button(top_buttons, text="Tester TDK", command=test_tdk_gui).grid(row=0, column=1, padx=5, pady=5)
ttk.Button(top_buttons, text="Test SPIN Point", command=single_point_gui).grid(row=0, column=2, padx=5, pady=5)

# === Corps principal : gauche config / droite boutons + console
main_frame = tk.Frame(root, bg="#1e1e2f")
main_frame.pack(fill="both", expand=True, padx=10)

# === Partie gauche : Config JSON
left_frame = tk.Frame(main_frame, bg="#1e1e2f")
left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

ttk.Button(left_frame, text="Lire base-config.json", command=load_base_config).pack(pady=(0, 10))

json_frame = tk.LabelFrame(left_frame, text="Paramètres JSON", fg="white", bg="#1e1e2f",
                           font=("Segoe UI", 10, "bold"))
json_frame.pack(fill="both", expand=True, pady=(0, 10))

config_canvas = tk.Canvas(json_frame, bg="#1e1e2f", highlightthickness=0)
scrollbar = ttk.Scrollbar(json_frame, orient="vertical", command=config_canvas.yview)
config_display = tk.Frame(config_canvas, bg="#1e1e2f")

config_display.bind("<Configure>", lambda e: config_canvas.configure(scrollregion=config_canvas.bbox("all")))
config_canvas.create_window((0, 0), window=config_display, anchor="nw")
config_canvas.configure(yscrollcommand=scrollbar.set)

config_canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# === Partie droite : Boutons actions + console
right_frame = tk.Frame(main_frame, bg="#1e1e2f")
right_frame.pack(side="left", fill="both", expand=True)

action_buttons = tk.Frame(right_frame, bg="#1e1e2f")
action_buttons.pack(pady=(0, 10))

ttk.Button(action_buttons, text="Créer JSON", command=launch_generate_json).grid(row=0, column=0, padx=10, pady=5)
ttk.Button(action_buttons, text="Vérif JSON", command=verify_json_files_gui).grid(row=1, column=0, padx=10, pady=5)

ttk.Button(action_buttons, text="Lancer Supervisor", command=launch_supervisor).grid(row=0, column=1, padx=10, pady=5)
ttk.Button(action_buttons, text="Traitement Final", command=launch_traitement).grid(row=1, column=1, padx=10, pady=5)

# === Console
output_frame = tk.LabelFrame(right_frame, text="Console de sortie", bg="#1e1e2f",
                             fg="white", font=("Segoe UI", 10, "bold"))
output_frame.pack(fill="both", expand=True, padx=5, pady=10)

output_text = tk.Text(output_frame, height=15, bg="#2c2f3f", fg="#d0f0ff",
                      insertbackground="white", font=("Courier New", 10),
                      wrap="word", borderwidth=0)
output_text.pack(side=tk.LEFT, fill="both", expand=True, padx=(10, 0), pady=10)

scrollbar = tk.Scrollbar(output_frame, command=output_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
output_text.config(yscrollcommand=scrollbar.set)

output_text.tag_config("info", foreground="#5dade2")
output_text.tag_config("success", foreground="#58d68d")
output_text.tag_config("error", foreground="#e74c3c")

def on_closing():
    try:
        gui_printer("Fermeture de l'application... Fermeture du ResourceManager.")
        rm.close()
    except Exception as e:
        gui_printer(f"Erreur lors de la fermeture du RM : {e}", tag="error")
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
