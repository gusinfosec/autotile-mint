#!/usr/bin/env python3
"""
AutoTile for Linux Mint (Cinnamon/X11)
--------------------------------------
Arranges visible, normal windows into a smart grid layout using wmctrl + xprop.
Skips minimized or ignored apps, respects Cinnamon panels, and adds spacing.
"""

import subprocess
import math
import shlex

# === CONFIG ===
GAP = 10                 # pixels between windows
FORCE_COLS = 0           # 0 = auto √n layout, >0 = fixed number of columns
IGNORE_APPS = ["Spotify", "Calculator"]  # match part of WM_CLASS or title

# === CORE HELPERS ===
def run(cmd):
    """Run a shell command and return its decoded output."""
    return subprocess.check_output(shlex.split(cmd), stderr=subprocess.DEVNULL).decode()

def get_current_workarea():
    """
    Parse 'wmctrl -d' to get current desktop's work area (excludes panels).
    Returns (wa_x, wa_y, wa_w, wa_h, current_desktop_index).
    """
    out = run("wmctrl -d").splitlines()
    current = [l for l in out if '*' in l][0]
    parts = current.split()
    desk_idx = int(parts[0])

    # Example: '... WA: 0,24 1920x1056'
    wa_idx = parts.index('WA:')
    wa_xy = parts[wa_idx + 1]
    wa_wh = parts[wa_idx + 2]

    wa_x, wa_y = map(int, wa_xy.rstrip(',').split(','))
    wa_w, wa_h = map(int, wa_wh.split('x'))
    return wa_x, wa_y, wa_w, wa_h, desk_idx

def list_windows():
    """Return list of window IDs (hex strings) from wmctrl -l (all windows)."""
    out = run("wmctrl -l").splitlines()
    return [ln.split()[0] for ln in out if ln.strip()]

def on_current_desktop(win_id, current_desktop):
    """Check if window is on current desktop via _NET_WM_DESKTOP."""
    try:
        out = run(f"xprop -id {win_id} _NET_WM_DESKTOP")
        if "0xffffffff" in out:
            return True  # sticky window
        desk = int(out.split('=')[1].strip())
        return desk == current_desktop
    except Exception:
        return False

def is_normal_window(win_id):
    """Filter only normal app windows."""
    try:
        out = run(f"xprop -id {win_id} _NET_WM_WINDOW_TYPE")
        return "_NET_WM_WINDOW_TYPE_NORMAL" in out
    except Exception:
        return False

def is_hidden_or_minimized(win_id):
    """Skip minimized/hidden windows."""
    try:
        out = run(f"xprop -id {win_id} _NET_WM_STATE")
        return "_NET_WM_STATE_HIDDEN" in out
    except Exception:
        return False

def is_ignored(win_id):
    """Check if the window name/class matches any ignored app."""
    try:
        info = run(f"xprop -id {win_id} WM_CLASS WM_NAME")
        return any(ign.lower() in info.lower() for ign in IGNORE_APPS)
    except Exception:
        return False

# === MAIN LOGIC ===
def get_tileable_windows():
    wa_x, wa_y, wa_w, wa_h, cur_desk = get_current_workarea()
    all_wins = list_windows()
    tileable = []
    for wid in all_wins:
        if (
            on_current_desktop(wid, cur_desk)
            and is_normal_window(wid)
            and not is_hidden_or_minimized(wid)
            and not is_ignored(wid)
        ):
            tileable.append(wid)
    return tileable, (wa_x, wa_y, wa_w, wa_h)

def tile_windows():
    windows, (wa_x, wa_y, wa_w, wa_h) = get_tileable_windows()
    if not windows:
        return

    n = len(windows)
    cols = FORCE_COLS if FORCE_COLS > 0 else math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    # account for gaps inside work area
    cell_w = (wa_w - GAP * (cols + 1)) // cols
    cell_h = (wa_h - GAP * (rows + 1)) // rows

    for idx, wid in enumerate(windows):
        r = idx // cols
        c = idx % cols
        x = wa_x + GAP + c * (cell_w + GAP)
        y = wa_y + GAP + r * (cell_h + GAP)
        try:
            subprocess.call(["wmctrl", "-i", "-r", wid, "-e", f"0,{x},{y},{cell_w},{cell_h}"])
        except Exception:
            continue  # skip disappearing windows

# === ENTRY POINT ===
if __name__ == "__main__":
    tile_windows()

