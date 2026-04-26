# TASK-S66-B-HOTFIX: 對帳變更持久化修復 🔧

> **狀態**：已完成 (Completed) ✅
> **完成日期**：2026-04-25
> **位階**：IRON §④ 原子轉換協議 與 §⑤ 透明性。

## 🏗️ 實作清單 (Implementation List)

- [x] **[Core]** 修改 `src/CryptoBot.Application/Synchronization/OrderReconciliationService.cs`：補上 `UpdateAsync` 呼叫。
- [x] **[Infrastructure]** 嘗試修改 `OrderRepository.UpdateAsync`：強制標記為 `Modified`（**已回退**，證實為 Guid 大小寫問題）。
- [x] **[Log]** 補上 `DB persistence mismatch!` 偵測警示，強化背景服務的透明度。

## ✅ 驗收紀錄 (Verification Record)

1.  **[VCP-Persistence]**：執行「人造孤兒單注入測試」。
    - **結果**：修正 Guid 為大寫後，日誌出現 `1 rows persisted`，資料成功落地。
2.  **[VCP-Diagnosis]**：證實 `DB persistence mismatch!` 警示能有效捕捉 EF 追蹤失效的邊角案例（本次成功導向 Guid 格式診斷）。
3.  **[VCP-Integrity]**：重啟後系統能正確識別已 Reject 訂單，不予重複處理。

### 🧪 歷史驗收 Log
- **12:57**：發現 DB 不落地。
- **13:13**：嘗試 `force Modified` 卻噴 `DbUpdateConcurrencyException`。
- **13:25**：回退 `force Modified` 並改用大寫 Guid -> **全綠**。

---
_「當 ChangeTracker 沉默時，代碼必須顯式地發聲。」_
