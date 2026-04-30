import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import io
import os
import webbrowser

# ─── CONFIG ───────────────────────────────────────────────────────────────────
DATA_JSON_URL = "https://raw.githubusercontent.com/Cloclo44400/faster-homework/main/data.json"

# ─── COULEURS & STYLE ─────────────────────────────────────────────────────────
BG        = "#0f1117"
BG2       = "#1a1d27"
ACCENT    = "#6c63ff"
ACCENT2   = "#a78bfa"
TEXT      = "#e2e8f0"
TEXT_DIM  = "#64748b"
SUCCESS   = "#22c55e"
DANGER    = "#ef4444"
FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_SUB    = ("Segoe UI", 11)
FONT_LABEL  = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Faster Homework v1.0")
        self.geometry("860x620")
        self.minsize(700, 500)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.data = None
        self._img_refs = []  # pour éviter le garbage collect des images

        self._build_ui()
        self._load_data()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG, pady=18)
        header.pack(fill="x", padx=30)

        tk.Label(header, text="⚡ Faster Homework", font=FONT_TITLE,
                 bg=BG, fg=ACCENT2).pack(side="left")

        self.status_dot = tk.Label(header, text="●", font=("Segoe UI", 14),
                                   bg=BG, fg=TEXT_DIM)
        self.status_dot.pack(side="right", padx=(0, 4))
        self.status_lbl = tk.Label(header, text="Chargement…", font=FONT_SMALL,
                                   bg=BG, fg=TEXT_DIM)
        self.status_lbl.pack(side="right")

        # Separator
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x", padx=30)

        # Notebook (onglets)
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG2, foreground=TEXT_DIM,
                        font=FONT_SUB, padding=[14, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", ACCENT2)])

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=20, pady=16)

        self.tab_textes   = self._make_tab("📄  Textes")
        self.tab_images   = self._make_tab("🖼️  Images")
        self.tab_fichiers = self._make_tab("📦  Fichiers")

        self.nb.add(self.tab_textes,   text="  📄  Textes  ")
        self.nb.add(self.tab_images,   text="  🖼️  Images  ")
        self.nb.add(self.tab_fichiers, text="  📦  Fichiers  ")

    def _make_tab(self, name):
        frame = tk.Frame(self.nb, bg=BG)
        return frame

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

    def _set_status(self, txt, color):
        self.status_lbl.config(text=txt, fg=color)
        self.status_dot.config(fg=color)

    # ── POPULATION DES ONGLETS ────────────────────────────────────────────────
    def _populate(self):
        self._populate_textes()
        self._populate_images()
        self._populate_fichiers()

    # -- Textes ----------------------------------------------------------------
    def _populate_textes(self):
        parent = self.tab_textes
        textes = self.data.get("textes", [])

        if not textes:
            tk.Label(parent, text="Aucun texte disponible.", font=FONT_SUB,
                     bg=BG, fg=TEXT_DIM).pack(pady=40)
            return

        # Liste à gauche, contenu à droite
        pane = tk.PanedWindow(parent, orient="horizontal", bg=BG,
                              sashwidth=4, sashrelief="flat")
        pane.pack(fill="both", expand=True)

        left = tk.Frame(pane, bg=BG2, width=200)
        right = tk.Frame(pane, bg=BG)
        pane.add(left, minsize=160)
        pane.add(right, minsize=300)

        tk.Label(left, text="Articles", font=("Segoe UI", 10, "bold"),
                 bg=BG2, fg=ACCENT2, pady=10).pack(fill="x", padx=10)

        txt_area = tk.Text(right, bg=BG2, fg=TEXT, font=("Consolas", 11),
                           wrap="word", relief="flat", padx=14, pady=14,
                           state="disabled", insertbackground=TEXT)
        scroll = tk.Scrollbar(right, command=txt_area.yview, bg=BG2)
        txt_area.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt_area.pack(fill="both", expand=True)

        def load_text(url, btn_ref):
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
                def update():
                    txt_area.config(state="normal")
                    txt_area.delete("1.0", "end")
                    txt_area.insert("end", content)
                    txt_area.config(state="disabled")
                self.after(0, update)

            threading.Thread(target=fetch, daemon=True).start()

        for item in textes:
            b = tk.Button(left, text=item["nom"], font=FONT_LABEL,
                          bg=BG2, fg=TEXT, relief="flat", anchor="w",
                          activebackground=ACCENT, activeforeground="white",
                          cursor="hand2", padx=12, pady=6)
            b.config(command=lambda u=item["url"], btn=b: load_text(u, btn))
            b.pack(fill="x", padx=6, pady=2)

    # -- Images ----------------------------------------------------------------
    def _populate_images(self):
        parent = self.tab_images
        images = self.data.get("images", [])

        if not images:
            tk.Label(parent, text="Aucune image disponible.", font=FONT_SUB,
                     bg=BG, fg=TEXT_DIM).pack(pady=40)
            return

        # Scrollable grid
        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        grid_frame = tk.Frame(canvas, bg=BG)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        grid_frame.bind("<Configure>",
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox("all")))

        cols = 3
        for i, item in enumerate(images):
            cell = tk.Frame(grid_frame, bg=BG2, padx=8, pady=8,
                            relief="flat", bd=0)
            cell.grid(row=i // cols, column=i % cols, padx=10, pady=10,
                      sticky="nsew")

            lbl_img = tk.Label(cell, bg=BG2, text="⏳", font=("Segoe UI", 28),
                               fg=TEXT_DIM)
            lbl_img.pack()
            tk.Label(cell, text=item["nom"], font=FONT_SMALL, bg=BG2,
                     fg=TEXT_DIM).pack()

            url = item["url"]
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
        except ImportError:
            # Pillow pas installé
            self.after(0, lambda: label.config(
                text="📷\nInstalle Pillow\npip install Pillow",
                font=FONT_SMALL, fg=TEXT_DIM))
        except Exception as e:
            self.after(0, lambda: label.config(
                text=f"❌ Erreur", font=FONT_SMALL, fg=DANGER))

    # -- Fichiers --------------------------------------------------------------
    def _populate_fichiers(self):
        parent = self.tab_fichiers
        fichiers = self.data.get("fichiers", [])

        if not fichiers:
            tk.Label(parent, text="Aucun fichier disponible.", font=FONT_SUB,
                     bg=BG, fg=TEXT_DIM).pack(pady=40)
            return

        tk.Label(parent, text="Fichiers disponibles au téléchargement",
                 font=("Segoe UI", 12, "bold"), bg=BG, fg=ACCENT2,
                 pady=16).pack()

        for item in fichiers:
            row = tk.Frame(parent, bg=BG2, pady=12, padx=16)
            row.pack(fill="x", padx=30, pady=6)

            tk.Label(row, text="📦", font=("Segoe UI", 18),
                     bg=BG2, fg=ACCENT).pack(side="left", padx=(0, 12))

            info = tk.Frame(row, bg=BG2)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=item["nom"], font=("Segoe UI", 11, "bold"),
                     bg=BG2, fg=TEXT, anchor="w").pack(anchor="w")
            tk.Label(info, text=item["url"], font=FONT_SMALL,
                     bg=BG2, fg=TEXT_DIM, anchor="w").pack(anchor="w")

            btn_dl = tk.Button(row, text="⬇ Télécharger",
                               font=("Segoe UI", 10, "bold"),
                               bg=ACCENT, fg="white", relief="flat",
                               activebackground=ACCENT2, cursor="hand2",
                               padx=14, pady=6)
            btn_dl.config(command=lambda u=item["url"], n=item["nom"],
                                          b=btn_dl: self._download(u, n, b))
            btn_dl.pack(side="right")

    def _download(self, url, nom, btn):
        save_path = filedialog.asksaveasfilename(
            defaultextension="",
            initialfile=nom,
            title="Enregistrer sous…"
        )
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


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
