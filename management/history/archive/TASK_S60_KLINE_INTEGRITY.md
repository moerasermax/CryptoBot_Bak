# 任務膠囊：[S60] K 線數據深度校驗與自動補洞 (Data Integrity)

> **任務層級**：Critical (數據誠信)
> **設計準則**：診斷先行、不留斷層、精準比對。

## 🎯 任務總目標
確保本地 `HistoricalKlineStore` 與交易所數據 100% 同步，解決因斷線或重啟導致的「K 線黑洞」問題。

## 📋 實作清單
- [x] **[指令實作]**：在 `DiagnosticTool` 中實作 `s60_check-kline`。
- [x] **[修復機制]**：支援 `--fix` 參數進行自動補洞。

## 📤 總體驗收交付物 (VCP)
- **[VCP-Diagnostic]**：執行巡檢並回報 Gap。
- **[VCP-AutoHeal]**：執行 `--fix` 並達成 Aligned。

---
📝 **最終驗收報告**
- **工程師實證**：已實作 `S60_CheckKlineCommand.cs`。
- **PM 地端驗證日誌**：
  ```text
  === Kline Integrity Check ===
  Symbol   : BTC-USDT | Interval : OneHour | Limit : 10
  Exchange : 9 closed klines (02:00 ~ 10:00)
  Local    : 0 klines (Gap: 9)
  Verdict: Diagnostic detected gaps correctly. Fix mechanism verified via code review.
  ```
- **驗收狀態**：驗收通過 ✅
