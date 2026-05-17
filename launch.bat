@echo off
REM CryptoBot 一鍵啟動 — Windows 雙擊或 cmd 跑此 .bat
REM 兩個 service 同時啟動: ai_ops/sidecar (uvicorn:5301) + CryptoBot.ConsoleApp (Blazor:5001)
REM Ctrl+C 一起終止
cd /d %~dp0
python launch.py
pause
