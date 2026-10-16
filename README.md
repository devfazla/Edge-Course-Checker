# Edge Course Checker

A modern, Fluent-styled desktop tool (Python + Tkinter) that validates account
combos against the Edge Course API in parallel and sorts the results into
**HIT** / **BAD** folders — with a polished GUI dashboard instead of a terminal.

> Made by [@devFazla](https://devfazla.com)

---

## ✨ Features

- **Startup dependency checker** — verifies, installs, and updates required
  packages (`requests`, `Pillow`) on launch with live, detailed progress and a
  **Skip check** button for offline use.
- **Modern Fluent GUI** — rounded bento stat cards, a full-height sidebar
  drawer navigation, custom slim scrollbars, and empty-state placeholders.
- **Parallel checking** — multi-threaded via `ThreadPoolExecutor` with
  configurable workers and per-worker delay (in milliseconds).
- **Input manager** — auto-detects `.txt` combo files in the input folder and
  lets you **Add more** files through a multi-select picker (copied into the
  input folder automatically).
- **Live activity log** — results stream to the Output page in real time with
  color-coded statuses.
- **Organized results** — hits and bads are written to `results/HIT` and
  `results/BAD`.
- **Fully responsive** — adapts to window size; nothing clips.
- **Persistent settings** — folders, request tuning, and API endpoints are
  editable in the Settings page and saved to `settings.json`.

---

## 📦 Requirements

- **Python 3.13+** with Tkinter included (standard on Windows).
- `requests` and `Pillow` — installed automatically at first launch, or manually:

```bash
pip install requests Pillow
```

---

## 🚀 Getting started

```bash
git clone https://github.com/devfazla/Edge-Course-Checker.git
cd Edge-Course-Checker
python abc.py
```

On first run the app checks and installs dependencies, then opens the dashboard.

---

##  Project structure

```
.
├── abc.py              # The whole application (GUI + checker)
├── make_logo.py        # Helper that generates the app logo / icon
├── assets/             # logo.png, logo_256.png, icon.ico
├── input/              # Drop your .txt combo files here (auto-created)
└── results/
    ├── HIT/            # Valid accounts
    └── BAD/            # Invalid / failed accounts
```

The `input/` and `results/` folders are created automatically on launch at the
currently targeted location.

---

## 🧾 Input format

Each `.txt` file inside the input folder holds one combo per line:

```
phone:password
phone:password
```

Every `.txt` file is treated as a separate input source.

---

## ⚙️ Usage

1. **Input page** — confirm your detected files and combo count, then click
   **Start**. Use **Add more** to import additional files, or **Refresh** to
   rescan the folder.
2. **Output page** — watch results stream live; use **Clear** to reset the log.
3. **Settings page** — change the input/HIT/BAD folders, delay (ms), worker
   count, and API endpoints, then **Save settings**.

---

## 🔒 Disclaimer

This tool is intended for legitimate, authorized account-recovery and security
testing on accounts you own or have explicit permission to use. Misuse is the
responsibility of the user.

---

## 📄 License

Released for educational purposes. See the source for details.

## 👤 Author

**@devFazla** — [devfazla.com](https://devfazla.com)
