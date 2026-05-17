#!/usr/bin/env python3
"""
CryptoBot 一鍵啟動 — ai_ops/sidecar (Bayesian Optuna) + CryptoBot ConsoleApp (Blazor + Strategy Runtime)

用法:
    python launch.py
    或雙擊 launch.bat

兩個 service 並行啟動:
  1. ai_ops/sidecar uvicorn on 127.0.0.1:5301  (Bayesian Optimization sidecar)
  2. CryptoBot.ConsoleApp on http://localhost:5001  (Blazor Server + 交易 Strategy Runtime)

Ctrl+C 一起終止兩 process (graceful → force kill fallback)。
任一 service 提前退出 → 自動關閉另一個 + 退出本 launcher。
"""

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SIDECAR_DIR = ROOT / "ai_ops" / "sidecar"
CONSOLEAPP_DIR = ROOT / "CryptoBot" / "src" / "CryptoBot.ConsoleApp"

processes: list[tuple[str, subprocess.Popen]] = []
stopping = False


def prefix_output(proc: subprocess.Popen, label: str) -> None:
    """讀 process stdout 加 prefix 印到本 launcher stdout (跨 process log multiplexing)."""
    try:
        if proc.stdout is None:
            return
        for line_bytes in iter(proc.stdout.readline, b""):
            if stopping:
                break
            line = line_bytes.decode("utf-8", errors="replace").rstrip()
            if line:
                print(f"[{label}] {line}", flush=True)
    except Exception as ex:
        print(f"[LAUNCH] prefix_output error for {label}: {ex}", flush=True)


def start_sidecar() -> subprocess.Popen:
    print("[LAUNCH] Starting ai_ops/sidecar uvicorn on 127.0.0.1:5301 ...", flush=True)
    if not (SIDECAR_DIR / "app.py").exists():
        print(f"[LAUNCH] ERROR: {SIDECAR_DIR / 'app.py'} not found.", flush=True)
        sys.exit(1)
    proc = subprocess.Popen(
        ["uvicorn", "app:app", "--host", "127.0.0.1", "--port", "5301"],
        cwd=str(SIDECAR_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        shell=False,
    )
    processes.append(("SIDECAR", proc))
    threading.Thread(target=prefix_output, args=(proc, "SIDECAR"), daemon=True).start()
    return proc


def start_consoleapp() -> subprocess.Popen:
    print("[LAUNCH] Starting CryptoBot.ConsoleApp (dotnet run, Blazor + Strategy Runtime) ...", flush=True)
    if not (CONSOLEAPP_DIR / "CryptoBot.ConsoleApp.csproj").exists():
        print(f"[LAUNCH] ERROR: {CONSOLEAPP_DIR / 'CryptoBot.ConsoleApp.csproj'} not found.", flush=True)
        sys.exit(1)
    proc = subprocess.Popen(
        ["dotnet", "run", "-c", "Debug"],
        cwd=str(CONSOLEAPP_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        shell=False,
    )
    processes.append(("CRYPTOBOT", proc))
    threading.Thread(target=prefix_output, args=(proc, "CRYPTOBOT"), daemon=True).start()
    return proc


def stop_all(signum=None, frame=None) -> None:  # noqa: ARG001
    global stopping
    if stopping:
        return
    stopping = True
    print("\n[LAUNCH] Stopping all processes ...", flush=True)
    for label, proc in processes:
        try:
            if proc.poll() is None:
                print(f"[LAUNCH] Terminating {label} (PID {proc.pid}) ...", flush=True)
                proc.terminate()
        except Exception as ex:
            print(f"[LAUNCH] Error terminating {label}: {ex}", flush=True)
    # graceful exit 等 5s, 否則 force kill
    for label, proc in processes:
        try:
            proc.wait(timeout=5)
            print(f"[LAUNCH] {label} exited (code {proc.returncode}).", flush=True)
        except subprocess.TimeoutExpired:
            print(f"[LAUNCH] {label} not exiting in 5s, force kill ...", flush=True)
            try:
                proc.kill()
            except Exception:
                pass
    print("[LAUNCH] All processes stopped. Bye.", flush=True)
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, stop_all)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop_all)

    print("=" * 60)
    print("  CryptoBot 一鍵啟動")
    print("=" * 60)
    print(f"  Root      : {ROOT}")
    print(f"  Sidecar   : {SIDECAR_DIR} (uvicorn:5301)")
    print(f"  ConsoleApp: {CONSOLEAPP_DIR} (Blazor:5001)")
    print("=" * 60)

    start_sidecar()
    time.sleep(2)  # 給 uvicorn 起來
    start_consoleapp()

    print("[LAUNCH] Both services started. Ctrl+C to stop both.", flush=True)
    print("[LAUNCH] Sidecar docs: http://127.0.0.1:5301/docs", flush=True)
    print("[LAUNCH] CryptoBot UI: http://localhost:5001", flush=True)
    print("-" * 60, flush=True)

    # 監視: 任一 process 退出則一起關
    try:
        while not stopping:
            for label, proc in processes:
                rc = proc.poll()
                if rc is not None:
                    print(f"[LAUNCH] {label} exited with code {rc}, stopping all.", flush=True)
                    stop_all()
                    return
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all()


if __name__ == "__main__":
    main()
