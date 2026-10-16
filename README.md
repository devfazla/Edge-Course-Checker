# Edge Course Checker

A desktop app, written in Python and Tkinter, that checks account combos
against the Edge Course API and sorts what comes back into working (HIT) and
dead (BAD) folders. It runs the checks across several threads at once. The
whole thing lives in one file, `abc.py`.

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
python abc.py
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
├── abc.py          # the app: GUI and checker
├── make_logo.py    # regenerates the logo and icon
├── assets/         # logo.png, logo_256.png, icon.ico
├── input/          # your .txt combo files
└── results/
    ├── HIT/
    └── BAD/
```

## A note on use

Run this against accounts you own or have permission to test. Anything else is
on you.

## Author

@devFazla, [devfazla.com](https://devfazla.com)
