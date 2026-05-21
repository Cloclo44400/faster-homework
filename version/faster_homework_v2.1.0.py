import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import io
import webbrowser
import urllib.parse
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────────
DATA_JSON_URL = "https://raw.githubusercontent.com/Cloclo44400/faster-homework/main/data.json"
MAIL_TO       = "suggestion.retoure.44@proton.me"

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
        self.title("Faster Homework v2.1.0")
        self.geometry("1100x640")  # Élargi par défaut pour accueillir la console dév
        self.minsize(720, 520)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.data      = None
        self._img_refs = []
        
        # Mode Développeur
        self.dev_mode = False
        self.dev_pane = None
        self.console_text = None

        self._build_ui()
        self._load_data()
        
        # Liaison de la touche F1 pour le Mode Développeur
        self.bind("<F1>", self._toggle_dev_mode)
        self.log("Application initialisée. Appuyez sur F1 pour activer le mode développeur.")

    # ── CONSOLE DE LOGS ───────────────────────────────────────────────────────
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        print(log_msg.strip())  # Écrit aussi dans la vraie console python
        
        if self.console_text and self.console_text.winfo_exists():
            self.console_text.config(state="normal")
            self.console_text.insert("end", log_msg)
            self.console_text.see("end")
            self.console_text.config(state="disabled")

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Frame principale pour diviser entre l'App et la Console Dev
        self.main_split = tk.PanedWindow(self, orient="horizontal", bg=BG, sashwidth=6, sashrelief="flat")
        self.main_split.pack(fill="both", expand=True)

        # Côté gauche (L'application elle-même)
        self.app_frame = tk.Frame(self.main_split, bg=BG)
        self.main_split.add(self.app_frame, minsize=500, stretch="always")

        # Header
        header = tk.Frame(self.app_frame, bg=BG, pady=16)
        header.pack(fill="x", padx=28)

        tk.Label(header, text="⚡ Faster Homework", font=FONT_TITLE,
                 bg=BG, fg=ACCENT2).pack(side="left")
        tk.Label(header, text="v2.1.0", font=FONT_SMALL,
                 bg=BG, fg=TEXT_DIM).pack(side="left", padx=(6, 0), pady=(6, 0))

        self.status_dot = tk.Label(header, text="●", font=("Syne", 13),
                                   bg=BG, fg=TEXT_DIM)
        self.status_dot.pack(side="right", padx=(0, 4))
        self.status_lbl = tk.Label(header, text="Chargement…", font=FONT_SMALL,
                                   bg=BG, fg=TEXT_DIM)
        self.status_lbl.pack(side="right")

        tk.Frame(self.app_frame, bg=ACCENT, height=2).pack(fill="x", padx=28)

        # Notebook
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook",     background=BG,  borderwidth=0)
        style.configure("TNotebook.Tab", background=BG2, foreground=TEXT_DIM,
                        font=FONT_SUB,   padding=[14, 7])
        style.map("TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", ACCENT2)])

        self.nb = ttk.Notebook(self.app_frame)
        self.nb.pack(fill="both", expand=True, padx=20, pady=14)

        self.tab_textes      = tk.Frame(self.nb, bg=BG)
        self.tab_images      = tk.Frame(self.nb, bg=BG)
        self.tab_fichiers    = tk.Frame(self.nb, bg=BG)
        self.tab_suggestions = tk.Frame(self.nb, bg=BG)

        self.nb.add(self.tab_textes,      text="  📄  Textes  ")
        self.nb.add(self.tab_images,      text="  🖼️  Images  ")
        self.nb.add(self.tab_fichiers,    text="  📦  Fichiers  ")
        self.nb.add(self.tab_suggestions, text="  ✉️  Suggestions  ")

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

        # Titre Dev
        tk.Label(self.dev_pane, text="🛠️ Mode Développeur", font=("Syne", 12, "bold"),
                 bg=BG2, fg=ACCENT2).pack(anchor="w", pady=(0, 5))
        
        # Notebook interne pour séparer Console et Outils de debug
        dev_nb = ttk.Notebook(self.dev_pane)
        dev_nb.pack(fill="both", expand=True)

        # Onglet 1 : Console
        tab_console = tk.Frame(dev_nb, bg=BG2)
        dev_nb.add(tab_console, text="Console")

        self.console_text = tk.Text(tab_console, bg=BG, fg=SUCCESS, font=FONT_MONO,
                                    wrap="word", relief="flat", state="disabled", padx=8, pady=8)
        scroll_c = tk.Scrollbar(tab_console, command=self.console_text.yview, bg=BG, troughcolor=BG2)
        self.console_text.config(yscrollcommand=scroll_c.set)
        
        scroll_c.pack(side="right", fill="y")
        self.console_text.pack(fill="both", expand=True)

        # Onglet 2 : Outils de Debug
        tab_debug = tk.Frame(dev_nb, bg=BG2, padx=8, pady=10)
        dev_nb.add(tab_debug, text="Debug / Outils")

        tk.Label(tab_debug, text="Actions de test :", font=FONT_LABEL, bg=BG2, fg=TEXT).pack(anchor="w", pady=(0, 10))

        btn_reload = tk.Button(tab_debug, text="Rafraîchir les données", font=FONT_SMALL,
                               bg=ACCENT, fg="white", relief="flat", activebackground=ACCENT2, cursor="hand2",
                               command=self._load_data, pady=6)
        btn_reload.pack(fill="x", pady=4)

        btn_test_err = tk.Button(tab_debug, text="Simuler une erreur réseau", font=FONT_SMALL,
                                 bg=DANGER, fg="white", relief="flat", activebackground=ACCENT2, cursor="hand2",
                                 command=lambda: self.log("[DEBUG TEST] Erreur réseau 404 simulée sur l'API."), pady=6)
        btn_test_err.pack(fill="x", pady=4)

        btn_clear_console = tk.Button(tab_debug, text="Effacer la console", font=FONT_SMALL,
                                      bg=BG3, fg=TEXT, relief="flat", activebackground=ACCENT2, cursor="hand2",
                                      command=self._clear_console, pady=6)
        btn_clear_console.pack(fill="x", pady=4)

        # Rediriger l'historique vers la nouvelle console
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
            self.after(0, lambda: messagebox.showerror(
                "Erreur", f"Impossible de charger data.json :\n{e}"))

    def _populate(self):
        self.log("Génération des éléments de l'interface graphique (onglets)...")
        self._populate_textes()
        self._populate_images()
        self._populate_fichiers()
        self._populate_suggestions()

    # ── TEXTES ────────────────────────────────────────────────────────────────
    def _populate_textes(self):
        parent = self.tab_textes
        # Vider l'ancien contenu si ré-exécuté
        for widget in parent.winfo_children():
            widget.destroy()

        textes = [t for t in self.data.get("textes", []) if t.get("url")]

        if not textes:
            self._empty(parent, "Aucun texte disponible.")
            return

        pane = tk.PanedWindow(parent, orient="horizontal", bg=BG,
                              sashwidth=4, sashrelief="flat")
        pane.pack(fill="both", expand=True)

        left  = tk.Frame(pane, bg=BG2, width=200)
        right = tk.Frame(pane, bg=BG)
        pane.add(left,  minsize=160)
        pane.add(right, minsize=300)

        tk.Label(left, text="Articles", font=("Syne", 9, "bold"),
                 bg=BG2, fg=ACCENT2, pady=10).pack(fill="x", padx=10)

        txt_area = tk.Text(right, bg=BG2, fg=TEXT, font=FONT_MONO,
                           wrap="word", relief="flat", padx=14, pady=14,
                           state="disabled", insertbackground=TEXT)
        scroll = tk.Scrollbar(right, command=txt_area.yview, bg=BG2,
                              troughcolor=BG2, relief="flat")
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
                self.after(0, lambda: (
                    txt_area.config(state="normal"),
                    txt_area.delete("1.0", "end"),
                    txt_area.insert("end", content),
                    txt_area.config(state="disabled")
                ))
            threading.Thread(target=fetch, daemon=True).start()

        for item in textes:
            b = tk.Button(left, text=item["nom"], font=FONT_LABEL,
                          bg=BG2, fg=TEXT, relief="flat", anchor="w",
                          activebackground=ACCENT, activeforeground="white",
                          cursor="hand2", padx=12, pady=7)
            b.config(command=lambda u=item["url"], n=item["nom"]: load_text(n, u))
            b.pack(fill="x", padx=6, pady=2)

    # ── IMAGES ────────────────────────────────────────────────────────────────
    def _populate_images(self):
        parent = self.tab_images
        for widget in parent.winfo_children():
            widget.destroy()

        images = [i for i in self.data.get("images", []) if i.get("url")]

        if not images:
            self._empty(parent, "Aucune image disponible.")
            return

        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview,
                           bg=BG2, troughcolor=BG2, relief="flat")
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        grid_frame = tk.Frame(canvas, bg=BG)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        grid_frame.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        cols = 3
        for i, item in enumerate(images):
            cell = tk.Frame(grid_frame, bg=BG2, padx=8, pady=8,
                            cursor="hand2")
            cell.grid(row=i // cols, column=i % cols, padx=10, pady=10,
                      sticky="nsew")

            lbl_img = tk.Label(cell, bg=BG2, text="⏳",
                               font=("Syne", 24), fg=TEXT_DIM)
            lbl_img.pack()
            tk.Label(cell, text=item["nom"], font=FONT_SMALL,
                     bg=BG2, fg=TEXT_DIM).pack()

            url = item["url"]
            nom = item["nom"]

            # Clic → lightbox
            cell.bind("<Button-1>",  lambda e, u=url, n=nom: self._open_lightbox(u, n))
            lbl_img.bind("<Button-1>", lambda e, u=url, n=nom: self._open_lightbox(u, n))

            threading.Thread(target=self._load_image,
                             args=(url, lbl_img, nom), daemon=True).start()

        for c in range(cols):
            grid_frame.columnconfigure(c, weight=1)

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
            self.after(0, lambda: label.config(
                text="📷\npip install Pillow",
                font=FONT_SMALL, fg=TEXT_DIM))
        except Exception as e:
            self.log(f"Erreur rendu miniature pour '{nom}' : {e}")
            self.after(0, lambda: label.config(text="❌", font=FONT_SMALL, fg=DANGER))

    # ── LIGHTBOX (AVEC FONCTION ZOOM MODIFIÉE) ────────────────────────────────
    def _open_lightbox(self, url, nom):
        self.log(f"Ouverture Lightbox pour '{nom}'")
        lb = tk.Toplevel(self)
        lb.title(nom)
        lb.configure(bg=BG)
        lb.geometry("900x720")
        lb.grab_set()

        # En-tête de la Lightbox
        header_frame = tk.Frame(lb, bg=BG)
        header_frame.pack(fill="x", pady=5)
        
        tk.Label(header_frame, text=nom, font=("Syne", 13, "bold"),
                 bg=BG, fg=ACCENT2, pady=5).pack()

        # Label d'instruction pour zoomer
        tk.Label(header_frame, text="💡 Astuce : Utilisez la Molette de la souris ou les boutons ci-dessous pour zoomer !",
                 font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack()

        # Zone d'image avec Canvas pour permettre le scroll/pan si l'image dépasse
        img_container = tk.Frame(lb, bg=BG)
        img_container.pack(fill="both", expand=True, padx=10, pady=5)

        lbl = tk.Label(img_container, bg=BG, text="⏳ Chargement de l'image haute définition…",
                       font=("Syne", 14), fg=TEXT_DIM)
        lbl.pack(expand=True)

        # Boutons de contrôle (Zoom + / - / Reset / Fermer)
        control_frame = tk.Frame(lb, bg=BG)
        control_frame.pack(fill="x", pady=10)

        # Variables d'état pour la gestion du zoom de l'image courante
        self.current_img_data = None
        self.current_zoom_level = 1.0

        def adjust_zoom(factor, relative=True):
            if not self.current_img_data:
                return
            
            if relative:
                self.current_zoom_level *= factor
            else:
                self.current_zoom_level = factor # Reset ou valeur brute
                
            # Bornes limites de zoom (10% à 500%)
            self.current_zoom_level = max(0.1, min(self.current_zoom_level, 5.0))
            self.log(f"Zoom appliqué : {int(self.current_zoom_level * 100)}%")
            render_image()

        def render_image():
            if not self.current_img_data:
                return
            try:
                from PIL import ImageTk
                # Copie originale pour redimensionner proprement à chaque fois
                img_copy = self.current_img_data.copy()
                
                # Appliquer la nouvelle taille basée sur le zoom
                w, h = img_copy.size
                new_w = max(int(w * self.current_zoom_level), 1)
                new_h = max(int(h * self.current_zoom_level), 1)
                
                img_copy = img_copy.resize((new_w, new_h), 1) # Image.Resampling.LANCZOS ou antialias basique
                photo = ImageTk.PhotoImage(img_copy)
                
                self._img_refs.append(photo) # Garde en mémoire pour éviter le garbage collection
                lbl.config(image=photo, text="")
            except Exception as e:
                self.log(f"Erreur de rendu lors du zoom : {e}")

        # Molette souris sur la fenêtre pour zoomer
        def on_mouse_wheel(event):
            # Windows & macOS / Linux gèrent l'événement différemment
            if event.num == 5 or event.delta < 0:
                adjust_zoom(0.9) # Dézoome
            elif event.num == 4 or event.delta > 0:
                adjust_zoom(1.1) # Zoome

        # Configuration des contrôles graphiques
        btn_zoom_in = tk.Button(control_frame, text="🔍+ Zoomer", font=FONT_LABEL,
                               bg=BG3, fg=TEXT, relief="flat", padx=12, pady=6,
                               activebackground=ACCENT, activeforeground="white",
                               cursor="hand2", command=lambda: adjust_zoom(1.2))
        btn_zoom_in.pack(side="left", padx=10, expand=True)

        btn_zoom_out = tk.Button(control_frame, text="🔍- Dézoomer", font=FONT_LABEL,
                                bg=BG3, fg=TEXT, relief="flat", padx=12, pady=6,
                                activebackground=ACCENT, activeforeground="white",
                                cursor="hand2", command=lambda: adjust_zoom(0.8))
        btn_zoom_out.pack(side="left", padx=10, expand=True)

        btn_reset = tk.Button(control_frame, text="🔄 Original", font=FONT_LABEL,
                              bg=BG3, fg=TEXT, relief="flat", padx=12, pady=6,
                              activebackground=ACCENT, activeforeground="white",
                              cursor="hand2", command=lambda: adjust_zoom(1.0, relative=False))
        btn_reset.pack(side="left", padx=10, expand=True)

        btn_close = tk.Button(control_frame, text="✕ Fermer", font=FONT_LABEL,
                             bg=BG3, fg=TEXT, relief="flat", padx=12, pady=6,
                             activebackground=DANGER, activeforeground="white",
                             cursor="hand2", command=lb.destroy)
        btn_close.pack(side="left", padx=10, expand=True)

        # Liaisons événements pour le zoom molette
        lb.bind("<MouseWheel>", on_mouse_wheel)  # Pour Windows/macOS
        lb.bind("<Button-4>", on_mouse_wheel)    # Pour Linux (scroll up)
        lb.bind("<Button-5>", on_mouse_wheel)    # Pour Linux (scroll down)
        lb.bind("<Escape>", lambda e: lb.destroy())

        def fetch():
            try:
                from PIL import Image
                r = requests.get(url, timeout=20)
                r.raise_for_status()
                # Charger l'image brute en mémoire sans altération pour le zoom
                raw_img = Image.open(io.BytesIO(r.content))
                
                # Taille initiale adaptée pour l'écran
                raw_img.thumbnail((840, 520))
                self.current_img_data = raw_img
                self.current_zoom_level = 1.0
                
                self.after(0, render_image)
                self.log(f"Image originale '{nom}' chargée et prête pour manipulation.")
            except ImportError:
                self.log("Erreur Pillow manquant lors du chargement lightbox.")
                self.after(0, lambda: lbl.config(
                    text="Installe Pillow :\npip install Pillow",
                    font=FONT_SUB, fg=TEXT_DIM))
            except Exception as e:
                self.log(f"Erreur récupération image HD '{nom}' : {e}")
                self.after(0, lambda: lbl.config(
                    text=f"❌ Erreur : {e}", font=FONT_SUB, fg=DANGER))

        threading.Thread(target=fetch, daemon=True).start()

    # ── FICHIERS ──────────────────────────────────────────────────────────────
    def _populate_fichiers(self):
        parent = self.tab_fichiers
        for widget in parent.winfo_children():
            widget.destroy()

        fichiers = [f for f in self.data.get("fichiers", []) if f.get("url")]

        if not fichiers:
            self._empty(parent, "Aucun fichier disponible.")
            return

        tk.Label(parent, text="Fichiers disponibles",
                 font=("Syne", 12, "bold"), bg=BG, fg=ACCENT2,
                 pady=14).pack()

        for item in fichiers:
            row = tk.Frame(parent, bg=BG2, pady=12, padx=16)
            row.pack(fill="x", padx=28, pady=5)

            tk.Label(row, text="📦", font=("Syne", 18),
                     bg=BG2, fg=ACCENT).pack(side="left", padx=(0, 12))

            info = tk.Frame(row, bg=BG2)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=item["nom"], font=("Syne", 11, "bold"),
                     bg=BG2, fg=TEXT, anchor="w").pack(anchor="w")
            tk.Label(info, text=item["url"], font=FONT_SMALL,
                     bg=BG2, fg=TEXT_DIM, anchor="w").pack(anchor="w")

            btn = tk.Button(row, text="⬇ Télécharger",
                            font=("Syne", 10, "bold"),
                            bg=ACCENT, fg="white", relief="flat",
                            activebackground=ACCENT2, cursor="hand2",
                            padx=14, pady=6)
            btn.config(command=lambda u=item["url"], n=item["nom"],
                                       b=btn: self._download(u, n, b))
            btn.pack(side="right")

    def _download(self, url, nom, btn):
        save_path = filedialog.asksaveasfilename(
            initialfile=nom, title="Enregistrer sous…")
        if not save_path:
            return

        self.log(f"Démarrage téléchargement du fichier : '{nom}'")
        btn.config(text="⏳ En cours…", state="disabled", bg=TEXT_DIM)

        def fetch():
            try:
                r = requests.get(url, timeout=30, stream=True)
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.log(f"Fichier '{nom}' correctement enregistré à : {save_path}")
                self.after(0, lambda: btn.config(
                    text="✅ Téléchargé", bg=SUCCESS, state="normal"))
            except Exception as e:
                self.log(f"Échec de téléchargement pour '{nom}' : {e}")
                self.after(0, lambda: btn.config(
                    text="⬇ Télécharger", bg=ACCENT, state="normal"))
                self.after(0, lambda: messagebox.showerror(
                    "Erreur", f"Téléchargement échoué :\n{e}"))

        threading.Thread(target=fetch, daemon=True).start()

    # ── SUGGESTIONS ───────────────────────────────────────────────────────────
    def _populate_suggestions(self):
        parent = self.tab_suggestions
        for widget in parent.winfo_children():
            widget.destroy()

        wrap = tk.Frame(parent, bg=BG)
        wrap.place(relx=.5, rely=.5, anchor="center")

        tk.Label(wrap, text="✉️  Envoyer une suggestion",
                 font=("Syne", 15, "bold"), bg=BG, fg=ACCENT2).pack(anchor="w")
        tk.Label(wrap, text="Une idée, un retour ou un bug ? Remplis le formulaire ci-dessous.",
                 font=FONT_SMALL, bg=BG, fg=TEXT_DIM, pady=6).pack(anchor="w")

        tk.Frame(wrap, bg=ACCENT, height=1).pack(fill="x", pady=(0, 18))

        # Prénom
        tk.Label(wrap, text="Ton prénom (optionnel)", font=FONT_SMALL,
                 bg=BG, fg=TEXT_DIM).pack(anchor="w")
        self.f_nom = tk.Entry(wrap, bg=BG2, fg=TEXT, font=FONT_SUB,
                              relief="flat", insertbackground=TEXT, width=44)
        self.f_nom.pack(fill="x", ipady=6, pady=(4, 12))

        # Type
        tk.Label(wrap, text="Type de message", font=FONT_SMALL,
                 bg=BG, fg=TEXT_DIM).pack(anchor="w")
        self.f_type = ttk.Combobox(wrap, state="readonly", font=FONT_SUB,
            values=["💡 Suggestion", "👍 Retour positif", "🐛 Bug / Problème", "✏️ Autre"])
        self.f_type.current(0)
        self.f_type.pack(fill="x", pady=(4, 12))

        # Message
        tk.Label(wrap, text="Message *", font=FONT_SMALL,
                 bg=BG, fg=TEXT_DIM).pack(anchor="w")
        self.f_msg = tk.Text(wrap, bg=BG2, fg=TEXT, font=FONT_SUB,
                             relief="flat", insertbackground=TEXT,
                             width=44, height=6, padx=8, pady=8)
        self.f_msg.pack(fill="x", pady=(4, 16))

        # Bouton
        self.btn_send = tk.Button(wrap, text="Envoyer ✉️",
                                  font=("Syne", 11, "bold"),
                                  bg=ACCENT, fg="white", relief="flat",
                                  activebackground=ACCENT2,
                                  activeforeground=BG,
                                  cursor="hand2", pady=10,
                                  command=self._send_mail)
        self.btn_send.pack(fill="x")

        self.lbl_feedback = tk.Label(wrap, text="", font=FONT_SMALL,
                                     bg=BG, fg=SUCCESS)
        self.lbl_feedback.pack(pady=(10, 0))

    def _send_mail(self):
        nom     = self.f_nom.get().strip()
        type_   = self.f_type.get()
        message = self.f_msg.get("1.0", "end").strip()

        if not message:
            self.lbl_feedback.config(
                text="⚠️ Le message ne peut pas être vide.", fg=DANGER)
            return

        subject = f"[Faster Homework] {type_}" + (f" — {nom}" if nom else "")
        body    = f"Type : {type_}\n" + (f"De : {nom}\n" if nom else "") + f"\n{message}"

        self.log(f"Ouverture du client mail pour envoi de suggestion ({type_}).")
        mailto = (
            f"mailto:{MAIL_TO}"
            f"?subject={urllib.parse.quote(subject)}"
            f"&body={urllib.parse.quote(body)}"
        )
        webbrowser.open(mailto)

        self.lbl_feedback.config(
            text="✅ Ton client mail va s'ouvrir !", fg=SUCCESS)
        self.f_msg.delete("1.0", "end")
        self.f_nom.delete(0, "end")

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _empty(self, parent, msg):
        tk.Label(parent, text=msg, font=FONT_SUB,
                 bg=BG, fg=TEXT_DIM).pack(pady=50)


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()