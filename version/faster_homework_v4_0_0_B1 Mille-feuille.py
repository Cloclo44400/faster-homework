import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
import threading
import requests
import io
import webbrowser
import urllib.parse
import platform
from datetime import datetime

IS_WINDOWS = platform.system().lower().startswith("win")

# ─── CONFIGURATION DES URLS DE CENTRALISATION ────────────────────────────────
TEXTE_JSON_URL    = "https://raw.githubusercontent.com/Cloclo44400/faster-homework/main/texte.json"
IMAGE_JSON_URL    = "https://raw.githubusercontent.com/Cloclo44400/faster-homework/main/image.json"
DOCUMENT_JSON_URL = "https://raw.githubusercontent.com/Cloclo44400/faster-homework/main/document.json"

MAIL_TO = "suggestion.retoure.44@proton.me"
APP_VERSION = "4.0.0 B-1"

LANG_MAP = {
    "Français": "fr", "Anglais": "en", "Espagnol": "es", "Allemand": "de",
    "Italien": "it", "Portugais": "pt", "Néerlandais": "nl"
}

# ─── THÈMES (palette bleue façon École Directe) ─────────────────────────────
THEMES = {
    "dark": {
        "label": "Sombre",
        "BG": "#0c0e14", "BG2": "#161923", "BG3": "#1f2330", "BORDER": "#2a2f3f",
        "ACCENT": "#4f8ef7", "ACCENT_HOV": "#3b7ce8", "ACCENT_SOFT": "#9cc2fb",
        "TEXT": "#eef1f6", "TEXT_DIM": "#6b7280", "TEXT_MUTED": "#9aa2b1",
        "SUCCESS": "#22c55e", "DANGER": "#f04747", "WARNING": "#f5a623",
        "ON_ACCENT": "#ffffff", "GLASS": False,
    },
    "light": {
        "label": "Clair",
        "BG": "#f2f4f8", "BG2": "#ffffff", "BG3": "#eaeefc", "BORDER": "#e1e5ee",
        "ACCENT": "#1f6fd6", "ACCENT_HOV": "#175bb5", "ACCENT_SOFT": "#175bb5",
        "TEXT": "#16213a", "TEXT_DIM": "#8891a3", "TEXT_MUTED": "#54617a",
        "SUCCESS": "#16a34a", "DANGER": "#dc2626", "WARNING": "#d97706",
        "ON_ACCENT": "#ffffff", "GLASS": False,
    },
    "splash": {
        "label": "Splash",
        "BG": "#c9dcf0", "BG2": "#eaf3fc", "BG3": "#d7e8f8", "BORDER": "#a9c9ea",
        "ACCENT": "#2f8ff0", "ACCENT_HOV": "#1f78e0", "ACCENT_SOFT": "#0f2c47",
        "TEXT": "#0f2c47", "TEXT_DIM": "#3d6690", "TEXT_MUTED": "#245380",
        "SUCCESS": "#1f9d55", "DANGER": "#e0433f", "WARNING": "#e0921f",
        "ON_ACCENT": "#ffffff", "GLASS": True, "TRANSPARENT_KEY": "#ff00fe",
    },
}

_FAMILIES = set()

def _pick_font_family():
    candidates = ["Segoe UI", "SF Pro Display", "Inter", "Helvetica Neue", "DejaVu Sans", "Arial"]
    for c in candidates:
        if not _FAMILIES or c in _FAMILIES:
            return c
    return "TkDefaultFont"

FONT_FAMILY = "Segoe UI"


# ─── OUTILS DE DESSIN "COINS ARRONDIS" ──────────────────────────────────────
def _rounded_points(x1, y1, x2, y2, r):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]

def draw_rounded_rect(canvas, x1, y1, x2, y2, r=16, **kwargs):
    return canvas.create_polygon(_rounded_points(x1, y1, x2, y2, r), smooth=True, **kwargs)


class RoundedButton(tk.Canvas):
    """Bouton à coins arrondis dessiné sur un Canvas (look moderne façon Apple/Samsung)."""

    def __init__(self, parent, text, command=None, font=None, fill="#4f8ef7", hover_fill=None,
                 text_color="#ffffff", hover_text=None, radius=14, padx=18, pady=11,
                 anchor="center", stretch=False, bg=None):
        self.font = font or (FONT_FAMILY, 10, "bold")
        self._fontobj = tkfont.Font(font=self.font)
        text_w = self._fontobj.measure(text)
        text_h = self._fontobj.metrics("linespace")
        self.padx, self.pady = padx, pady
        h = text_h + pady * 2
        w = text_w + padx * 2
        super().__init__(parent, width=w, height=h, highlightthickness=0, bd=0,
                          bg=bg if bg is not None else parent.cget("bg"), cursor="hand2")
        self.text = text
        self.command = command
        self.fill = fill
        self.hover_fill = hover_fill or fill
        self.text_color = text_color
        self.hover_text = hover_text or text_color
        self.radius = radius
        self.anchor = anchor
        self.stretch = stretch
        self.disabled = False
        self._redraw()
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.bind("<Button-1>", self._click)
        if stretch:
            self.bind("<Configure>", lambda e: self._redraw())

    def _redraw(self, fill=None, text_color=None):
        self.delete("all")
        w = self.winfo_width() if (self.stretch and self.winfo_width() > 1) else int(self["width"])
        h = int(self["height"])
        draw_rounded_rect(self, 1, 1, w - 1, h - 1, self.radius, fill=fill or self.fill, outline="")
        if self.anchor == "w":
            self.create_text(self.padx, h // 2, text=self.text, fill=text_color or self.text_color,
                              font=self._fontobj, anchor="w")
        else:
            self.create_text(w // 2, h // 2, text=self.text, fill=text_color or self.text_color,
                              font=self._fontobj, anchor="center")

    def _hover(self, entering):
        if self.disabled:
            return
        self._redraw(self.hover_fill if entering else None, self.hover_text if entering else None)

    def _click(self, _e):
        if not self.disabled and self.command:
            self.command()

    def set_text(self, text):
        self.text = text
        self._redraw()

    def set_colors(self, fill=None, text_color=None, hover_fill=None, hover_text=None):
        if fill: self.fill = fill
        if text_color: self.text_color = text_color
        if hover_fill: self.hover_fill = hover_fill
        if hover_text: self.hover_text = hover_text
        self._redraw()

    def set_disabled(self, disabled=True, disabled_fill=None):
        self.disabled = disabled
        self.config(cursor="arrow" if disabled else "hand2")
        self._redraw(disabled_fill if disabled else None)


