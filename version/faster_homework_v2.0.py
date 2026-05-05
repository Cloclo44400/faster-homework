import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import io
import webbrowser
import urllib.parse

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
        self.title("Faster Homework v2.0")
        self.geometry("900x640")
        self.minsize(720, 520)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.data      = None
        self._img_refs = []

        self._build_ui()
        self._load_data()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG, pady=16)
        header.pack(fill="x", padx=28)

        tk.Label(header, text="⚡ Faster Homework", font=FONT_TITLE,
                 bg=BG, fg=ACCENT2).pack(side="left")
        tk.Label(header, text="v2.0", font=FONT_SMALL,
                 bg=BG, fg=TEXT_DIM).pack(side="left", padx=(6, 0), pady=(6, 0))

        self.status_dot = tk.Label(header, text="●", font=("Syne", 13),
                                   bg=BG, fg=TEXT_DIM)
        self.status_dot.pack(side="right", padx=(0, 4))
        self.status_lbl = tk.Label(header, text="Chargement…", font=FONT_SMALL,
                                   bg=BG, fg=TEXT_DIM)
        self.status_lbl.pack(side="right")

        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x", padx=28)

        # Notebook
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook",     background=BG,  borderwidth=0)
        style.configure("TNotebook.Tab", background=BG2, foreground=TEXT_DIM,
                        font=FONT_SUB,   padding=[14, 7])
        style.map("TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", ACCENT2)])

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=20, pady=14)

        self.tab_textes      = tk.Frame(self.nb, bg=BG)
        self.tab_images      = tk.Frame(self.nb, bg=BG)
        self.tab_fichiers    = tk.Frame(self.nb, bg=BG)
        self.tab_suggestions = tk.Frame(self.nb, bg=BG)

        self.nb.add(self.tab_textes,      text="  📄  Textes  ")
        self.nb.add(self.tab_images,      text="  🖼️  Images  ")
        self.nb.add(self.tab_fichiers,    text="  📦  Fichiers  ")
        self.nb.add(self.tab_suggestions, text="  ✉️  Suggestions  ")

    # ── STATUS ────────────────────────────────────────────────────────────────
    def _set_status(self, txt, color):
        self.status_lbl.config(text=txt, fg=color)
        self.status_dot.config(fg=color)

    # ── CHARGEMENT DATA ───────────────────────────────────────────────────────
    def _load_data(self):
        self._set_status("Connexion…", TEXT_DIM)
        threading.Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_data(self):
        try:
            r = requests.get(DATA_JSON_URL, timeout=10)
            r.raise_for_status()
            self.data = r.json()
            self.after(0, self._populate)
            self.after(0, lambda: self._set_status("Connecté", SUCCESS))
        except Exception as e:
            self.after(0, lambda: self._set_status("Erreur de connexion", DANGER))
            self.after(0, lambda: messagebox.showerror(
                "Erreur", f"Impossible de charger data.json :\n{e}"))

    def _populate(self):
        self._populate_textes()
        self._populate_images()
        self._populate_fichiers()
        self._populate_suggestions()

    # ── TEXTES ────────────────────────────────────────────────────────────────
    def _populate_textes(self):
        parent = self.tab_textes
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

        def load_text(url):
            txt_area.config(state="normal")
            txt_area.delete("1.0", "end")
            txt_area.insert("end", "Chargement…")
            txt_area.config(state="disabled")

            def fetch():
                try:
                    r = requests.get(url, timeout=10)
                    r.raise_for_status()
                    content = r.text
                except Exception as e:
                    content = f"[Erreur] {e}"
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
            b.config(command=lambda u=item["url"]: load_text(u))
            b.pack(fill="x", padx=6, pady=2)

    # ── IMAGES ────────────────────────────────────────────────────────────────
    def _populate_images(self):
        parent = self.tab_images
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
                             args=(url, lbl_img), daemon=True).start()

        for c in range(cols):
            grid_frame.columnconfigure(c, weight=1)

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
            # Stocker l'image originale pour la lightbox
            label._original_url = url
        except ImportError:
            self.after(0, lambda: label.config(
                text="📷\npip install Pillow",
                font=FONT_SMALL, fg=TEXT_DIM))
        except Exception:
            self.after(0, lambda: label.config(text="❌", font=FONT_SMALL, fg=DANGER))

    # ── LIGHTBOX ──────────────────────────────────────────────────────────────
    def _open_lightbox(self, url, nom):
        lb = tk.Toplevel(self)
        lb.title(nom)
        lb.configure(bg=BG)
        lb.geometry("900x680")
        lb.grab_set()

        tk.Label(lb, text=nom, font=("Syne", 13, "bold"),
                 bg=BG, fg=ACCENT2, pady=12).pack()

        lbl = tk.Label(lb, bg=BG, text="⏳ Chargement…",
                       font=("Syne", 16), fg=TEXT_DIM)
        lbl.pack(expand=True)

        tk.Button(lb, text="✕  Fermer", font=FONT_LABEL,
                  bg=BG3, fg=TEXT, relief="flat", padx=16, pady=7,
                  activebackground=DANGER, activeforeground="white",
                  cursor="hand2", command=lb.destroy).pack(pady=14)

        lb.bind("<Escape>", lambda e: lb.destroy())

        def fetch():
            try:
                from PIL import Image, ImageTk
                r = requests.get(url, timeout=20)
                r.raise_for_status()
                img = Image.open(io.BytesIO(r.content))
                img.thumbnail((860, 580))
                photo = ImageTk.PhotoImage(img)
                self._img_refs.append(photo)
                self.after(0, lambda: lbl.config(image=photo, text=""))
            except ImportError:
                self.after(0, lambda: lbl.config(
                    text="Installe Pillow :\npip install Pillow",
                    font=FONT_SUB, fg=TEXT_DIM))
            except Exception as e:
                self.after(0, lambda: lbl.config(
                    text=f"❌ Erreur : {e}", font=FONT_SUB, fg=DANGER))

        threading.Thread(target=fetch, daemon=True).start()

    # ── FICHIERS ──────────────────────────────────────────────────────────────
    def _populate_fichiers(self):
        parent = self.tab_fichiers
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

        btn.config(text="⏳ En cours…", state="disabled", bg=TEXT_DIM)

        def fetch():
            try:
                r = requests.get(url, timeout=30, stream=True)
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.after(0, lambda: btn.config(
                    text="✅ Téléchargé", bg=SUCCESS, state="normal"))
            except Exception as e:
                self.after(0, lambda: btn.config(
                    text="⬇ Télécharger", bg=ACCENT, state="normal"))
                self.after(0, lambda: messagebox.showerror(
                    "Erreur", f"Téléchargement échoué :\n{e}"))

        threading.Thread(target=fetch, daemon=True).start()

    # ── SUGGESTIONS ───────────────────────────────────────────────────────────
    def _populate_suggestions(self):
        parent = self.tab_suggestions

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
