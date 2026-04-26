# 任務膠囊：[S27-HOTFIX] start-ngrok.ps1 語法與編碼修正

## 🎯 任務目標
修正 `scripts/start-ngrok.ps1` 因編碼錯誤導致的語法崩潰（Missing Terminator），並確保腳本能正常執行。

## 🛠️ 修正要點
1. **移除亂碼**：將所有中文字元改為英文，避免編碼不相容問題。
2. **語法補全**：修復字串未閉合（L34）與程式碼區塊未閉合（L25）的問題。
3. **編碼格式**：建議以 UTF-8 無 BOM 格式存檔。

## 📋 修正後的程式碼內容 (請直接替換全檔)
```powershell
$ErrorActionPreference = 'Stop'
$port = 5000

# Check if ngrok is installed
$ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
if ($null -eq $ngrok) {
    Write-Host "X ngrok not found. Please install it first:" -ForegroundColor Red
    Write-Host "  winget install Ngrok.Ngrok" -ForegroundColor Yellow
    exit 1
}

# Check if CryptoBot is listening on port 5000
$listening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($null -eq $listening) {
    Write-Host "! Service on port $port is not running." -ForegroundColor Yellow
    Write-Host "  Please run: dotnet run --project src/CryptoBot.ConsoleApp"
    $continue = Read-Host "Start ngrok anyway? (y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') { exit 1 }
}

Write-Host "-> Starting ngrok tunnel for http://localhost:$port" -ForegroundColor Cyan
Write-Host "   (ngrok Dashboard: http://127.0.0.1:4040)" -ForegroundColor DarkGray
Write-Host ""

ngrok http $port
```

## ✅ 驗證檢核點 (VCP)
- [ ] **[VCP-Syntax]**：執行 `powershell -Command "Get-Content scripts/start-ngrok.ps1 | Out-Null"` 不應有報錯。
- [ ] **[VCP-Run]**：直接執行 `.\scripts\start-ngrok.ps1` 應能正確顯示歡迎文字並啟動 ngrok。
