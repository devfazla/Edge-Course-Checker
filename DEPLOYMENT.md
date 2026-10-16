# Deployment and operations

How the Windows build is produced, how the remote activation and update switch
works, and how to ship changes later. Written for whoever maintains
`Edge-Course-Checker` next, including a future you.

Everything here is driven from a single file, `main.py`. There is no backend
service to run; the only "server" side is one text file you edit on GitHub.

## What ships

| File | Role |
|---|---|
| `main.py` | The whole application. |
| `assets/` | Logo (`images/`), `icon.ico`, `icon.png`. Bundled into the exe. |
| `EdgeCourseChecker.spec` | PyInstaller build config (one-file, windowed). |
| `installer.iss` | Inno Setup installer script. |
| `build.ps1` | Installs requirements, runs PyInstaller. |
| `requirements.txt` | `requests`, `Pillow`, `pyinstaller`. |

### On the user's machine after install

The app installs to `Program Files\Edge Course Checker\` (or a per-user
location if there's no admin rights) and creates, right there:

```
Edge Course Checker/
  EdgeCourseChecker.exe
  input/            drop combo files here (phone:password per line)
  results/
    HIT/            accounts that returned a status
    BAD/            accounts with no status
  settings.json     created on first launch
```

`input/`, `results/`, and `settings.json` are **never** overwritten by a new
setup, so a user keeps their data and settings across updates. They are also
gitignored, so never commit them.

## Building the exe and installer

From a terminal in the project root:

```powershell
python -m pip install -r requirements.txt
python -m PyInstaller --clean --noconfirm EdgeCourseChecker.spec   # -> dist\EdgeCourseChecker.exe
ISCC.exe installer.iss                                             # -> output\EdgeCourseChecker-Setup-<version>.exe
```

Or run `pwsh -File build.ps1` for the first two steps. `pwsh` is PowerShell 7;
`powershell` (5.1) works too if you prefer. Inno Setup is a separate install and
adds `ISCC.exe` to PATH.

The exe is a single ~37 MB file. It is not signed, so SmartScreen warns "Unknown
publisher" on first run (More info → Run anyway). Code-signing is the only way to
stop that prompt; it's optional.

The packaged build behaves differently from running `python main.py`: the exe has
`requests` and `Pillow` frozen inside it, so it **skips** the first-run
dependency installer and goes straight to the gate check, then the dashboard.

## The remote activation and update switch

On every launch, before showing anything, the app downloads one small text file:

```
https://raw.githubusercontent.com/devfazla/public-cst-cmd/main/cmd3.txt
```

This uses only the Python standard library (`urllib`), so it works even before
`requests` is installed and in the frozen exe.

### File format

One `key = value` per line. A trailing `;` is ignored, so this:

```
ecc = true; ecc-up-f = false; ecc-v = 1.0.0
```

and the same spread over three lines are equivalent. Keys are lowercased when
parsed.

### The keys

| Key | Meaning |
|---|---|
| `ecc` | Master activation switch. `true` runs the app. Anything else pauses it. |
| `ecc-up-f` | Force update. When `true`, the app blocks everything and only offers the release page. |
| `ecc-up` | Soft update. When `true`, the app opens but shows an "update available" chip. |
| `ecc-v` | Latest version string, e.g. `1.1.0`. If higher than the running version, it behaves like `ecc-up`. |

Truth-like values: `true`, `1`, `yes`, `on` (case-insensitive). Everything else
counts as false.

### How a launch resolves

The app checks in this order and stops at the first match:

1. **paused** — `ecc` is not true → a full-screen "This app is paused by Author
   @devFazla" page with Retry / Close. The dashboard never loads.
2. **force** — `ecc-up-f` is true → a full-screen "Update Required" page with
   Update now / Close. The dashboard never loads.
3. **update** — `ecc-up` is true, or `ecc-v` is higher than `APP_VERSION` → the
   app opens normally, plus a clickable version chip in the top bar.
4. **ok** — none of the above → the app opens, no prompt.

Version compare treats the dotted number as a tuple, so `1.10.0 > 1.9.0` and
`1.0.1 > 1.0.0`. Non-numeric junk falls back to a plain compare.

**If the fetch fails** (offline, file moved, GitHub down), the app **opens
normally**. A control outage never locks out a legitimate user.

Both the pause and force pages open the same destination when the user chooses to
update / view releases:

```
https://github.com/devfazla/Edge-Course-Checker/releases/latest
```

`/releases/latest` always redirects to the newest release, so that link never
rots.

### Managing it later, from `cmd3.txt`

You change app behavior without rebuilding anything, just by editing that file:

| Want | Set |
|---|---|
| Normal operation | `ecc = true` |
| Pause everyone | `ecc = false` |
| Tell everyone an update exists | `ecc-v = <new version>` (or `ecc-up = true`) |
| Stop old builds from working | `ecc-up-f = true` and `ecc-v = <new version>` |
| Back to quiet after an update push | `ecc-up = false`, `ecc-up-f = false`, `ecc-v = <current>` |

## Shipping a new version, start to finish

1. **Bump the version in two places, to the same value:**
   - `APP_VERSION = "1.1.0"` in `main.py`
   - `#define MyAppVersion "1.1.0"` in `installer.iss`
2. **Rebuild:**
   ```powershell
   Remove-Item -Recurse -Force build, dist, output   # clean slate
   pwsh -File build.ps1
   ISCC.exe installer.iss
   ```
3. **Test** the new `dist\EdgeCourseChecker.exe` locally.
4. **Publish a GitHub release** and upload
   `output\EdgeCourseChecker-Setup-1.1.0.exe` as the release asset. Tag it
   `v1.1.0`.
5. **Flip `cmd3.txt`** so older installs can find it:
   - soft: set `ecc-v = 1.1.0`
   - hard (old builds must stop): also set `ecc-up-f = true`

Users on the old build then see the update prompt; clicking it opens the release
page; they download the new setup and run it **over** the old install. Inno
closes the running old exe, replaces it, and leaves `settings.json`, `input/`,
and `results/` untouched. That's the "merge" behavior: no data is lost, no manual
uninstall needed.

### Before you push people to a new version

Make sure the version you publish is **greater than or equal to** the `ecc-v` you
set. If `ecc-v` is higher than every setup you've actually published, a forced
update can leave a user with no installable file. Keep `ecc-v` pointing at a
release that exists.

## Quick reference

- Change app logic / UI: edit `main.py`, rebuild.
- Change the version users see in the title: `APP_VERSION` in `main.py`.
- Change when users are told to update: `ecc-v` (and `ecc-up` / `ecc-up-f`) in
  `cmd3.txt`.
- Stop or resume the whole app: `ecc` in `cmd3.txt`.
- The release link users are sent to is fixed at the repo's `/releases/latest`.
