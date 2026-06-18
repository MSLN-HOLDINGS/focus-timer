#!/usr/bin/env python3
"""Focus Timer — a terminal Pomodoro timer with visual progress bar."""

import time
import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
WORK_MINUTES = 25
SHORT_BREAK_MINUTES = 5
LONG_BREAK_MINUTES = 15
SESSIONS_BEFORE_LONG = 4
BAR_WIDTH = 40
STATS_FILE = Path(__file__).parent / "sessions.json"

# ── Colors ───────────────────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    DIM     = "\033[2m"

def clear():
    os.system("clear")

def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

# ── Stats ────────────────────────────────────────────────────────────────────
def load_stats():
    if STATS_FILE.exists():
        with open(STATS_FILE) as f:
            return json.load(f)
    return {"total_sessions": 0, "total_minutes": 0, "today": {"date": "", "sessions": 0}}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def record_session(stats, minutes):
    today = datetime.now().strftime("%Y-%m-%d")
    stats["total_sessions"] += 1
    stats["total_minutes"] += minutes
    if stats["today"]["date"] != today:
        stats["today"] = {"date": today, "sessions": 0}
    stats["today"]["sessions"] += 1
    save_stats(stats)

# ── Sound ────────────────────────────────────────────────────────────────────
def beep(times=3):
    """Play a system sound on macOS or fall back to terminal bell."""
    for _ in range(times):
        try:
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"],
                           capture_output=True, timeout=3)
        except Exception:
            sys.stdout.write("\a")
            sys.stdout.flush()
        time.sleep(0.4)

# ── Rendering ────────────────────────────────────────────────────────────────
def render_bar(elapsed, total, color):
    fraction = elapsed / total
    filled = int(BAR_WIDTH * fraction)
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    pct = int(fraction * 100)
    return f"{color}[{bar}]{C.RESET} {pct:>3}%"

def fmt_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

def render_screen(phase, elapsed, total, session_num, stats, color, label):
    remaining = total - elapsed
    clear()

    today = stats["today"]["sessions"]
    total_s = stats["total_sessions"]

    print(f"\n  {C.BOLD}🍅 Focus Timer{C.RESET}  {C.DIM}Session #{session_num}{C.RESET}")
    print(f"  {C.DIM}Today: {today} sessions  ·  All time: {total_s} sessions{C.RESET}")
    print()
    print(f"  {color}{C.BOLD}{label}{C.RESET}")
    print()
    print(f"  {render_bar(elapsed, total, color)}")
    print()
    print(f"  {C.BOLD}  {fmt_time(remaining)}{C.RESET} remaining  {C.DIM}({fmt_time(elapsed)} elapsed){C.RESET}")
    print()
    print(f"  {C.DIM}Press Ctrl+C to quit{C.RESET}")

# ── Countdown ────────────────────────────────────────────────────────────────
def run_phase(label, minutes, session_num, stats, color):
    total = minutes * 60
    start = time.time()
    try:
        while True:
            elapsed = time.time() - start
            if elapsed >= total:
                break
            render_screen(label, elapsed, total, session_num, stats, color, label)
            time.sleep(0.5)
        render_screen(label, total, total, session_num, stats, color, label)
    except KeyboardInterrupt:
        show_cursor()
        print(f"\n\n  {C.YELLOW}Timer stopped.{C.RESET}\n")
        sys.exit(0)

def prompt_continue(message):
    show_cursor()
    print(f"\n  {C.BOLD}{message}{C.RESET}")
    print(f"  Press {C.BOLD}Enter{C.RESET} to continue or {C.BOLD}Ctrl+C{C.RESET} to quit...")
    try:
        input()
        hide_cursor()
        return True
    except (KeyboardInterrupt, EOFError):
        show_cursor()
        print(f"\n  {C.YELLOW}Goodbye! Great work today.{C.RESET}\n")
        sys.exit(0)

# ── Summary screen ────────────────────────────────────────────────────────────
def show_summary(stats):
    clear()
    today = stats["today"]["sessions"]
    total_sessions = stats["total_sessions"]
    total_hours = stats["total_minutes"] // 60
    total_mins  = stats["total_minutes"] % 60
    print(f"\n  {C.BOLD}🍅 Focus Timer — Session Complete!{C.RESET}\n")
    print(f"  {C.GREEN}✓ Today:{C.RESET}     {today} Pomodoro{'s' if today != 1 else ''} = {today * WORK_MINUTES} focused minutes")
    print(f"  {C.BLUE}✓ All time:{C.RESET}  {total_sessions} sessions = {total_hours}h {total_mins}m")
    print()

# ── Main loop ────────────────────────────────────────────────────────────────
def main():
    stats = load_stats()
    session_num = 0

    clear()
    print(f"\n  {C.BOLD}🍅 Focus Timer{C.RESET}\n")
    print(f"  {C.GREEN}{WORK_MINUTES}min work{C.RESET}  ·  "
          f"{C.CYAN}{SHORT_BREAK_MINUTES}min short break{C.RESET}  ·  "
          f"{C.MAGENTA}{LONG_BREAK_MINUTES}min long break{C.RESET} (every {SESSIONS_BEFORE_LONG} sessions)\n")
    print(f"  {C.DIM}All-time sessions: {stats['total_sessions']}  ·  "
          f"Today: {stats['today']['sessions']}{C.RESET}\n")
    prompt_continue("Ready to focus?")

    hide_cursor()
    try:
        while True:
            session_num += 1

            # Work phase
            run_phase("🔴  FOCUS", WORK_MINUTES, session_num, stats, C.RED)
            record_session(stats, WORK_MINUTES)
            beep(3)
            show_summary(stats)

            # Break phase
            if session_num % SESSIONS_BEFORE_LONG == 0:
                prompt_continue(f"🎉 {SESSIONS_BEFORE_LONG} sessions done! Take a long break ({LONG_BREAK_MINUTES} min).")
                hide_cursor()
                run_phase("🟢  LONG BREAK", LONG_BREAK_MINUTES, session_num, stats, C.GREEN)
            else:
                prompt_continue(f"✅ Nice work! Take a short break ({SHORT_BREAK_MINUTES} min).")
                hide_cursor()
                run_phase("🔵  SHORT BREAK", SHORT_BREAK_MINUTES, session_num, stats, C.CYAN)

            beep(2)
            prompt_continue("Break over — ready for another session?")
            hide_cursor()

    except KeyboardInterrupt:
        show_cursor()
        print(f"\n  {C.YELLOW}See you next time!{C.RESET}\n")


if __name__ == "__main__":
    main()
