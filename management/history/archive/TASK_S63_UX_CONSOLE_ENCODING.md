# 任務膠囊：[S63-UX] 診斷工具中文亂碼修復

## 🎯 任務目標
解決 `CryptoBot.DiagnosticTool` 在 Windows 終端機執行時產生中文亂碼的問題，確保所有診斷資訊與警告能清晰顯示。

## 📋 實作清單

### T1. 強制設定 Console 輸出編碼
- [ ] **編碼設定**：在 `src/CryptoBot.DiagnosticTool/Program.cs` 的 `Main` 方法最開頭，加入 `Console.OutputEncoding = System.Text.Encoding.UTF8;`，強制將終端機輸出設為 UTF-8。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Encoding]**：執行 `dotnet run --project ../CryptoBot.DiagnosticTool -- s63_check-mtf BTC-USDT`，終端機不再出現亂碼，能正確顯示中文字元（如「落在」與「進行中」）。

## 📤 交付要求
- 完成後回報「診斷工具中文亂碼修復完畢」。
