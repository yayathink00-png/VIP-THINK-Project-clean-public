#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path


FB_DIR = Path(os.getenv("FB_BROADCAST_WORKDIR", Path(__file__).resolve().parent))
LOG_DIR = FB_DIR / "outputs" / "fb_daily_logs"
ACCOUNTS = "act_468253789344241,act_366864216464093,act_442457935507062,act_1158469106256042,act_627543006449377,act_2107766700052928"
ACCOUNT_ALIASES = "7,8,9,27,18,23"
COMMAND_TIMEOUT_SECONDS = int(os.getenv("FB_BROADCAST_COMMAND_TIMEOUT_SECONDS", "1800"))


def main() -> int:
    since, until = target_window(date.today())
    since_day = since.isoformat()
    until_day = until.isoformat()
    window_label = since_day if since_day == until_day else f"{since_day}_to_{until_day}"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"fb_new_creative_broadcast_{window_label}.log"
    preview_path = LOG_DIR / f"fb_new_creative_broadcast_{window_label}.txt"

    commands = [
        [
            sys.executable,
            "fb_new_creative_broadcast.py",
            "--since",
            since_day,
            "--until",
            until_day,
            "--accounts",
            ACCOUNTS,
            "--skip-insights",
        ],
    ]

    robot_cmd = [
        sys.executable,
        "fb_robot_broadcast.py",
        "--since",
        since_day,
        "--until",
        until_day,
        "--account-aliases",
        ACCOUNT_ALIASES,
        "--material-lookback-days",
        "7",
        "--max-lines",
        "0",
    ]
    if force_dry_run() or not has_webhook(FB_DIR / ".env"):
        robot_cmd.append("--dry-run")
    commands.append(robot_cmd)

    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"FB new creative daily broadcast for {since_day} to {until_day}\n\n")
        for cmd in commands:
            log.write("$ " + " ".join(cmd) + "\n")
            log.flush()
            try:
                result = subprocess.run(
                    cmd,
                    cwd=FB_DIR,
                    text=True,
                    capture_output=True,
                    timeout=COMMAND_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as exc:
                if exc.stdout:
                    log.write(str(exc.stdout))
                if exc.stderr:
                    log.write("\n[stderr]\n" + str(exc.stderr))
                log.write(
                    f"\n[timeout] command exceeded {COMMAND_TIMEOUT_SECONDS} seconds\n\n"
                )
                return 124
            if result.stdout:
                log.write(result.stdout)
                if cmd[1] == "fb_robot_broadcast.py":
                    preview_path.write_text(result.stdout, encoding="utf-8")
            if result.stderr:
                log.write("\n[stderr]\n" + result.stderr)
            log.write(f"\n[exit] {result.returncode}\n\n")
            if result.returncode != 0:
                return result.returncode

    print(f"[OK] since={since_day}")
    print(f"[OK] until={until_day}")
    print(f"[OK] log={log_path}")
    if preview_path.exists():
        print(f"[OK] preview={preview_path}")
    return 0


def target_window(today: date) -> tuple[date, date]:
    if today.weekday() == 0:
        return today - timedelta(days=3), today - timedelta(days=1)
    yesterday = today - timedelta(days=1)
    return yesterday, yesterday


def has_webhook(env_path: Path) -> bool:
    if not env_path.exists():
        return False
    for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "FB_BROADCAST_WEBHOOK_URL" and value.strip().strip('"').strip("'"):
            return True
    return bool(os.getenv("FB_BROADCAST_WEBHOOK_URL", "").strip())


def force_dry_run() -> bool:
    return os.getenv("FB_BROADCAST_FORCE_DRY_RUN", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }


if __name__ == "__main__":
    raise SystemExit(main())
