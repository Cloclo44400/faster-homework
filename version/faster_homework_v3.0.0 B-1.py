import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import io
import webbrowser
import urllib.parse
from datetime import datetime
import shutil
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
DATA_JSON_URL = "https://raw.githubusercontent.com/Cloclo44400/faster-homework/main/data.json"
MAIL_TO       = "suggestion.retoure.44@proton.me"

# Whitelist des modèles IA autorisés sur Hugging Face (ID du dépôt : Nom affiché)
ALLOWED_MODELS = {
    "Qwen/Qwen2.5-1.5B-Instruct": "🧠 Qwen 2.5 1.5B (basique (8go ram) — ~3 Go)",
    "openbmb/MiniCPM5-1B": "🤖 MiniCPM 1B (limter (6go ram) — ~2 Go)"
}

# ─── COULEURS & STYLE ─────────────────────────────────────────────────────────
BG          = "#0b0d14"
BG2         = "#13161f"
BG3         = "#1c2030"
ACCENT      = "#7c6dfa"
ACCENT2     = "#b8aeff"
TEXT        = "#e2e8f0"
TEXT_DIM    = "#4a5068"
SUCCESS     = "#34d399"
DANGER      = "#f87171"
FONT_TITLE  = ("Syne", 20, "bold")
FONT_SUB    = ("Syne", 11)
FONT_LABEL  = ("Syne", 10)
FONT_SMALL  = ("Syne", 9)
FONT_MONO   = ("Consolas", 11)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Faster Homework v3.0.0 [Beta-1]")
        self.geometry("1150x660")
        self.minsize(720, 520)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.data      = None
        self._img_refs = []
        
        # Mode Développeur
        self.dev_mode = False
        self.dev_pane = None
        self.console_text = None

        # Variables d'état de l'IA
        self.ai_model = None
        self.ai_tokenizer = None
        self.ai_loaded_id = None

        self._build_ui()
        self._load_data()
        
        self.bind("<F1>", self._toggle_dev_mode)
        self.log("Application v3.0.0 B-1 prête. Mode dév disponible via F1.")

    # ── CONSOLE DE LOGS ───────────────────────────────────────────────────────
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        print(log_msg.strip())
        
        if self.console_text and self.console_text.winfo_exists():
            self.console_text.config(state="normal")
            self.console_text.insert("end", log_msg)
            self.console_text.see("end")
            self.console_text.config(state="disabled")

    # ── UI PRINCIPALE ─────────────────────────────────────────────────────────
    def _build_ui(self):
        self.main_split = tk.PanedWindow(self, orient="horizontal", bg=BG, sashwidth=6, sashrelief="flat")
        self.main_split.pack(fill="both", expand=True)

        self.app_frame = tk.Frame(self.main_split, bg=BG)
        self.main_split.add(self.app_frame, minsize=500, stretch="always")

        # Header
        header = tk.Frame(self.app_frame, bg=BG, pady=16)
        header.pack(fill="x", padx=28)

        tk.Label(header, text="⚡ Faster Homework", font=FONT_TITLE, bg=BG, fg=ACCENT2).pack(side="left")
        tk.Label(header, text="v3.0.0 B-1", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(side="left", padx=(6, 0), pady=(6, 0))

        self.status_dot = tk.Label(header, text="●", font=("Syne", 13), bg=BG, fg=TEXT_DIM)
        self.status_dot.pack(side="right", padx=(0, 4))
        self.status_lbl = tk.Label(header, text="Chargement…", font=FONT_SMALL, bg=BG, fg=TEXT_DIM)
        self.status_lbl.pack(side="right")

        tk.Frame(self.app_frame, bg=ACCENT, height=2).pack(fill="x", padx=28)

        # Notebook
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook",     background=BG,  borderwidth=0)
        style.configure("TNotebook.Tab", background=BG2, foreground=TEXT_DIM, font=FONT_SUB, padding=[14, 7])
        style.map("TNotebook.Tab", background=[("selected", BG)], foreground=[("selected", ACCENT2)])

        self.nb = ttk.Notebook(self.app_frame)
        self.nb.pack(fill="both", expand=True, padx=20, pady=14)

        self.tab_textes      = tk.Frame(self.nb, bg=BG)
        self.tab_images      = tk.Frame(self.nb, bg=BG)
        self.tab_fichiers    = tk.Frame(self.nb, bg=BG)
        self.tab_ia          = tk.Frame(self.nb, bg=BG) # Onglet IA
        self.tab_suggestions = tk.Frame(self.nb, bg=BG)

        self.nb.add(self.tab_textes,      text="  📄  Textes  ")
        self.nb.add(self.tab_images,      text="  🖼️  Images  ")
        self.nb.add(self.tab_fichiers,    text="  📦  Fichiers  ")
        self.nb.add(self.tab_ia,          text="  🤖  IA (Beta)  ")
        self.nb.add(self.tab_suggestions, text="  ✉️  Suggestions  ")
        
        self._populate_ia()

    # ── ONGLET IA (LOCAL) ─────────────────────────────────────────────────────
    def _populate_ia(self):
        parent = self.tab_ia
        
        # Division de l'onglet IA : Contrôles en haut, Chat/Prompt en bas
        ctrl_frame = tk.Frame(parent, bg=BG2, padx=14, pady=12)
        ctrl_frame.pack(fill="x", padx=14, pady=10)
        
        tk.Label(ctrl_frame, text="Modèle local autorisé :", font=FONT_LABEL, bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(0, 10))
        
        # Combobox basée sur les clés inversées de la Whitelist pour un affichage propre
        self.ai_choice = ttk.Combobox(ctrl_frame, state="readonly", font=FONT_SMALL, width=42)
        self.ai_choice['values'] = list(ALLOWED_MODELS.values())
        self.ai_choice.current(0)
        self.ai_choice.pack(side="left", padx=(0, 10))
        self.ai_choice.bind("<<ComboboxSelected>>", lambda e: self._check_local_status())
        
        # Bouton Charger
        self.btn_load_ai = tk.Button(ctrl_frame, text="Charger le modèle", font=FONT_SMALL, bg=ACCENT, fg="white",
                                     relief="flat", cursor="hand2", padx=10, command=self._start_load_ai)
        self.btn_load_ai.pack(side="left", padx=(0, 5))

        # Bouton Décharger
        self.btn_unload_ai = tk.Button(ctrl_frame, text="🔌 Décharger", font=FONT_SMALL, bg=BG3, fg=TEXT,
                                       relief="flat", cursor="hand2", padx=10, state="disabled", command=self._unload_active_model)
        self.btn_unload_ai.pack(side="left", padx=(0, 5))

        # Bouton Désinstaller
        self.btn_uninstall_ai = tk.Button(ctrl_frame, text="🗑️ Désinstaller", font=FONT_SMALL, bg=DANGER, fg="white",
                                          relief="flat", cursor="hand2", padx=10, state="disabled", command=self._uninstall_selected_model)
        self.btn_uninstall_ai.pack(side="left", padx=(0, 10))
        
        # Indicateur de téléchargement sur le disque
        self.lbl_ai_status_on_disk = tk.Label(ctrl_frame, text="Vérification...", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM)
        self.lbl_ai_status_on_disk.pack(side="left", padx=(5, 10))

        # Statut du chargement en mémoire active
        self.lbl_ai_state = tk.Label(ctrl_frame, text="🔴 Non chargé", font=FONT_SMALL, bg=BG2, fg=DANGER, padx=10)
        self.lbl_ai_state.pack(side="right")

        # Zone d'interaction (Saisie et Réponse)
        chat_frame = tk.Frame(parent, bg=BG)
        chat_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        
        # Entrée utilisateur
        tk.Label(chat_frame, text="Pose ta question à l'IA :", font=FONT_LABEL, bg=BG, fg=TEXT).pack(anchor="w", pady=(5, 2))
        self.ai_input = tk.Entry(chat_frame, bg=BG2, fg=TEXT, font=FONT_SUB, relief="flat", insertbackground=TEXT)
        self.ai_input.pack(fill="x", ipady=6, pady=(0, 10))
        self.ai_input.bind("<Return>", lambda e: self._start_ai_generation()) # Entrée déclenche l'IA
        
        # Bouton Générer
        self.btn_gen_ai = tk.Button(chat_frame, text="Générer une réponse ✨", font=("Syne", 10, "bold"), bg=BG3, fg=TEXT_DIM,
                                    relief="flat", state="disabled", cursor="hand2", pady=6, command=self._start_ai_generation)
        self.btn_gen_ai.pack(fill="x", pady=(0, 10))
        
        # Sortie Réponse
        tk.Label(chat_frame, text="Réponse de l'IA (locale) :", font=FONT_LABEL, bg=BG, fg=TEXT).pack(anchor="w")
        self.ai_output = tk.Text(chat_frame, bg=BG2, fg=TEXT, font=FONT_MONO, wrap="word", relief="flat", padx=10, pady=10)
        scroll_ai = tk.Scrollbar(self.ai_output, command=self.ai_output.yview, bg=BG2, troughcolor=BG2)
        self.ai_output.config(yscrollcommand=scroll_ai.set)
        scroll_ai.pack(side="right", fill="y")
        self.ai_output.pack(fill="both", expand=True)

        # Déterminer le statut du disque au lancement
        self._check_local_status()

    # ── LOGIQUE DE L'IA ───────────────────────────────────────────────────────
    def _get_selected_model_id(self):
        # Retrouve l'ID Hugging Face à partir du nom sélectionné dans le menu déroulant
        selected_name = self.ai_choice.get()
        for hf_id, name in ALLOWED_MODELS.items():
            if name == selected_name:
                return hf_id
        return None

    def _check_local_status(self):
        # Vérifie si le dossier du modèle est présent sur le disque dur
        model_id = self._get_selected_model_id()
        if not model_id:
            return

        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        folder_name = f"models--{model_id.replace('/', '--')}"
        model_path = cache_dir / folder_name

        if model_path.exists():
            self.lbl_ai_status_on_disk.config(text="📥 Téléchargé (sur le disque)", fg=SUCCESS)
            self.btn_uninstall_ai.config(state="normal")
        else:
            self.lbl_ai_status_on_disk.config(text="☁️ Non installé (Sera téléchargé)", fg=TEXT_DIM)
            self.btn_uninstall_ai.config(state="disabled")

    def _show_download_popup(self, model_id):
        # Fenêtre modale de progression dédiée au téléchargement
        popup = tk.Toplevel(self)
        popup.title("Téléchargement du modèle IA")
        popup.geometry("520x360")
        popup.configure(bg=BG)
        popup.grab_set()  # Verrouille l'interaction avec la fenêtre principale
        popup.resizable(False, False)

        tk.Label(popup, text="⬇️ Téléchargement du modèle local", font=("Syne", 13, "bold"), bg=BG, fg=ACCENT2).pack(pady=(20, 5))
        tk.Label(popup, text=f"Modèle ciblé : {model_id}", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack()

        # Barre de progression
        progress = ttk.Progressbar(popup, mode="indeterminate", length=440)
        progress.pack(pady=20)
        progress.start(12)  # Démarre l'animation continue

        # Terminal de progression
        terminal = tk.Text(popup, bg=BG2, fg=SUCCESS, font=FONT_MONO, wrap="word", height=8, width=55, relief="flat", padx=10, pady=10)
        terminal.pack(padx=20, pady=5)
        terminal.insert("end", "Initialisation de la connexion avec Hugging Face…\n")
        terminal.config(state="disabled")

        # Empêcher l'utilisateur de fermer la fenêtre manuellement pour éviter de casser le cache
        def prevent_close():
            messagebox.showwarning("Téléchargement en cours", "Veuillez patienter pendant le téléchargement pour éviter de corrompre les fichiers de l'IA.")
        
        popup.protocol("WM_DELETE_WINDOW", prevent_close)

        return popup, terminal

    def _start_load_ai(self):
        model_id = self._get_selected_model_id()
        if not model_id:
            return
        
        # Vérification si le modèle est déjà là
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        folder_name = f"models--{model_id.replace('/', '--')}"
        model_path = cache_dir / folder_name
        is_already_installed = model_path.exists()

        self.btn_load_ai.config(state="disabled", text="⏳ En cours…", bg=BG3)
        self.btn_uninstall_ai.config(state="disabled")
        self.btn_unload_ai.config(state="disabled")
        self.lbl_ai_state.config(text="⚙️ Initialisation...", fg=ACCENT2)

        popup = None
        popup_terminal = None

        if not is_already_installed:
            self.log(f"Premier téléchargement requis pour : {model_id}")
            popup, popup_terminal = self._show_download_popup(model_id)
        else:
            self.log(f"Chargement direct depuis le cache local pour : {model_id}")

        threading.Thread(target=self._async_load_ai, args=(model_id, popup, popup_terminal), daemon=True).start()

    def _async_load_ai(self, model_id, popup=None, popup_terminal=None):
        def update_log(msg):
            # Écrit dans la console dev de l'application
            self.log(msg)
            # Écrit dans le petit terminal de la fenêtre de téléchargement s'il existe
            if popup_terminal and popup_terminal.winfo_exists():
                self.after(0, lambda: (
                    popup_terminal.config(state="normal"),
                    popup_terminal.insert("end", f"▶ {msg}\n"),
                    popup_terminal.see("end"),
                    popup_terminal.config(state="disabled")
                ))

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            update_log("Vérification et chargement du Tokenizer…")
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            
            update_log("Téléchargement/Chargement des poids du modèle IA (cette étape peut prendre quelques minutes au premier lancement)…")
            model = AutoModelForCausalLM.from_pretrained(model_id)
            
            self.ai_model = model
            self.ai_tokenizer = tokenizer
            self.ai_loaded_id = model_id
            
            # Si la fenêtre de téléchargement est ouverte, on la ferme proprement
            if popup and popup.winfo_exists():
                self.after(0, popup.destroy)
                
            self.after(0, self._on_ai_loaded_success)
        except ImportError:
            if popup and popup.winfo_exists():
                self.after(0, popup.destroy)
            self.log("Erreur critique : 'transformers' ou 'torch' introuvable dans l'environnement Python.")
            self.after(0, lambda: messagebox.showerror("Dépendances manquantes", "Veuillez exécuter la commande : pip install transformers torch"))
            self.after(0, self._on_ai_loaded_failure)
        except Exception as e:
            if popup and popup.winfo_exists():
                self.after(0, popup.destroy)
            self.log(f"Échec du chargement du modèle IA local : {e}")
            self.after(0, lambda: messagebox.showerror("Erreur IA", f"Impossible de charger le modèle local :\n{e}"))
            self.after(0, self._on_ai_loaded_failure)

    def _on_ai_loaded_success(self):
        self.log(f"Modèle {self.ai_loaded_id} prêt et chargé en mémoire RAM avec succès !")
        self.lbl_ai_state.config(text="🟢 Prêt (Local)", fg=SUCCESS)
        self.btn_load_ai.config(state="normal", text="Changer de modèle", bg=BG3)
        self.btn_gen_ai.config(state="normal", bg=ACCENT, fg="white")
        self.btn_unload_ai.config(state="normal")
        self._check_local_status()

    def _on_ai_loaded_failure(self):
        self.lbl_ai_state.config(text="❌ Échec", fg=DANGER)
        self.btn_load_ai.config(state="normal", text="Réessayer", bg=ACCENT)
        self.btn_gen_ai.config(state="disabled", bg=BG3, fg=TEXT_DIM)
        self.btn_unload_ai.config(state="disabled")
        self._check_local_status()

    def _unload_active_model(self):
        if not self.ai_loaded_id:
            return
        
        model_id = self.ai_loaded_id
        self.log(f"Déchargement manuel du modèle IA : {model_id}")
        
        # Réinitialisation de l'état mémoire
        self.ai_model = None
        self.ai_tokenizer = None
        self.ai_loaded_id = None
        
        # Appel du garbage collector pour libérer immédiatement la RAM physique
        try:
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.log("RAM système nettoyée et cache VRAM vidé.")
        except Exception as e:
            self.log(f"Erreur mineure lors du nettoyage mémoire : {e}")

        # Mise à jour graphique
        self.lbl_ai_state.config(text="🔴 Non chargé", fg=DANGER)
        self.btn_gen_ai.config(state="disabled", bg=BG3, fg=TEXT_DIM)
        self.btn_unload_ai.config(state="disabled")
        self.btn_load_ai.config(text="Charger le modèle", bg=ACCENT)
        
        self._check_local_status()
        messagebox.showinfo("Modèle déchargé", f"Le modèle '{model_id}' a bien été déchargé de la mémoire RAM.")

    def _uninstall_selected_model(self):
        model_id = self._get_selected_model_id()
        if not model_id:
            return

        confirm = messagebox.askyesno(
            "Confirmer la désinstallation", 
            f"Es-tu sûr de vouloir désinstaller le modèle '{model_id}' ?\n\nCela va supprimer définitivement ses fichiers du disque dur pour libérer de l'espace sur ton ordinateur."
        )
        if not confirm:
            return

        self.log(f"Lancement de la désinstallation de : {model_id}")

        # Si le modèle supprimé est celui actuellement chargé en RAM, on le désactive d'abord
        if self.ai_loaded_id == model_id:
            self.ai_model = None
            self.ai_tokenizer = None
            self.ai_loaded_id = None
            self.lbl_ai_state.config(text="🔴 Non chargé", fg=DANGER)
            self.btn_gen_ai.config(state="disabled", bg=BG3, fg=TEXT_DIM)
            self.btn_unload_ai.config(state="disabled")
            self.btn_load_ai.config(text="Charger le modèle", bg=ACCENT)
            self.log("Modèle actif déchargé de la mémoire RAM avant désinstallation.")

        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        folder_name = f"models--{model_id.replace('/', '--')}"
        model_path = cache_dir / folder_name

        try:
            if model_path.exists():
                shutil.rmtree(model_path)
                self.log(f"Dossier {folder_name} supprimé avec succès.")
                messagebox.showinfo("Désinstallation réussie", f"Le modèle {model_id} a bien été retiré de ton ordinateur.")
            else:
                messagebox.showwarning("Introuvable", "Le modèle n'est plus présent sur le disque dur.")
        except Exception as e:
            self.log(f"Erreur lors de la désinstallation : {e}")
            messagebox.showerror("Erreur de suppression", f"Impossible de supprimer les fichiers du modèle :\n{e}")

        self._check_local_status()

    def _start_ai_generation(self):
        prompt = self.ai_input.get().strip()
        if not prompt or not self.ai_model:
            return
        
        self.btn_gen_ai.config(state="disabled", text="⚡ L'IA réfléchit...")
        self.ai_output.delete("1.0", "end")
        self.ai_output.insert("end", "🧠 Calcul des tokens en cours, veuillez patienter...")
        self.log(f"Prompt envoyé à l'IA : '{prompt}'")
        
        threading.Thread(target=self._async_generate, args=(prompt,), daemon=True).start()

    def _async_generate(self, prompt):
        try:
            messages = [{"role": "user", "content": prompt}]
            text = self.ai_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            
            model_inputs = self.ai_tokenizer([text], return_tensors="pt")
            
            generated_ids = self.ai_model.generate(
                **model_inputs,
                max_new_tokens=150, 
                do_sample=True,
                temperature=0.7
            )
            
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            response = self.ai_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            self.after(0, lambda: self._on_generation_success(response))
        except Exception as e:
            self.log(f"Erreur pendant la génération : {e}")
            self.after(0, lambda: self._on_generation_success(f"[Erreur de génération locale] : {e}"))

    def _on_generation_success(self, response):
        self.ai_output.delete("1.0", "end")
        self.ai_output.insert("end", response.strip())
        self.btn_gen_ai.config(state="normal", text="Générer une réponse ✨")
        self.log("Réponse générée et affichée à l'écran.")


    # ── ACTION CLAVIER F1 (MODE DEVELOPPEUR) ──────────────────────────────────
    def _toggle_dev_mode(self, event=None):
        self.dev_mode = not self.dev_mode
        self.log(f"Mode développeur {'activé' if self.dev_mode else 'désactivé'}.")
        
        if self.dev_mode:
            self._build_dev_pane()
        else:
            if self.dev_pane:
                self.main_split.forget(self.dev_pane)
                self.dev_pane.destroy()
                self.dev_pane = None
                self.console_text = None

    def _build_dev_pane(self):
        self.dev_pane = tk.Frame(self.main_split, bg=BG2, padx=10, pady=10)
        self.main_split.add(self.dev_pane, minsize=320, stretch="never")

        tk.Label(self.dev_pane, text="🛠️ Mode Développeur", font=("Syne", 12, "bold"), bg=BG2, fg=ACCENT2).pack(anchor="w", pady=(0, 5))
        
        dev_nb = ttk.Notebook(self.dev_pane)
        dev_nb.pack(fill="both", expand=True)

        tab_console = tk.Frame(dev_nb, bg=BG2)
        dev_nb.add(tab_console, text="Console")

        self.console_text = tk.Text(tab_console, bg=BG, fg=SUCCESS, font=FONT_MONO, wrap="word", relief="flat", state="disabled", padx=8, pady=8)
        scroll_c = tk.Scrollbar(tab_console, command=self.console_text.yview, bg=BG, troughcolor=BG2)
        self.console_text.config(yscrollcommand=scroll_c.set)
        scroll_c.pack(side="right", fill="y")
        self.console_text.pack(fill="both", expand=True)

        tab_debug = tk.Frame(dev_nb, bg=BG2, padx=8, pady=10)
        dev_nb.add(tab_debug, text="Debug / Outils")

        tk.Label(tab_debug, text="Actions de test :", font=FONT_LABEL, bg=BG2, fg=TEXT).pack(anchor="w", pady=(0, 10))

        tk.Button(tab_debug, text="Rafraîchir les données", font=FONT_SMALL, bg=ACCENT, fg="white", relief="flat", activebackground=ACCENT2, cursor="hand2", command=self._load_data, pady=6).pack(fill="x", pady=4)
        tk.Button(tab_debug, text="Simuler une erreur réseau", font=FONT_SMALL, bg=DANGER, fg="white", relief="flat", activebackground=ACCENT2, cursor="hand2", command=lambda: self.log("[DEBUG TEST] Erreur réseau 404 simulée sur l'API."), pady=6).pack(fill="x", pady=4)
        tk.Button(tab_debug, text="Effacer la console", font=FONT_SMALL, bg=BG3, fg=TEXT, relief="flat", activebackground=ACCENT2, cursor="hand2", command=self._clear_console, pady=6).pack(fill="x", pady=4)

        self.log("Panneau de contrôle développeur attaché avec succès.")

    def _clear_console(self):
        if self.console_text:
            self.console_text.config(state="normal")
            self.console_text.delete("1.0", "end")
            self.console_text.config(state="disabled")
            self.log("Console effacée.")

    # ── STATUS ────────────────────────────────────────────────────────────────
    def _set_status(self, txt, color):
        self.status_lbl.config(text=txt, fg=color)
        self.status_dot.config(fg=color)

    # ── CHARGEMENT DATA ───────────────────────────────────────────────────────
    def _load_data(self):
        self._set_status("Connexion…", TEXT_DIM)
        self.log(f"Requête HTTP GET vers {DATA_JSON_URL}")
        threading.Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_data(self):
        try:
            r = requests.get(DATA_JSON_URL, timeout=10)
            r.raise_for_status()
            self.data = r.json()
            self.log("Données JSON récupérées avec succès !")
            self.after(0, self._populate)
            self.after(0, lambda: self._set_status("Connecté", SUCCESS))
        except Exception as e:
            self.log(f"Erreur de récupération : {e}")
            self.after(0, lambda: self._set_status("Erreur de connexion", DANGER))
            self.after(0, lambda: messagebox.showerror("Erreur", f"Impossible de charger data.json :\n{e}"))

    def _populate(self):
        self.log("Génération des éléments de l'interface graphique (onglets)...")
        self._populate_textes()
        self._populate_images()
        self._populate_fichiers()
        self._populate_suggestions()

    # ── TEXTES ────────────────────────────────────────────────────────────────
    def _populate_textes(self):
        parent = self.tab_textes
        for widget in parent.winfo_children(): widget.destroy()
        textes = [t for t in self.data.get("textes", []) if t.get("url")]

        if not textes:
            self._empty(parent, "Aucun texte disponible.")
            return

        pane = tk.PanedWindow(parent, orient="horizontal", bg=BG, sashwidth=4, sashrelief="flat")
        pane.pack(fill="both", expand=True)

        left  = tk.Frame(pane, bg=BG2, width=200)
        right = tk.Frame(pane, bg=BG)
        pane.add(left,  minsize=160)
        pane.add(right, minsize=300)

        tk.Label(left, text="Articles", font=("Syne", 9, "bold"), bg=BG2, fg=ACCENT2, pady=10).pack(fill="x", padx=10)

        txt_area = tk.Text(right, bg=BG2, fg=TEXT, font=FONT_MONO, wrap="word", relief="flat", padx=14, pady=14, state="disabled", insertbackground=TEXT)
        scroll = tk.Scrollbar(right, command=txt_area.yview, bg=BG2, troughcolor=BG2, relief="flat")
        txt_area.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt_area.pack(fill="both", expand=True)

        def load_text(nom, url):
            self.log(f"Chargement du document texte : '{nom}'")
            txt_area.config(state="normal")
            txt_area.delete("1.0", "end")
            txt_area.insert("end", "Chargement…")
            txt_area.config(state="disabled")

            def fetch():
                try:
                    r = requests.get(url, timeout=10)
                    r.raise_for_status()
                    content = r.text
                    self.log(f"Document '{nom}' chargé avec succès ({len(content)} caractères).")
                except Exception as e:
                    content = f"[Erreur] {e}"
                    self.log(f"Erreur de chargement pour '{nom}' : {e}")
                self.after(0, lambda: (txt_area.config(state="normal"), txt_area.delete("1.0", "end"), txt_area.insert("end", content), txt_area.config(state="disabled")))
            threading.Thread(target=fetch, daemon=True).start()

        for item in textes:
            b = tk.Button(left, text=item["nom"], font=FONT_LABEL, bg=BG2, fg=TEXT, relief="flat", anchor="w", activebackground=ACCENT, activeforeground="white", cursor="hand2", padx=12, pady=7)
            b.config(command=lambda u=item["url"], n=item["nom"]: load_text(n, u))
            b.pack(fill="x", padx=6, pady=2)

    # ── IMAGES ────────────────────────────────────────────────────────────────
    def _populate_images(self):
        parent = self.tab_images
        for widget in parent.winfo_children(): widget.destroy()
        images = [i for i in self.data.get("images", []) if i.get("url")]

        if not images:
            self._empty(parent, "Aucune image disponible.")
            return

        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview, bg=BG2, troughcolor=BG2, relief="flat")
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        grid_frame = tk.Frame(canvas, bg=BG)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        grid_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        cols = 3
        for i, item in enumerate(images):
            cell = tk.Frame(grid_frame, bg=BG2, padx=8, pady=8, cursor="hand2")
            cell.grid(row=i // cols, column=i % cols, padx=10, pady=10, sticky="nsew")

            lbl_img = tk.Label(cell, bg=BG2, text="⏳", font=("Syne", 24), fg=TEXT_DIM)
            lbl_img.pack()
            tk.Label(cell, text=item["nom"], font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack()

            url = item["url"]
            nom = item["nom"]

            cell.bind("<Button-1>",  lambda e, u=url, n=nom: self._open_lightbox(u, n))
            lbl_img.bind("<Button-1>", lambda e, u=url, n=nom: self._open_lightbox(u, n))

            threading.Thread(target=self._load_image, args=(url, lbl_img, nom), daemon=True).start()

        for c in range(cols): grid_frame.columnconfigure(c, weight=1)

    def _load_image(self, url, label, nom):
        self.log(f"Chargement miniature pour '{nom}'")
        try:
            from PIL import Image, ImageTk
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content))
            img.thumbnail((200, 160))
            photo = ImageTk.PhotoImage(img)
            self._img_refs.append(photo)
            self.after(0, lambda: label.config(image=photo, text=""))
            label._original_url = url
            self.log(f"Miniature '{nom}' affichée.")
        except ImportError:
            self.log("Erreur Pillow manquant lors du rendu de la miniature.")
            self.after(0, lambda: label.config(text="📷\npip install Pillow", font=FONT_SMALL, fg=TEXT_DIM))
        except Exception as e:
            self.log(f"Erreur rendu miniature pour '{nom}' : {e}")
            self.after(0, lambda: label.config(text="❌", font=FONT_SMALL, fg=DANGER))

    # ── LIGHTBOX (AVEC DEPLACEMENT CLIC-GLISSER ET ZOOM) ──────────────────────
    def _open_lightbox(self, url, nom):
        self.log(f"Ouverture Lightbox pour '{nom}'")
        lb = tk.Toplevel(self)
        lb.title(nom)
        lb.configure(bg=BG)
        lb.geometry("900x720")
        lb.grab_set()

        header_frame = tk.Frame(lb, bg=BG)
        header_frame.pack(fill="x", pady=5)
        tk.Label(header_frame, text=nom, font=("Syne", 13, "bold"), bg=BG, fg=ACCENT2, pady=5).pack()
        tk.Label(header_frame, text="💡 Astuce : Zoomez à la molette, et cliquez-glissez pour vous déplacer sur l'image !", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack()

        img_container = tk.Frame(lb, bg=BG)
        img_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Remplacement du composant Label par un Canvas interactif pour le déplacement (panning)
        canvas = tk.Canvas(img_container, bg=BG, highlightthickness=0, cursor="fleur")
        canvas.pack(fill="both", expand=True)

        # Dessiner le texte de chargement temporaire
        canvas.create_text(450, 260, text="⏳ Chargement de l'image haute définition…", font=("Syne", 14), fill=TEXT_DIM, tags="loading")

        # Centrage dynamique du texte de chargement lors d'un éventuel redimensionnement initial
        def on_canvas_configure(event):
            loading_items = canvas.find_withtag("loading")
            if loading_items:
                canvas.coords(loading_items[0], event.width // 2, event.height // 2)
        canvas.bind("<Configure>", on_canvas_configure)

        control_frame = tk.Frame(lb, bg=BG)
        control_frame.pack(fill="x", pady=10)

        self.current_img_data = None
        self.current_zoom_level = 1.0

        # Enregistrement des positions d'ancrage pour le clic-glisser (pan)
        lb.drag_x = 0
        lb.drag_y = 0

        def on_drag_start(event):
            lb.drag_x = event.x
            lb.drag_y = event.y

        def on_drag(event):
            dx = event.x - lb.drag_x
            dy = event.y - lb.drag_y
            # Déplacer l'élément image par rapport aux écarts souris
            canvas.move("img", dx, dy)
            lb.drag_x = event.x
            lb.drag_y = event.y

        # Liaison des événements de déplacement souris
        canvas.bind("<ButtonPress-1>", on_drag_start)
        canvas.bind("<B1-Motion>", on_drag)

        def adjust_zoom(factor, relative=True):
            if not self.current_img_data: return
            if relative: 
                self.current_zoom_level *= factor
            else: 
                self.current_zoom_level = factor
                # Replacer l'image exactement au centre lors d'un reset de zoom
                cw = canvas.winfo_width()
                ch = canvas.winfo_height()
                if cw <= 1: cw = 880
                if ch <= 1: ch = 500
                img_items = canvas.find_withtag("img")
                if img_items:
                    canvas.coords(img_items[0], cw // 2, ch // 2)

            self.current_zoom_level = max(0.1, min(self.current_zoom_level, 5.0))
            self.log(f"Zoom appliqué : {int(self.current_zoom_level * 100)}%")
            render_image()

        def render_image():
            if not self.current_img_data: return
            try:
                from PIL import ImageTk
                img_copy = self.current_img_data.copy()
                w, h = img_copy.size
                new_w = max(int(w * self.current_zoom_level), 1)
                new_h = max(int(h * self.current_zoom_level), 1)
                img_copy = img_copy.resize((new_w, new_h), 1)
                photo = ImageTk.PhotoImage(img_copy)
                self._img_refs.append(photo)

                canvas.delete("loading")
                img_items = canvas.find_withtag("img")
                
                # Si l'image existe déjà sur le Canvas, on met à jour ses pixels sans changer ses coordonnées (garde le pan)
                if img_items:
                    canvas.itemconfig(img_items[0], image=photo)
                else:
                    cw = canvas.winfo_width()
                    ch = canvas.winfo_height()
                    if cw <= 1: cw = 880
                    if ch <= 1: ch = 500
                    canvas.create_image(cw // 2, ch // 2, image=photo, anchor="center", tags="img")
            except Exception as e: 
                self.log(f"Erreur de rendu lors du zoom : {e}")

        def on_mouse_wheel(event):
            if event.num == 5 or event.delta < 0: adjust_zoom(0.9)
            elif event.num == 4 or event.delta > 0: adjust_zoom(1.1)

        tk.Button(control_frame, text="🔍+ Zoomer", font=FONT_LABEL, bg=BG3, fg=TEXT, relief="flat", padx=12, pady=6, activebackground=ACCENT, activeforeground="white", cursor="hand2", command=lambda: adjust_zoom(1.2)).pack(side="left", padx=10, expand=True)
        tk.Button(control_frame, text="🔍- Dézoomer", font=FONT_LABEL, bg=BG3, fg=TEXT, relief="flat", padx=12, pady=6, activebackground=ACCENT, activeforeground="white", cursor="hand2", command=lambda: adjust_zoom(0.8)).pack(side="left", padx=10, expand=True)
        tk.Button(control_frame, text="🔄 Original", font=FONT_LABEL, bg=BG3, fg=TEXT, relief="flat", padx=12, pady=6, activebackground=ACCENT, activeforeground="white", cursor="hand2", command=lambda: adjust_zoom(1.0, relative=False)).pack(side="left", padx=10, expand=True)
        tk.Button(control_frame, text="✕ Fermer", font=FONT_LABEL, bg=BG3, fg=TEXT, relief="flat", padx=12, pady=6, activebackground=DANGER, activeforeground="white", cursor="hand2", command=lb.destroy).pack(side="left", padx=10, expand=True)

        # Lier le zoom molette uniquement au survol de la zone image interactrice
        canvas.bind("<MouseWheel>", on_mouse_wheel)
        canvas.bind("<Button-4>", on_mouse_wheel)
        canvas.bind("<Button-5>", on_mouse_wheel)
        lb.bind("<Escape>", lambda e: lb.destroy())

        def fetch():
            try:
                from PIL import Image
                r = requests.get(url, timeout=20)
                r.raise_for_status()
                raw_img = Image.open(io.BytesIO(r.content))
                raw_img.thumbnail((840, 520))
                self.current_img_data = raw_img
                self.current_zoom_level = 1.0
                self.after(0, render_image)
                self.log(f"Image originale '{nom}' chargée et prête pour manipulation.")
            except ImportError:
                self.log("Erreur Pillow manquant lors du chargement lightbox.")
                canvas.delete("loading")
                canvas.create_text(450, 260, text="Installe Pillow :\npip install Pillow", font=FONT_SUB, fill=TEXT_DIM, tags="loading")
            except Exception as e:
                self.log(f"Erreur récupération image HD '{nom}' : {e}")
                canvas.delete("loading")
                canvas.create_text(450, 260, text=f"❌ Erreur : {e}", font=FONT_SUB, fill=DANGER, tags="loading")

        threading.Thread(target=fetch, daemon=True).start()

    # ── FICHIERS ──────────────────────────────────────────────────────────────
    def _populate_fichiers(self):
        parent = self.tab_fichiers
        for widget in parent.winfo_children(): widget.destroy()
        fichiers = [f for f in self.data.get("fichiers", []) if f.get("url")]

        if not fichiers:
            self._empty(parent, "Aucun fichier disponible.")
            return

        tk.Label(parent, text="Fichiers disponibles", font=("Syne", 12, "bold"), bg=BG, fg=ACCENT2, pady=14).pack()

        for item in fichiers:
            row = tk.Frame(parent, bg=BG2, pady=12, padx=16)
            row.pack(fill="x", padx=28, pady=5)
            tk.Label(row, text="📦", font=("Syne", 18), bg=BG2, fg=ACCENT).pack(side="left", padx=(0, 12))

            info = tk.Frame(row, bg=BG2)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=item["nom"], font=("Syne", 11, "bold"), bg=BG2, fg=TEXT, anchor="w").pack(anchor="w")
            tk.Label(info, text=item["url"], font=FONT_SMALL, bg=BG2, fg=TEXT_DIM, anchor="w").pack(anchor="w")

            btn = tk.Button(row, text="⬇ Télécharger", font=("Syne", 10, "bold"), bg=ACCENT, fg="white", relief="flat", activebackground=ACCENT2, cursor="hand2", padx=14, pady=6)
            btn.config(command=lambda u=item["url"], n=item["nom"], b=btn: self._download(u, n, b))
            btn.pack(side="right")

    def _download(self, url, nom, btn):
        save_path = filedialog.asksaveasfilename(initialfile=nom, title="Enregistrer sous…")
        if not save_path: return

        self.log(f"Démarrage téléchargement du fichier : '{nom}'")
        btn.config(text="⏳ En cours…", state="disabled", bg=TEXT_DIM)

        def fetch():
            try:
                r = requests.get(url, timeout=30, stream=True)
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                self.log(f"Fichier '{nom}' correctement enregistré à : {save_path}")
                self.after(0, lambda: btn.config(text="✅ Téléchargé", bg=SUCCESS, state="normal"))
            except Exception as e:
                self.log(f"Échec de téléchargement pour '{nom}' : {e}")
                self.after(0, lambda: btn.config(text="⬇ Télécharger", bg=ACCENT, state="normal"))
                self.after(0, lambda: messagebox.showerror("Erreur", f"Téléchargement échoué :\n{e}"))

        threading.Thread(target=fetch, daemon=True).start()

    # ── SUGGESTIONS ───────────────────────────────────────────────────────────
    def _populate_suggestions(self):
        parent = self.tab_suggestions
        for widget in parent.winfo_children(): widget.destroy()

        wrap = tk.Frame(parent, bg=BG)
        wrap.place(relx=.5, rely=.5, anchor="center")

        tk.Label(wrap, text="✉️  Envoyer une suggestion", font=("Syne", 15, "bold"), bg=BG, fg=ACCENT2).pack(anchor="w")
        tk.Label(wrap, text="Une idée, un retour ou un bug ? Remplis le formulaire ci-dessous.", font=FONT_SMALL, bg=BG, fg=TEXT_DIM, pady=6).pack(anchor="w")
        tk.Frame(wrap, bg=ACCENT, height=1).pack(fill="x", pady=(0, 18))

        tk.Label(wrap, text="Ton prénom (optionnel)", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(anchor="w")
        self.f_nom = tk.Entry(wrap, bg=BG2, fg=TEXT, font=FONT_SUB, relief="flat", insertbackground=TEXT, width=44)
        self.f_nom.pack(fill="x", ipady=6, pady=(4, 12))

        tk.Label(wrap, text="Type de message", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(anchor="w")
        self.f_type = ttk.Combobox(wrap, state="readonly", font=FONT_SUB, values=["💡 Suggestion", "👍 Retour positif", "🐛 Bug / Problème", "✏️ Autre"])
        self.f_type.current(0)
        self.f_type.pack(fill="x", pady=(4, 12))

        tk.Label(wrap, text="Message *", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(anchor="w")
        self.f_msg = tk.Text(wrap, bg=BG2, fg=TEXT, font=FONT_SUB, relief="flat", insertbackground=TEXT, width=44, height=6, padx=8, pady=8)
        self.f_msg.pack(fill="x", pady=(4, 16))

        self.btn_send = tk.Button(wrap, text="Envoyer ✉️", font=("Syne", 11, "bold"), bg=ACCENT, fg="white", relief="flat", activebackground=ACCENT2, activeforeground=BG, cursor="hand2", pady=10, command=self._send_mail)
        self.btn_send.pack(fill="x")

        self.lbl_feedback = tk.Label(wrap, text="", font=FONT_SMALL, bg=BG, fg=SUCCESS)
        self.lbl_feedback.pack(pady=(10, 0))

    def _send_mail(self):
        nom     = self.f_nom.get().strip()
        type_   = self.f_type.get()
        message = self.f_msg.get("1.0", "end").strip()

        if not message:
            self.lbl_feedback.config(text="⚠️ Le message ne peut pas être vide.", fg=DANGER)
            return

        subject = f"[Faster Homework] {type_}" + (f" — {nom}" if nom else "")
        body = f"Type : {type_}\n" + (f"De : {nom}\n" if nom else "") + f"\n{message}"

        self.log(f"Ouverture du client mail pour envoi de suggestion ({type_}).")
        mailto = f"mailto:{MAIL_TO}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        webbrowser.open(mailto)

        self.lbl_feedback.config(text="✅ Ton client mail va s'ouvrir !", fg=SUCCESS)
        self.f_msg.delete("1.0", "end")
        self.f_nom.delete(0, "end")

    def _empty(self, parent, msg):
        tk.Label(parent, text=msg, font=FONT_SUB, bg=BG, fg=TEXT_DIM).pack(pady=50)


if __name__ == "__main__":
    app = App()
    app.mainloop()