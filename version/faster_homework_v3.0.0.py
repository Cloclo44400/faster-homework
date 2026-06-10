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
import os
import platform

# ─── CONFIGURATION DES URLS DE CENTRALISATION ────────────────────────────────
TEXTE_JSON_URL    = "https://raw.githubusercontent.com/Cloclo44400/faster-homework/main/texte.json"
IMAGE_JSON_URL    = "https://raw.githubusercontent.com/Cloclo44400/faster-homework/main/image.json"
DOCUMENT_JSON_URL = "https://raw.githubusercontent.com/Cloclo44400/faster-homework/main/document.json"

MAIL_TO           = "suggestion.retoure.44@proton.me"

# Liste des langues disponibles pour le traducteur (Nom: Code API)
LANG_MAP = {
    "Français": "fr",
    "Anglais": "en",
    "Espagnol": "es",
    "Allemand": "de",
    "Italien": "it",
    "Portugais": "pt",
    "Néerlandais": "nl"
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
WARNING     = "#f59e0b"
FONT_TITLE  = ("Syne", 20, "bold")
FONT_SUB    = ("Syne", 11)
FONT_LABEL  = ("Syne", 10)
FONT_SMALL  = ("Syne", 9)
FONT_MONO   = ("Consolas", 11)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Faster Homework v3.0.0")
        self.geometry("1150x660")
        self.minsize(720, 520)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.data      = None
        self._img_refs = []
        
        # Suivi des erreurs de chargement pour chaque fichier JSON
        self.load_errors = {}
        
        # Mode Développeur
        self.dev_mode = False
        self.dev_pane = None
        self.console_text = None

        self._build_ui()
        self._load_data()
        
        self.bind("<F1>", self._toggle_dev_mode)
        self.log("Application v3.0.0 prête. Mode dév disponible via F1.")

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
        tk.Label(header, text="v3.0.0", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(side="left", padx=(6, 0), pady=(6, 0))

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
        self.tab_traduction  = tk.Frame(self.nb, bg=BG) # Onglet de traduction
        self.tab_suggestions = tk.Frame(self.nb, bg=BG)

        self.nb.add(self.tab_textes,      text="  📄  Textes  ")
        self.nb.add(self.tab_images,      text="  🖼️  Images  ")
        self.nb.add(self.tab_fichiers,    text="  📦  Documents  ")
        self.nb.add(self.tab_traduction,  text="  🌐  Traduction  ")
        self.nb.add(self.tab_suggestions, text="  ✉️  Suggestions  ")
        
        self._populate_traduction()

    # ── ONGLET TRADUCTION SANS IA (RAPIDE & INSTANTANÉ) ──────────────────────
    def _populate_traduction(self):
        parent = self.tab_traduction
        
        # En-tête
        header_trad = tk.Frame(parent, bg=BG, pady=10)
        header_trad.pack(fill="x", padx=28)
        
        tk.Label(header_trad, text="🌐 Traducteur de Cours", font=("Syne", 14, "bold"), bg=BG, fg=ACCENT2).pack(anchor="w")
        tk.Label(header_trad, text="Saisis ou colle ton texte pour le traduire.", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(anchor="w")

        # Boîte principale de traduction
        main_box = tk.Frame(parent, bg=BG2, padx=15, pady=15)
        main_box.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        # Barre des sélecteurs de langues
        sel_bar = tk.Frame(main_box, bg=BG2)
        sel_bar.pack(fill="x", pady=(0, 12))

        tk.Label(sel_bar, text="De :", font=FONT_LABEL, bg=BG2, fg=TEXT).pack(side="left")
        self.combo_src = ttk.Combobox(sel_bar, state="readonly", font=FONT_SMALL, width=12, values=list(LANG_MAP.keys()))
        self.combo_src.set("Français")
        self.combo_src.pack(side="left", padx=5)

        btn_swap = tk.Button(sel_bar, text="⇄", font=("Syne", 10, "bold"), bg=BG3, fg=ACCENT2, relief="flat", padx=8, cursor="hand2", command=self._swap_languages)
        btn_swap.pack(side="left", padx=5)

        tk.Label(sel_bar, text="Vers :", font=FONT_LABEL, bg=BG2, fg=TEXT).pack(side="left")
        self.combo_tgt = ttk.Combobox(sel_bar, state="readonly", font=FONT_SMALL, width=12, values=list(LANG_MAP.keys()))
        self.combo_tgt.set("Anglais")
        self.combo_tgt.pack(side="left", padx=5)

        self.btn_translate = tk.Button(sel_bar, text="Traduire 🚀", font=("Syne", 9, "bold"), bg=ACCENT, fg="white", relief="flat", padx=15, cursor="hand2", command=self._start_translation)
        self.btn_translate.pack(side="right")

        # Panneaux de texte (Gauche: Source, Droite: Cible)
        panes = tk.PanedWindow(main_box, orient="horizontal", bg=BG2, sashwidth=6, sashrelief="flat")
        panes.pack(fill="both", expand=True)

        left_f = tk.Frame(panes, bg=BG2)
        right_f = tk.Frame(panes, bg=BG2)
        panes.add(left_f, minsize=200, stretch="always")
        panes.add(right_f, minsize=200, stretch="always")

        # Zone de saisie source
        tk.Label(left_f, text="Texte d'origine :", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(0, 4))
        self.txt_src = tk.Text(left_f, bg=BG, fg=TEXT, font=FONT_MONO, wrap="word", relief="flat", insertbackground=TEXT, padx=8, pady=8)
        self.txt_src.pack(fill="both", expand=True, padx=(0, 5))

        # Zone de résultat traduit
        tk.Label(right_f, text="Texte traduit :", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(0, 4))
        self.txt_tgt = tk.Text(right_f, bg=BG, fg=TEXT, font=FONT_MONO, wrap="word", relief="flat", state="disabled", padx=8, pady=8)
        self.txt_tgt.pack(fill="both", expand=True, padx=(5, 0))

    def _swap_languages(self):
        src, tgt = self.combo_src.get(), self.combo_tgt.get()
        self.combo_src.set(tgt)
        self.combo_tgt.set(src)
        self.log(f"Inversion des langues : {src} ⇄ {tgt}")

    def _start_translation(self):
        text_to_translate = self.txt_src.get("1.0", "end").strip()
        if not text_to_translate:
            return

        self.btn_translate.config(state="disabled", text="⏳ Traduction…", bg=BG3)
        self.txt_tgt.config(state="normal")
        self.txt_tgt.delete("1.0", "end")
        self.txt_tgt.insert("end", "Traduction en cours sur le serveur… 🌐")
        self.txt_tgt.config(state="disabled")

        src_lang = LANG_MAP.get(self.combo_src.get(), "fr")
        tgt_lang = LANG_MAP.get(self.combo_tgt.get(), "en")

        self.log(f"Requête de traduction lancée ({src_lang} -> {tgt_lang})")
        threading.Thread(target=self._async_translate, args=(text_to_translate, src_lang, tgt_lang), daemon=True).start()

    def _async_translate(self, text, src, tgt):
        try:
            # Utilisation de l'API publique et gratuite MyMemory
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": text,
                "langpair": f"{src}|{tgt}"
            }
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            res_data = r.json()
            
            translated_text = res_data.get("responseData", {}).get("translatedText", "")
            if not translated_text:
                translated_text = "[Erreur] Aucun résultat retourné par l'API."

            self.log("Traduction réussie et récupérée avec succès.")
            self.after(0, lambda: self._on_translation_success(translated_text))
        except Exception as e:
            self.log(f"Échec de la traduction réseau : {e}")
            self.after(0, lambda: self._on_translation_success(f"[Erreur de connexion] Impossible de joindre le traducteur en ligne :\n{e}"))

    def _on_translation_success(self, result):
        self.txt_tgt.config(state="normal")
        self.txt_tgt.delete("1.0", "end")
        self.txt_tgt.insert("end", result)
        self.txt_tgt.config(state="disabled")
        self.btn_translate.config(state="normal", text="Traduire 🚀", bg=ACCENT)

    # ── ACTION CLAVIER F1 (MODE DEVELOPPEUR) ──────────────────────────────────
    def _toggle_dev_mode(self, event=None):
        self.dev_mode = not self.dev_mode
        if self.dev_mode: self._build_dev_pane()
        else:
            if self.dev_pane:
                self.main_split.forget(self.dev_pane)
                self.dev_pane.destroy()
                self.dev_pane, self.console_text = None, None

    def _build_dev_pane(self):
        self.dev_pane = tk.Frame(self.main_split, bg=BG2, padx=10, pady=10)
        self.main_split.add(self.dev_pane, minsize=320, stretch="never")
        tk.Label(self.dev_pane, text="🛠️ Mode Développeur", font=("Syne", 12, "bold"), bg=BG2, fg=ACCENT2).pack(anchor="w", pady=(0, 5))
        
        dev_nb = ttk.Notebook(self.dev_pane)
        dev_nb.pack(fill="both", expand=True)
        tab_console = tk.Frame(dev_nb, bg=BG2)
        dev_nb.add(tab_console, text="Console")

        self.console_text = tk.Text(tab_console, bg=BG, fg=SUCCESS, font=FONT_MONO, wrap="word", relief="flat", state="disabled", padx=8, pady=8)
        self.console_text.pack(fill="both", expand=True)
        
        tab_debug = tk.Frame(dev_nb, bg=BG2, padx=8, pady=10)
        dev_nb.add(tab_debug, text="Outils")
        tk.Button(tab_debug, text="Rafraîchir les données JSON", font=FONT_SMALL, bg=ACCENT, fg="white", relief="flat", command=self._load_data, pady=6).pack(fill="x", pady=4)

    # ── STATUS ────────────────────────────────────────────────────────────────
    def _set_status(self, txt, color):
        self.status_lbl.config(text=txt, fg=color)
        self.status_dot.config(fg=color)

    # ── CHARGEMENT DE TOUTES LES SOURCES JSON DÉCOUPÉES ───────────────────────
    def _load_data(self):
        self._set_status("Connexion…", TEXT_DIM)
        threading.Thread(target=self._fetch_split_data, daemon=True).start()

    def _fetch_split_data(self):
        merged_data = {"textes": [], "images": [], "documents": []}
        targets = [
            ("Textes", TEXTE_JSON_URL, "textes"),
            ("Images", IMAGE_JSON_URL, "images"),
            ("Documents", DOCUMENT_JSON_URL, "documents")
        ]
        
        self.load_errors = {}  # Réinitialiser les erreurs à chaque chargement
        success_count = 0
        
        for name, url, key in targets:
            self.log(f"Téléchargement de {name} depuis: {url}")
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                content = r.json()
                if isinstance(content, dict) and key in content:
                    merged_data[key] = content[key]
                success_count += 1
            except Exception as e:
                self.log(f"Erreur de chargement pour {name}: {e}")
                self.load_errors[key] = str(e)

        if success_count > 0:
            self.data = merged_data
            self.after(0, self._populate)
            self.after(0, lambda: self._set_status("Connecté", SUCCESS))
        else:
            self.after(0, lambda: self._set_status("Erreur", DANGER))
            self.after(0, lambda: messagebox.showerror("Erreur", "Impossible de charger les fichiers de configuration JSON."))

    def _populate(self):
        self._populate_textes()
        self._populate_images()
        self._populate_documents() 
        self._populate_suggestions()

    # ── TEXTES ────────────────────────────────────────────────────────────────
    def _populate_textes(self):
        parent = self.tab_textes
        for widget in parent.winfo_children(): widget.destroy()
        
        if "textes" in self.load_errors:
            self._empty(parent, f"⚠️ Erreur de chargement du fichier JSON :\n\n{self.load_errors['textes']}")
            return

        textes = [t for t in self.data.get("textes", []) if t.get("url")]

        if not textes:
            self._empty(parent, "Aucun texte disponible.")
            return

        pane = tk.PanedWindow(parent, orient="horizontal", bg=BG, sashwidth=4, sashrelief="flat")
        pane.pack(fill="both", expand=True)

        left, right = tk.Frame(pane, bg=BG2, width=200), tk.Frame(pane, bg=BG)
        pane.add(left, minsize=160), pane.add(right, minsize=300)

        tk.Label(left, text="Articles", font=("Syne", 9, "bold"), bg=BG2, fg=ACCENT2, pady=10).pack(fill="x", padx=10)
        txt_area = tk.Text(right, bg=BG2, fg=TEXT, font=FONT_MONO, wrap="word", relief="flat", padx=14, pady=14, state="disabled", insertbackground=TEXT)
        scroll = tk.Scrollbar(right, command=txt_area.yview, bg=BG2, troughcolor=BG2)
        txt_area.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y"), txt_area.pack(fill="both", expand=True)

        def load_text(url):
            txt_area.config(state="normal")
            txt_area.delete("1.0", "end")
            txt_area.insert("end", "Chargement…")
            txt_area.config(state="disabled")
            def fetch():
                try: content = requests.get(url, timeout=10).text
                except: content = "[Erreur de chargement]"
                self.after(0, lambda: (txt_area.config(state="normal"), txt_area.delete("1.0", "end"), txt_area.insert("end", content), txt_area.config(state="disabled")))
            threading.Thread(target=fetch, daemon=True).start()

        for item in textes:
            b = tk.Button(left, text=item["nom"], font=FONT_LABEL, bg=BG2, fg=TEXT, relief="flat", anchor="w", activebackground=ACCENT, activeforeground="white", cursor="hand2", padx=12, pady=7)
            b.config(command=lambda u=item["url"]: load_text(u))
            b.pack(fill="x", padx=6, pady=2)

    # ── IMAGES ────────────────────────────────────────────────────────────────
    def _populate_images(self):
        parent = self.tab_images
        for widget in parent.winfo_children(): widget.destroy()
        
        if "images" in self.load_errors:
            self._empty(parent, f"⚠️ Erreur de chargement du fichier JSON :\n\n{self.load_errors['images']}")
            return

        images = [i for i in self.data.get("images", []) if i.get("url")]

        if not images:
            self._empty(parent, "Aucune image disponible.")
            return

        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview, bg=BG2)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"), canvas.pack(side="left", fill="both", expand=True)

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

            url, nom = item["url"], item["nom"]
            cell.bind("<Button-1>",  lambda e, u=url, n=nom: self._open_lightbox(u, n))
            lbl_img.bind("<Button-1>", lambda e, u=url, n=nom: self._open_lightbox(u, n))
            threading.Thread(target=self._load_image, args=(url, lbl_img), daemon=True).start()

        for c in range(cols): grid_frame.columnconfigure(c, weight=1)

    def _load_image(self, url, label):
        try:
            from PIL import Image, ImageTk
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content))
            img.thumbnail((200, 160))
            photo = ImageTk.PhotoImage(img)
            self._img_refs.append(photo)
            self.after(0, lambda: label.config(image=photo, text=""))
        except:
            self.after(0, lambda: label.config(text="❌", font=FONT_SMALL, fg=DANGER))

    # ── LIGHTBOX (AVEC DEPLACEMENT CLIC-GLISSER ET ZOOM CORRIGÉ) ──────────────
    def _open_lightbox(self, url, nom):
        self.log(f"Ouverture de la Lightbox interactive pour '{nom}'")
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

        # Utilisation du Canvas interactif pour le déplacement (panning)
        canvas = tk.Canvas(img_container, bg=BG, highlightthickness=0, cursor="fleur")
        canvas.pack(fill="both", expand=True)

        canvas.create_text(450, 260, text="⏳ Chargement de l'image haute définition…", font=("Syne", 14), fill=TEXT_DIM, tags="loading")

        def on_canvas_configure(event):
            loading_items = canvas.find_withtag("loading")
            if loading_items:
                canvas.coords(loading_items[0], event.width // 2, event.height // 2)
        canvas.bind("<Configure>", on_canvas_configure)

        control_frame = tk.Frame(lb, bg=BG)
        control_frame.pack(fill="x", pady=10)

        self.current_img_data = None
        self.current_zoom_level = 1.0

        lb.drag_x = 0
        lb.drag_y = 0

        def on_drag_start(event):
            lb.drag_x = event.x
            lb.drag_y = event.y

        def on_drag(event):
            dx = event.x - lb.drag_x
            dy = event.y - lb.drag_y
            canvas.move("img", dx, dy)
            lb.drag_x = event.x
            lb.drag_y = event.y

        canvas.bind("<ButtonPress-1>", on_drag_start)
        canvas.bind("<B1-Motion>", on_drag)

        def adjust_zoom(factor, relative=True):
            if not self.current_img_data: return
            if relative: 
                self.current_zoom_level *= factor
            else: 
                self.current_zoom_level = factor
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

    # ── DOCUMENTS ─────────────────────────────────────────────────────────────
    def _populate_documents(self):
        parent = self.tab_fichiers
        for widget in parent.winfo_children(): widget.destroy()
        
        # S'il y a eu une erreur d'analyse ou de syntaxe dans document.json
        if "documents" in self.load_errors:
            self._empty(parent, f"⚠️ Erreur de chargement du fichier JSON :\n\n{self.load_errors['documents']}")
            return

        # Lecture correcte de la clé "documents" issue de document.json
        documents = [d for d in self.data.get("documents", []) if d.get("url")]

        if not documents:
            self._empty(parent, "Aucun document disponible.")
            return

        tk.Label(parent, text="Documents de cours disponibles", font=("Syne", 12, "bold"), bg=BG, fg=ACCENT2, pady=14).pack()
        for item in documents:
            row = tk.Frame(parent, bg=BG2, pady=12, padx=16)
            row.pack(fill="x", padx=28, pady=5)
            tk.Label(row, text="📦", font=("Syne", 18), bg=BG2, fg=ACCENT).pack(side="left", padx=(0, 12))

            info = tk.Frame(row, bg=BG2)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=item["nom"], font=("Syne", 11, "bold"), bg=BG2, fg=TEXT, anchor="w").pack(anchor="w")
            
            btn = tk.Button(row, text="⬇ Télécharger", font=("Syne", 10, "bold"), bg=ACCENT, fg="white", relief="flat", padx=14, pady=6)
            btn.config(command=lambda u=item["url"], n=item["nom"], b=btn: self._download(u, n, b))
            btn.pack(side="right")

    def _download(self, url, nom, btn):
        save_path = filedialog.asksaveasfilename(initialfile=nom, title="Enregistrer sous…")
        if not save_path: return
        btn.config(text="⏳ En cours…", state="disabled", bg=TEXT_DIM)
        def fetch():
            try:
                r = requests.get(url, timeout=30, stream=True)
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                self.after(0, lambda: btn.config(text="✅ Téléchargé", bg=SUCCESS, state="normal"))
            except:
                self.after(0, lambda: (btn.config(text="⬇ Télécharger", bg=ACCENT, state="normal"), messagebox.showerror("Erreur", "Échec.")))
        threading.Thread(target=fetch, daemon=True).start()

    # ── SUGGESTIONS ───────────────────────────────────────────────────────────
    def _populate_suggestions(self):
        parent = self.tab_suggestions
        for widget in parent.winfo_children(): widget.destroy()
        wrap = tk.Frame(parent, bg=BG)
        wrap.place(relx=.5, rely=.5, anchor="center")

        tk.Label(wrap, text="✉️  Envoyer une suggestion", font=("Syne", 15, "bold"), bg=BG, fg=ACCENT2).pack(anchor="w")
        tk.Frame(wrap, bg=ACCENT, height=1).pack(fill="x", pady=(4, 18))

        tk.Label(wrap, text="Ton prénom (optionnel)", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(anchor="w")
        self.f_nom = tk.Entry(wrap, bg=BG2, fg=TEXT, font=FONT_SUB, relief="flat", width=44, insertbackground=TEXT)
        self.f_nom.pack(fill="x", ipady=6, pady=(4, 12))

        tk.Label(wrap, text="Message *", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(anchor="w")
        self.f_msg = tk.Text(wrap, bg=BG2, fg=TEXT, font=FONT_SUB, relief="flat", width=44, height=6, padx=8, pady=8, insertbackground=TEXT)
        self.f_msg.pack(fill="x", pady=(4, 16))

        tk.Button(wrap, text="Envoyer ✉️", font=("Syne", 11, "bold"), bg=ACCENT, fg="white", relief="flat", pady=10, command=self._send_mail).pack(fill="x")
        self.lbl_feedback = tk.Label(wrap, text="", font=FONT_SMALL, bg=BG, fg=SUCCESS)
        self.lbl_feedback.pack(pady=(10, 0))

    def _send_mail(self):
        nom, message = self.f_nom.get().strip(), self.f_msg.get("1.0", "end").strip()
        if not message: return
        subject = f"[Faster Homework] Suggestion" + (f" — {nom}" if nom else "")
        body = f"De : {nom}\n\n{message}"
        webbrowser.open(f"mailto:{MAIL_TO}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}")
        self.f_msg.delete("1.0", "end")

    def _empty(self, parent, msg):
        tk.Label(parent, text=msg, font=FONT_SUB, bg=BG, fg=TEXT_DIM).pack(pady=50)


if __name__ == "__main__":
    app = App()
    app.mainloop()