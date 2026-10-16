# Edge Course Checker

A desktop app, written in Python and Tkinter, that checks account combos
against the Edge Course API and sorts what comes back into working (HIT) and
dead (BAD) folders. It runs the checks across several threads at once. The
whole thing lives in one file, `main.py`.

Made by [@devFazla](https://devfazla.com).

## What it does

When you start it, the app checks whether `requests` and `Pillow` are installed
and up to date, then installs or updates whatever is missing while showing you
the progress. There's a "Skip check" button for when you're offline.

The main window has a sidebar with three pages.

- **Input.** Lists the `.txt` files it found in the input folder, with counts
  for files, combos, hits and bads. "Add more" opens a picker so you can select
  several files at once and copy them into the input folder.
- **Output.** Streams results as the run happens, color coded by status.
- **Settings.** Holds the folder paths, the per-worker delay in milliseconds,
  the worker count, and the API endpoints. Saved to `settings.json`.

Working logins are written to `results/HIT`, failures to `results/BAD`.

## Requirements

- Python 3.13 or newer, with Tkinter (bundled with the Windows installer).
- `requests` and `Pillow`. The app installs them on first run, or do it
  yourself:

```bash
pip install requests Pillow
```

## Run it

```bash
git clone https://github.com/devfazla/Edge-Course-Checker.git
cd Edge-Course-Checker
python main.py
```

## Input format

One combo per line, in any `.txt` file inside the input folder:

```
phone:password
phone:password
```

Each file is read on its own. The input and results folders are created on
launch if they aren't there.

## Layout

```
.
├── main.py         # the app: GUI and checker
├── make_logo.py    # regenerates the logo and icon
├── assets/         # logo.png, logo_256.png, icon.ico
├── input/          # your .txt combo files
└── results/
    ├── HIT/
    └── BAD/
```

## Build a Windows exe

Make the executable with PyInstaller, then wrap it in a setup with Inno Setup.

```powershell
pwsh -File build.ps1        # produces dist\EdgeCourseChecker.exe
ISCC.exe installer.iss      # produces output\EdgeCourseChecker-Setup-1.0.0.exe
```

`build.ps1` installs the deps from `requirements.txt` and runs the
`EdgeCourseChecker.spec`. Inno Setup is a separate download; once installed it
adds `ISCC.exe` to your PATH. The packaged app skips the first-run dependency
installer, since `requests` and `Pillow` are already bundled.

For the remote activation/update switch and the release process, see
[DEPLOYMENT.md](DEPLOYMENT.md).

## A note on use

Run this against accounts you own or have permission to test. Anything else is
on you.

## Portfolio (Author)

<div align="start">

<img src="assets/fazla.png" alt="Author" width="140" />

</div>

| | |
|---|---|
| **Name** | *Fazla Rabbi* |
| **Role** | Software Developer |
| **Portfolio / Website** | *https://devfazla.com* |
| **Contact** | [contact@devfazla.com](mailto:contact@devfazla.com) |

<div align="start">

<b>Socials:</b><br>

<a href="https://devfazla.com" title="Website"><img src="https://cdn.simpleicons.org/googlechrome" height="20" alt="Website" /></a>&nbsp;&nbsp;
<a href="https://github.com/devfazla" title="GitHub"><img src="https://cdn.simpleicons.org/github" height="20" alt="GitHub" /></a>&nbsp;&nbsp;
<a href="https://www.linkedin.com/in/devfazla/" title="LinkedIn"><img src="https://cdn.simpleicons.org/linkedin" height="20" alt="LinkedIn" /></a>&nbsp;&nbsp;
<a href="https://www.facebook.com/devfazla" title="Facebook"><img src="https://cdn.simpleicons.org/facebook" height="20" alt="Facebook" /></a>&nbsp;&nbsp;
<a href="https://x.com/devfazla" title="X (Twitter)"><img src="https://cdn.simpleicons.org/x" height="18" alt="X" /></a>&nbsp;&nbsp;

</div>

### Key Skills in This Project

- **Language & GUI**: `Python 3.13`, `Tkinter` / `ttk`
- **Concurrency**: `threading`, `concurrent.futures` (`ThreadPoolExecutor`)
- **HTTP & Networking**: `requests`
- **Image handling**: `Pillow`
- **Packaging & distribution**: `PyInstaller`, `Inno Setup`