class RoundedPanel(tk.Canvas):
    """Panneau/carte à coins arrondis. `.inner` est le Frame où placer le contenu."""

    def __init__(self, parent, bg_parent, fill, radius=20, pad=16):
        super().__init__(parent, highlightthickness=0, bd=0, bg=bg_parent)
        self.fill = fill
        self.radius = radius
        self.pad = pad
        self.inner = tk.Frame(self, bg=fill)
        self.win_id = self.create_window(pad, pad, window=self.inner, anchor="nw")
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        w, h = event.width, event.height
        if w < 4 or h < 4:
            return
        self.itemconfig(self.win_id, width=max(w - 2 * self.pad, 1), height=max(h - 2 * self.pad, 1))
        self.delete("bgrect")
        rect = draw_rounded_rect(self, 1, 1, w - 1, h - 1, self.radius, fill=self.fill, outline="", tags="bgrect")
        self.tag_lower(rect)

    def autosize(self):
        """Fige la hauteur du panneau à celle de son contenu (utile pour les lignes de liste)."""
        self.update_idletasks()
        h = self.inner.winfo_reqheight() + self.pad * 2
        self.config(height=h)


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        global FONT_FAMILY, _FAMILIES
        _FAMILIES = set(tkfont.families())
        FONT_FAMILY = _pick_font_family()
        self._set_fonts()

        self.title(f"Faster Homework — v{APP_VERSION}")
        self.geometry("1200x700")
        self.minsize(780, 560)
        self.resizable(True, True)

        self.data = None
        self._img_refs = []
        self.load_errors = {}

        self.dev_mode = False
        self.dev_pane = None
        self.console_text = None

        self.theme_name = "dark"
        self.t = THEMES[self.theme_name]
        self.can_glass = False

        self.tab_defs = [
            ("textes",      "📄  Textes"),
            ("images",      "🖼️  Images"),
            ("documents",   "📦  Documents"),
            ("traduction",  "🌐  Traduction"),
            ("suggestions", "✉️  Suggestions"),
        ]
        self.tab_frames = {}
        self.tab_buttons = {}
        self.active_tab = "textes"

        self.configure(bg=self.t["BG"])
        self._build_ui()
        self._load_data()

        self.bind("<F1>", self._toggle_dev_mode)
        self.log(f"Application v{APP_VERSION} prête. Mode développeur disponible via F1.")

    def _set_fonts(self):
        self.FONT_TITLE   = (FONT_FAMILY, 20, "bold")
        self.FONT_SUBHEAD = (FONT_FAMILY, 13, "bold")
        self.FONT_SUB     = (FONT_FAMILY, 11)
        self.FONT_LABEL   = (FONT_FAMILY, 10)
        self.FONT_SMALL   = (FONT_FAMILY, 9)
        self.FONT_BTN     = (FONT_FAMILY, 10, "bold")
        self.FONT_MONO    = ("Consolas", 11)

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

    # ── TRANSPARENCE RÉELLE (thème Splash, Windows uniquement) ────────────────
    def _apply_window_glass(self, window):
        t = self.t
        try:
            if self.theme_name == "splash" and IS_WINDOWS:
                window.attributes("-transparentcolor", t["TRANSPARENT_KEY"])
                return True
            window.attributes("-transparentcolor", "")
            return False
        except tk.TclError:
            return False

    def glass_color(self, fallback):
        if self.theme_name == "splash" and self.can_glass:
            return self.t["TRANSPARENT_KEY"]
        return fallback

    # ── RACCOURCIS DE STYLE ───────────────────────────────────────────────────
    def mk_button(self, parent, text, command=None, kind="primary", anchor="center", stretch=False, bg=None):
        t = self.t
        bg = bg if bg is not None else parent.cget("bg")
        if kind == "primary":
            return RoundedButton(parent, text, command, font=self.FONT_BTN, fill=t["ACCENT"],
                                  hover_fill=t["ACCENT_HOV"], text_color=t["ON_ACCENT"], hover_text=t["ON_ACCENT"],
                                  radius=14, anchor=anchor, stretch=stretch, bg=bg)
        if kind == "secondary":
            return RoundedButton(parent, text, command, font=self.FONT_BTN, fill=t["BG3"],
                                  hover_fill=t["ACCENT"], text_color=t["TEXT"], hover_text=t["ON_ACCENT"],
                                  radius=14, anchor=anchor, stretch=stretch, bg=bg)
        if kind == "ghost":
            gbg = self.glass_color(t["BG2"])
            return RoundedButton(parent, text, command, font=self.FONT_LABEL, fill=gbg,
                                  hover_fill=t["ACCENT"], text_color=t["TEXT"], hover_text=t["ON_ACCENT"],
                                  radius=12, anchor=anchor, stretch=stretch, bg=bg)
        if kind == "danger":
            return RoundedButton(parent, text, command, font=self.FONT_BTN, fill=t["BG3"],
                                  hover_fill=t["DANGER"], text_color=t["TEXT"], hover_text=t["ON_ACCENT"],
                                  radius=14, anchor=anchor, stretch=stretch, bg=bg)
        return RoundedButton(parent, text, command, font=self.FONT_BTN, fill=t["BG3"], text_color=t["TEXT"],
                              radius=14, anchor=anchor, stretch=stretch, bg=bg)

    def mk_panel(self, parent, radius=20, pad=16, fill=None):
        t = self.t
        fill = fill if fill is not None else self.glass_color(t["BG2"])
        return RoundedPanel(parent, bg_parent=parent.cget("bg"), fill=fill, radius=radius, pad=pad)

    # ── UI PRINCIPALE ─────────────────────────────────────────────────────────
    def _build_ui(self):
        t = self.t
        self.configure(bg=t["BG"])
        self.can_glass = self._apply_window_glass(self)
        if self.theme_name == "splash" and not IS_WINDOWS:
            self.log("La transparence réelle du thème Splash nécessite Windows ; rendu en mode givré simulé.")

        self.main_split = tk.PanedWindow(self, orient="horizontal", bg=t["BG"], sashwidth=6, sashrelief="flat", bd=0)
        self.main_split.pack(fill="both", expand=True)

        self.app_frame = tk.Frame(self.main_split, bg=t["BG"])
        self.main_split.add(self.app_frame, minsize=560, stretch="always")

        # ── Header ──
        header = tk.Frame(self.app_frame, bg=t["BG"], pady=20)
        header.pack(fill="x", padx=28)

        self.settings_btn = RoundedButton(header, "⚙", command=self._open_theme_menu,
                                           font=(FONT_FAMILY, 13), fill=self.glass_color(t["BG3"]),
                                           hover_fill=t["ACCENT"], text_color=t["TEXT_DIM"],
                                           hover_text=t["ON_ACCENT"], radius=999, padx=12, pady=9, bg=t["BG"])
        self.settings_btn.pack(side="left", padx=(0, 14))

        title_wrap = tk.Frame(header, bg=t["BG"])
        title_wrap.pack(side="left")

        badge_canvas = tk.Canvas(title_wrap, width=42, height=42, bg=t["BG"], highlightthickness=0)
        badge_canvas.pack(side="left", padx=(0, 12))
        badge_canvas.create_oval(1, 1, 41, 41, fill=t["ACCENT"], outline="")
        badge_canvas.create_text(21, 22, text="FH", fill=t["ON_ACCENT"], font=(FONT_FAMILY, 12, "bold"))

        name_wrap = tk.Frame(title_wrap, bg=t["BG"])
        name_wrap.pack(side="left")
        tk.Label(name_wrap, text="Faster Homework", font=self.FONT_TITLE, bg=t["BG"], fg=t["TEXT"]).pack(anchor="w")
        tk.Label(name_wrap, text=f"version {APP_VERSION} · thème {t['label']}", font=self.FONT_SMALL, bg=t["BG"],
                 fg=t["TEXT_DIM"]).pack(anchor="w")

        status_wrap = tk.Frame(header, bg=t["BG"])
        status_wrap.pack(side="right")
        self.status_dot = tk.Label(status_wrap, text="●", font=(FONT_FAMILY, 12), bg=t["BG"], fg=t["TEXT_DIM"])
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_lbl = tk.Label(status_wrap, text="Connexion…", font=self.FONT_SMALL, bg=t["BG"], fg=t["TEXT_DIM"])
        self.status_lbl.pack(side="left")

        # ── Barre d'onglets façon "segmented control" (pilule arrondie) ──
        tabbar_wrap = tk.Frame(self.app_frame, bg=t["BG"])
        tabbar_wrap.pack(fill="x", padx=28, pady=(4, 14))

        self.tabbar_panel = self.mk_panel(tabbar_wrap, radius=999, pad=6, fill=self.glass_color(t["BG2"]))
        self.tabbar_panel.pack(fill="x")

        self.tab_buttons = {}
        for key, label in self.tab_defs:
            btn = RoundedButton(self.tabbar_panel.inner, label, command=lambda k=key: self._show_tab(k),
                                 font=self.FONT_LABEL, fill=self.glass_color(t["BG2"]), text_color=t["TEXT_MUTED"],
                                 hover_fill=t["BG3"], hover_text=t["TEXT"], radius=999, padx=16, pady=9,
                                 bg=t["BG2"] if not self.glass_color(None) else t["BG2"])
            btn.pack(side="left", padx=3, pady=3)
            self.tab_buttons[key] = btn
        self.tabbar_panel.autosize()

        # ── Zone de contenu (les 5 onglets empilés) ──
        content_wrap = tk.Frame(self.app_frame, bg=t["BG"])
        content_wrap.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        content_wrap.grid_rowconfigure(0, weight=1)
        content_wrap.grid_columnconfigure(0, weight=1)

        self.tab_frames = {}
        for key, _label in self.tab_defs:
            f = tk.Frame(content_wrap, bg=t["BG"])
            f.grid(row=0, column=0, sticky="nsew")
            self.tab_frames[key] = f

        self.tab_textes      = self.tab_frames["textes"]
        self.tab_images      = self.tab_frames["images"]
        self.tab_fichiers    = self.tab_frames["documents"]
        self.tab_traduction  = self.tab_frames["traduction"]
        self.tab_suggestions = self.tab_frames["suggestions"]

        self._populate_traduction()
        self._show_tab(self.active_tab)

        if self.dev_mode:
            self._build_dev_pane()

    def _show_tab(self, key):
        self.active_tab = key
        t = self.t
        for k, btn in self.tab_buttons.items():
            if k == key:
                btn.set_colors(fill=t["ACCENT"], text_color=t["ON_ACCENT"], hover_fill=t["ACCENT"], hover_text=t["ON_ACCENT"])
            else:
                btn.set_colors(fill=self.glass_color(t["BG2"]), text_color=t["TEXT_MUTED"],
                                hover_fill=t["BG3"], hover_text=t["TEXT"])
        self.tab_frames[key].tkraise()

    # ── MENU DE SÉLECTION DE THÈME ────────────────────────────────────────────
    def _open_theme_menu(self):
        t = self.t
        menu = tk.Menu(self, tearoff=0, bg=t["BG2"], fg=t["TEXT"], activebackground=t["ACCENT"],
                        activeforeground=t["ON_ACCENT"], font=self.FONT_SUB, bd=0)
        for key, theme in THEMES.items():
            prefix = "● " if key == self.theme_name else "   "
            menu.add_command(label=f"{prefix}{theme['label']}", command=lambda k=key: self._set_theme(k))
        try:
            x = self.settings_btn.winfo_rootx()
            y = self.settings_btn.winfo_rooty() + self.settings_btn.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _set_theme(self, key):
        if key == self.theme_name:
            return
        self.theme_name = key
        self.t = THEMES[key]
        self.log(f"Changement de thème : {self.t['label']}")

        was_dev = self.dev_mode
        self.main_split.destroy()
        self.console_text = None
        self.dev_pane = None
        self.dev_mode = was_dev

        self._build_ui()

        if self.data is not None:
            self._populate()
            self._set_status("Connecté", self.t["SUCCESS"])
        else:
            self._set_status("Connexion…", self.t["TEXT_DIM"])

    # ── ONGLET TRADUCTION ──────────────────────────────────────────────────────
    def _populate_traduction(self):
        t = self.t
        parent = self.tab_traduction

        tk.Label(parent, text="Traducteur de cours", font=self.FONT_SUBHEAD, bg=t["BG"], fg=t["TEXT"]).pack(anchor="w", pady=(0, 2))
        tk.Label(parent, text="Saisis ou colle ton texte pour le traduire instantanément.",
                 font=self.FONT_SMALL, bg=t["BG"], fg=t["TEXT_DIM"]).pack(anchor="w", pady=(0, 14))

        panel = self.mk_panel(parent, radius=22, pad=18)
        panel.pack(fill="both", expand=True)
        box = panel.inner

        sel_bar = tk.Frame(box, bg=panel.fill)
        sel_bar.pack(fill="x", pady=(0, 14))

        tk.Label(sel_bar, text="De", font=self.FONT_LABEL, bg=panel.fill, fg=t["TEXT_MUTED"]).pack(side="left")
        self.combo_src = ttk.Combobox(sel_bar, state="readonly", font=self.FONT_SMALL, width=12, values=list(LANG_MAP.keys()))
        self.combo_src.set("Français")
        self.combo_src.pack(side="left", padx=(8, 6))

        btn_swap = RoundedButton(sel_bar, "⇄", command=self._swap_languages, font=self.FONT_BTN,
                                  fill=t["BG3"], hover_fill=t["ACCENT"], text_color=t["ACCENT_SOFT"],
                                  hover_text=t["ON_ACCENT"], radius=999, padx=12, pady=8, bg=panel.fill)
        btn_swap.pack(side="left", padx=4)

        tk.Label(sel_bar, text="Vers", font=self.FONT_LABEL, bg=panel.fill, fg=t["TEXT_MUTED"]).pack(side="left", padx=(6, 0))
        self.combo_tgt = ttk.Combobox(sel_bar, state="readonly", font=self.FONT_SMALL, width=12, values=list(LANG_MAP.keys()))
        self.combo_tgt.set("Anglais")
        self.combo_tgt.pack(side="left", padx=8)

        self.btn_translate = self.mk_button(sel_bar, "Traduire", command=self._start_translation, kind="primary", bg=panel.fill)
        self.btn_translate.pack(side="right")

        panes = tk.PanedWindow(box, orient="horizontal", bg=panel.fill, sashwidth=8, sashrelief="flat", bd=0)
        panes.pack(fill="both", expand=True)

        left_f = tk.Frame(panes, bg=panel.fill)
        right_f = tk.Frame(panes, bg=panel.fill)
        panes.add(left_f, minsize=200, stretch="always")
        panes.add(right_f, minsize=200, stretch="always")

        tk.Label(left_f, text="TEXTE D'ORIGINE", font=self.FONT_SMALL, bg=panel.fill, fg=t["TEXT_DIM"]).pack(anchor="w", pady=(0, 6))
        src_panel = self.mk_panel(left_f, radius=16, pad=2, fill=t["BG"])
        src_panel.pack(fill="both", expand=True, padx=(0, 6))
        self.txt_src = tk.Text(src_panel.inner, bg=t["BG"], fg=t["TEXT"], font=self.FONT_MONO, wrap="word",
                                relief="flat", insertbackground=t["TEXT"], padx=10, pady=10, bd=0)
        self.txt_src.pack(fill="both", expand=True)

        tk.Label(right_f, text="TEXTE TRADUIT", font=self.FONT_SMALL, bg=panel.fill, fg=t["TEXT_DIM"]).pack(anchor="w", pady=(0, 6))
        tgt_panel = self.mk_panel(right_f, radius=16, pad=2, fill=t["BG"])
        tgt_panel.pack(fill="both", expand=True, padx=(6, 0))
        self.txt_tgt = tk.Text(tgt_panel.inner, bg=t["BG"], fg=t["TEXT"], font=self.FONT_MONO, wrap="word",
                                relief="flat", state="disabled", padx=10, pady=10, bd=0)
        self.txt_tgt.pack(fill="both", expand=True)

    def _swap_languages(self):
        src, tgt = self.combo_src.get(), self.combo_tgt.get()
        self.combo_src.set(tgt)
        self.combo_tgt.set(src)
        self.log(f"Inversion des langues : {src} ⇄ {tgt}")

    def _start_translation(self):
        t = self.t
        text_to_translate = self.txt_src.get("1.0", "end").strip()
        if not text_to_translate:
            return

        self.btn_translate.set_disabled(True, disabled_fill=t["BG3"])
        self.btn_translate.set_text("Traduction…")
        self.txt_tgt.config(state="normal")
        self.txt_tgt.delete("1.0", "end")
        self.txt_tgt.insert("end", "Traduction en cours sur le serveur…")
        self.txt_tgt.config(state="disabled")

        src_lang = LANG_MAP.get(self.combo_src.get(), "fr")
        tgt_lang = LANG_MAP.get(self.combo_tgt.get(), "en")

        self.log(f"Requête de traduction lancée ({src_lang} -> {tgt_lang})")
        threading.Thread(target=self._async_translate, args=(text_to_translate, src_lang, tgt_lang), daemon=True).start()

    def _async_translate(self, text, src, tgt):
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {"q": text, "langpair": f"{src}|{tgt}"}
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
        self.btn_translate.set_disabled(False)
        self.btn_translate.set_text("Traduire")

    # ── MODE DÉVELOPPEUR (F1) ──────────────────────────────────────────────────
    def _toggle_dev_mode(self, event=None):
        self.dev_mode = not self.dev_mode
        if self.dev_mode:
            self._build_dev_pane()
        else:
            if self.dev_pane:
                self.main_split.forget(self.dev_pane)
                self.dev_pane.destroy()
                self.dev_pane, self.console_text = None, None

    def _build_dev_pane(self):
        t = self.t
        self.dev_pane = tk.Frame(self.main_split, bg=t["BG2"], padx=12, pady=12)
        self.main_split.add(self.dev_pane, minsize=330, stretch="never")
        tk.Label(self.dev_pane, text="Mode développeur", font=self.FONT_SUBHEAD, bg=t["BG2"], fg=t["ACCENT_SOFT"]).pack(anchor="w", pady=(0, 8))

        dev_nb = ttk.Notebook(self.dev_pane)
        dev_nb.pack(fill="both", expand=True)
        tab_console = tk.Frame(dev_nb, bg=t["BG2"])
        dev_nb.add(tab_console, text="Console")

        self.console_text = tk.Text(tab_console, bg=t["BG"], fg=t["SUCCESS"], font=self.FONT_MONO, wrap="word",
                                     relief="flat", state="disabled", padx=8, pady=8)
        self.console_text.pack(fill="both", expand=True)

        tab_debug = tk.Frame(dev_nb, bg=t["BG2"], padx=8, pady=10)
        dev_nb.add(tab_debug, text="Outils")
        btn_refresh = self.mk_button(tab_debug, "Actualiser les données", command=self._load_data, kind="primary", stretch=True)
        btn_refresh.pack(fill="x", pady=4)

    # ── STATUS ────────────────────────────────────────────────────────────────
    def _set_status(self, txt, color):
        self.status_lbl.config(text=txt, fg=color)
        self.status_dot.config(fg=color)

    # ── CHARGEMENT DES DONNÉES JSON ────────────────────────────────────────────
    def _load_data(self):
        self._set_status("Connexion…", self.t["TEXT_DIM"])
        threading.Thread(target=self._fetch_split_data, daemon=True).start()

    def _fetch_split_data(self):
        merged_data = {"textes": [], "images": [], "documents": []}
        targets = [
            ("Textes", TEXTE_JSON_URL, "textes"),
            ("Images", IMAGE_JSON_URL, "images"),
            ("Documents", DOCUMENT_JSON_URL, "documents"),
        ]
        self.load_errors = {}
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
            self.after(0, lambda: self._set_status("Connecté", self.t["SUCCESS"]))
        else:
            self.after(0, lambda: self._set_status("Erreur", self.t["DANGER"]))
            self.after(0, lambda: messagebox.showerror("Erreur", "Impossible de charger les fichiers de configuration JSON."))

    def _populate(self):
        self._populate_textes()
        self._populate_images()
        self._populate_documents()
        self._populate_suggestions()

    # ── TEXTES ────────────────────────────────────────────────────────────────
    def _populate_textes(self):
        t = self.t
        parent = self.tab_textes
        for widget in parent.winfo_children(): widget.destroy()

        if "textes" in self.load_errors:
            self._empty(parent, f"⚠️ Erreur de chargement du fichier JSON :\n\n{self.load_errors['textes']}")
            return
        textes = [x for x in self.data.get("textes", []) if x.get("url")]
        if not textes:
            self._empty(parent, "Aucun texte disponible.")
            return

        pane = tk.PanedWindow(parent, orient="horizontal", bg=t["BG"], sashwidth=8, sashrelief="flat", bd=0)
        pane.pack(fill="both", expand=True)

        left_panel = self.mk_panel(pane, radius=20, pad=10)
        right_panel = self.mk_panel(pane, radius=20, pad=16, fill=t["BG"])
        pane.add(left_panel, minsize=200)
        pane.add(right_panel, minsize=340)

        tk.Label(left_panel.inner, text="ARTICLES", font=self.FONT_SMALL, bg=left_panel.fill, fg=t["TEXT_DIM"]).pack(fill="x", pady=(2, 10), padx=4)

        txt_area = tk.Text(right_panel.inner, bg=t["BG"], fg=t["TEXT"], font=self.FONT_MONO, wrap="word",
                            relief="flat", bd=0, padx=4, pady=4, state="disabled", insertbackground=t["TEXT"])
        txt_area.pack(fill="both", expand=True)

        def load_text(url):
            txt_area.config(state="normal")
            txt_area.delete("1.0", "end")
            txt_area.insert("end", "Chargement…")
            txt_area.config(state="disabled")

            def fetch():
                try:
                    content = requests.get(url, timeout=10).text
                except Exception:
                    content = "[Erreur de chargement]"
                self.after(0, lambda: (txt_area.config(state="normal"), txt_area.delete("1.0", "end"),
                                        txt_area.insert("end", content), txt_area.config(state="disabled")))
            threading.Thread(target=fetch, daemon=True).start()

        for item in textes:
            b = RoundedButton(left_panel.inner, item["nom"], command=lambda u=item["url"]: load_text(u),
                               font=self.FONT_LABEL, fill=self.glass_color(t["BG3"]), hover_fill=t["ACCENT"],
                               text_color=t["TEXT"], hover_text=t["ON_ACCENT"], radius=12, anchor="w",
                               stretch=True, bg=left_panel.fill)
            b.pack(fill="x", pady=3)

    # ── IMAGES ────────────────────────────────────────────────────────────────
    def _populate_images(self):
        t = self.t
        parent = self.tab_images
        for widget in parent.winfo_children(): widget.destroy()

        if "images" in self.load_errors:
            self._empty(parent, f"⚠️ Erreur de chargement du fichier JSON :\n\n{self.load_errors['images']}")
            return
        images = [x for x in self.data.get("images", []) if x.get("url")]
        if not images:
            self._empty(parent, "Aucune image disponible.")
            return

        outer_panel = self.mk_panel(parent, radius=20, pad=4)
        outer_panel.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer_panel.inner, bg=outer_panel.fill, highlightthickness=0)
        vsb = tk.Scrollbar(outer_panel.inner, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        grid_frame = tk.Frame(canvas, bg=outer_panel.fill)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        grid_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        cell_bg = self.glass_color(t["BG3"])
        cols = 3
        for i, item in enumerate(images):
            cell_panel = RoundedPanel(grid_frame, bg_parent=outer_panel.fill, fill=cell_bg, radius=18, pad=10)
            cell_panel.grid(row=i // cols, column=i % cols, padx=10, pady=10, sticky="nsew")
            cell_panel.config(width=210, height=180, cursor="hand2")

            lbl_img = tk.Label(cell_panel.inner, bg=cell_bg, text="⏳", font=(FONT_FAMILY, 22), fg=t["TEXT_DIM"])
            lbl_img.pack(expand=True)
            tk.Label(cell_panel.inner, text=item["nom"], font=self.FONT_SMALL, bg=cell_bg, fg=t["TEXT_MUTED"]).pack(pady=(4, 0))

            url, nom = item["url"], item["nom"]
            for w in (cell_panel, lbl_img):
                w.bind("<Button-1>", lambda e, u=url, n=nom: self._open_lightbox(u, n))
            threading.Thread(target=self._load_image, args=(url, lbl_img), daemon=True).start()

        for c in range(cols): grid_frame.columnconfigure(c, weight=1)

    def _load_image(self, url, label):
        try:
            from PIL import Image, ImageTk
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content))
            img.thumbnail((180, 120))
            photo = ImageTk.PhotoImage(img)
            self._img_refs.append(photo)
            self.after(0, lambda: label.config(image=photo, text=""))
        except Exception:
            self.after(0, lambda: label.config(text="❌", font=self.FONT_SMALL, fg=self.t["DANGER"]))

    # ── LIGHTBOX (ZOOM + DEPLACEMENT) ─────────────────────────────────────────
    def _open_lightbox(self, url, nom):
        t = self.t
        self.log(f"Ouverture de la vue détaillée pour '{nom}'")

        is_glass_active = self.theme_name == "splash" and IS_WINDOWS
        lb_bg = t["TRANSPARENT_KEY"] if is_glass_active else t["BG"]

        lb = tk.Toplevel(self)
        lb.title(nom)
        lb.configure(bg=lb_bg)
        lb.geometry("900x720")
        if is_glass_active:
            try:
                lb.attributes("-transparentcolor", t["TRANSPARENT_KEY"])
            except tk.TclError:
                is_glass_active = False
        lb.grab_set()

        card_fill = lb_bg if is_glass_active else t["BG2"]
        card = RoundedPanel(lb, bg_parent=lb_bg, fill=card_fill, radius=24, pad=16)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(card.inner, text=nom, font=self.FONT_SUBHEAD, bg=card_fill, fg=t["ACCENT_SOFT"]).pack()
        tk.Label(card.inner, text="Molette pour zoomer · Clic-glissé pour se déplacer",
                 font=self.FONT_SMALL, bg=card_fill, fg=t["TEXT_DIM"]).pack(pady=(2, 8))

        canvas = tk.Canvas(card.inner, bg=card_fill, highlightthickness=0, cursor="fleur")
        canvas.pack(fill="both", expand=True)
        canvas.create_text(430, 250, text="Chargement de l'image haute définition…", font=self.FONT_SUB,
                            fill=t["TEXT_DIM"], tags="loading")

        def on_canvas_configure(event):
            loading_items = canvas.find_withtag("loading")
            if loading_items:
                canvas.coords(loading_items[0], event.width // 2, event.height // 2)
        canvas.bind("<Configure>", on_canvas_configure)

        control_frame = tk.Frame(card.inner, bg=card_fill, pady=10)
        control_frame.pack(fill="x")

        self.current_img_data = None
        self.current_zoom_level = 1.0
        lb.drag_x, lb.drag_y = 0, 0

        def on_drag_start(event):
            lb.drag_x, lb.drag_y = event.x, event.y

        def on_drag(event):
            dx, dy = event.x - lb.drag_x, event.y - lb.drag_y
            canvas.move("img", dx, dy)
            lb.drag_x, lb.drag_y = event.x, event.y

        canvas.bind("<ButtonPress-1>", on_drag_start)
        canvas.bind("<B1-Motion>", on_drag)

        def adjust_zoom(factor, relative=True):
            if not self.current_img_data: return
            if relative:
                self.current_zoom_level *= factor
            else:
                self.current_zoom_level = factor
                cw, ch = canvas.winfo_width() or 860, canvas.winfo_height() or 480
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
                    cw, ch = canvas.winfo_width() or 860, canvas.winfo_height() or 480
                    canvas.create_image(cw // 2, ch // 2, image=photo, anchor="center", tags="img")
            except Exception as e:
                self.log(f"Erreur de rendu lors du zoom : {e}")

        def on_mouse_wheel(event):
            if event.num == 5 or event.delta < 0: adjust_zoom(0.9)
            elif event.num == 4 or event.delta > 0: adjust_zoom(1.1)

        ctrl_bg = card_fill
        btn_zoom_in  = RoundedButton(control_frame, "Zoom avant", command=lambda: adjust_zoom(1.2), font=self.FONT_BTN, fill=t["BG3"] if not is_glass_active else ctrl_bg, hover_fill=t["ACCENT"], text_color=t["TEXT"] if not is_glass_active else t["ACCENT_SOFT"], hover_text=t["ON_ACCENT"], radius=999, bg=ctrl_bg)
        btn_zoom_out = RoundedButton(control_frame, "Zoom arrière", command=lambda: adjust_zoom(0.8), font=self.FONT_BTN, fill=t["BG3"] if not is_glass_active else ctrl_bg, hover_fill=t["ACCENT"], text_color=t["TEXT"] if not is_glass_active else t["ACCENT_SOFT"], hover_text=t["ON_ACCENT"], radius=999, bg=ctrl_bg)
        btn_reset    = RoundedButton(control_frame, "Réinitialiser", command=lambda: adjust_zoom(1.0, relative=False), font=self.FONT_BTN, fill=t["BG3"] if not is_glass_active else ctrl_bg, hover_fill=t["ACCENT"], text_color=t["TEXT"] if not is_glass_active else t["ACCENT_SOFT"], hover_text=t["ON_ACCENT"], radius=999, bg=ctrl_bg)
        btn_close    = RoundedButton(control_frame, "Fermer", command=lb.destroy, font=self.FONT_BTN, fill=t["BG3"] if not is_glass_active else ctrl_bg, hover_fill=t["DANGER"], text_color=t["TEXT"] if not is_glass_active else t["ACCENT_SOFT"], hover_text=t["ON_ACCENT"], radius=999, bg=ctrl_bg)

        for b in (btn_zoom_in, btn_zoom_out, btn_reset, btn_close):
            b.pack(side="left", padx=6, expand=True)

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
                raw_img.thumbnail((820, 480))
                self.current_img_data = raw_img
                self.current_zoom_level = 1.0
                self.after(0, render_image)
                self.log(f"Image originale '{nom}' chargée et prête pour manipulation.")
            except ImportError:
                self.log("Erreur Pillow manquant lors du chargement de la vue détaillée.")
                canvas.delete("loading")
                canvas.create_text(430, 250, text="Installe Pillow :\npip install Pillow", font=self.FONT_SUB,
                                    fill=t["TEXT_DIM"], tags="loading")
            except Exception as e:
                self.log(f"Erreur récupération image HD '{nom}' : {e}")
                canvas.delete("loading")
                canvas.create_text(430, 250, text=f"Erreur : {e}", font=self.FONT_SUB, fill=t["DANGER"], tags="loading")

        threading.Thread(target=fetch, daemon=True).start()

    # ── DOCUMENTS ─────────────────────────────────────────────────────────────
    def _populate_documents(self):
        t = self.t
        parent = self.tab_fichiers
        for widget in parent.winfo_children(): widget.destroy()

        if "documents" in self.load_errors:
            self._empty(parent, f"⚠️ Erreur de chargement du fichier JSON :\n\n{self.load_errors['documents']}")
            return
        documents = [x for x in self.data.get("documents", []) if x.get("url")]
        if not documents:
            self._empty(parent, "Aucun document disponible.")
            return

        tk.Label(parent, text="Documents de cours disponibles", font=self.FONT_SUBHEAD, bg=t["BG"], fg=t["TEXT"],
                 pady=6).pack(anchor="w")

        scroll_panel = self.mk_panel(parent, radius=20, pad=10)
        scroll_panel.pack(fill="both", expand=True, pady=(8, 0))

        is_glass_active = self.theme_name == "splash" and self.can_glass
        for item in documents:
            row_bg = self.glass_color(t["BG3"])
            row = RoundedPanel(scroll_panel.inner, bg_parent=scroll_panel.fill, fill=row_bg, radius=16, pad=12)
            row.pack(fill="x", pady=5)

            content = tk.Frame(row.inner, bg=row_bg)
            content.pack(fill="x")

            icon_c = tk.Canvas(content, width=36, height=36, bg=row_bg, highlightthickness=0)
            icon_c.pack(side="left", padx=(0, 12))
            icon_c.create_oval(1, 1, 35, 35, fill=t["ACCENT"], outline="")
            icon_c.create_text(18, 18, text="📦", font=(FONT_FAMILY, 13))

            tk.Label(content, text=item["nom"], font=(FONT_FAMILY, 11, "bold"), bg=row_bg, fg=t["TEXT"],
                     anchor="w").pack(side="left", fill="x", expand=True)

            btn_fill = t["TRANSPARENT_KEY"] if is_glass_active else t["ACCENT"]
            btn_fg = t["ACCENT_SOFT"] if is_glass_active else t["ON_ACCENT"]
            btn = RoundedButton(content, "Télécharger", font=self.FONT_BTN, fill=btn_fill, hover_fill=t["ACCENT_HOV"],
                                 text_color=btn_fg, hover_text=t["ON_ACCENT"], radius=999, bg=row_bg)
            btn.config(command=lambda u=item["url"], n=item["nom"], b=btn: self._download(u, n, b))
            btn.pack(side="right")

            row.autosize()

        scroll_panel.autosize()

    def _download(self, url, nom, btn):
        t = self.t
        save_path = filedialog.asksaveasfilename(initialfile=nom, title="Enregistrer sous…")
        if not save_path: return
        btn.set_disabled(True, disabled_fill=t["TEXT_DIM"])
        btn.set_text("En cours…")

        def fetch():
            try:
                r = requests.get(url, timeout=30, stream=True)
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                self.after(0, lambda: (btn.set_disabled(False), btn.set_colors(fill=t["SUCCESS"]), btn.set_text("Téléchargé")))
            except Exception:
                self.after(0, lambda: (btn.set_disabled(False), btn.set_text("Télécharger"),
                                        messagebox.showerror("Erreur", "Échec du téléchargement.")))
        threading.Thread(target=fetch, daemon=True).start()

    # ── SUGGESTIONS ───────────────────────────────────────────────────────────
    def _populate_suggestions(self):
        t = self.t
        parent = self.tab_suggestions
        for widget in parent.winfo_children(): widget.destroy()

        outer = tk.Frame(parent, bg=t["BG"])
        outer.pack(expand=True)

        panel = self.mk_panel(outer, radius=22, pad=24)
        panel.pack()
        box = panel.inner
        panel.config(width=460)

        tk.Label(box, text="Envoyer une suggestion", font=self.FONT_SUBHEAD, bg=panel.fill, fg=t["TEXT"]).pack(anchor="w")
        tk.Label(box, text="Une idée, un bug, une remarque ? Écris-nous.", font=self.FONT_SMALL, bg=panel.fill,
                 fg=t["TEXT_DIM"]).pack(anchor="w", pady=(2, 16))

        tk.Label(box, text="TON PRÉNOM (OPTIONNEL)", font=self.FONT_SMALL, bg=panel.fill, fg=t["TEXT_DIM"]).pack(anchor="w")
        entry_panel = self.mk_panel(box, radius=14, pad=2, fill=t["BG"])
        entry_panel.pack(fill="x", pady=(4, 14))
        entry_panel.config(height=42)
        self.f_nom = tk.Entry(entry_panel.inner, bg=t["BG"], fg=t["TEXT"], font=self.FONT_SUB, relief="flat",
                               bd=0, insertbackground=t["TEXT"])
        self.f_nom.pack(fill="both", expand=True, padx=8)

        tk.Label(box, text="MESSAGE *", font=self.FONT_SMALL, bg=panel.fill, fg=t["TEXT_DIM"]).pack(anchor="w")
        msg_panel = self.mk_panel(box, radius=14, pad=4, fill=t["BG"])
        msg_panel.pack(fill="x", pady=(4, 18))
        msg_panel.config(height=140)
        self.f_msg = tk.Text(msg_panel.inner, bg=t["BG"], fg=t["TEXT"], font=self.FONT_SUB, relief="flat", bd=0,
                              insertbackground=t["TEXT"])
        self.f_msg.pack(fill="both", expand=True)

        btn_send = self.mk_button(box, "Envoyer la suggestion", command=self._send_mail, kind="primary", stretch=True, bg=panel.fill)
        btn_send.pack(fill="x")

        self.lbl_feedback = tk.Label(box, text="", font=self.FONT_SMALL, bg=panel.fill, fg=t["SUCCESS"])
        self.lbl_feedback.pack(pady=(10, 0))

        panel.autosize()

    def _send_mail(self):
        nom, message = self.f_nom.get().strip(), self.f_msg.get("1.0", "end").strip()
        if not message: return
        subject = f"[Faster Homework] Suggestion" + (f" — {nom}" if nom else "")
        body = f"De : {nom}\n\n{message}"
        webbrowser.open(f"mailto:{MAIL_TO}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}")
        self.f_msg.delete("1.0", "end")
        self.lbl_feedback.config(text="Ton client mail s'est ouvert avec le message pré-rempli ✓")

    def _empty(self, parent, msg):
        t = self.t
        tk.Label(parent, text=msg, font=self.FONT_SUB, bg=t["BG"], fg=t["TEXT_DIM"], justify="left").pack(pady=50, padx=20)


if __name__ == "__main__":
    app = App()
    app.mainloop()