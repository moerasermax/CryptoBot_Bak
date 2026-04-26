# TASK-S66-B: 交易所狀態對帳 (Reconciliation) 🔄

> **狀態**：已完成 (Completed) ✅
> **完成日期**：2026-04-25
> **觸發原因**：解決下單管線中因網路中斷或程序崩潰產生的「殭屍單/幽靈單」，確保本地與交易所狀態最終一致。
> **位階**：IRON §④ 原子轉換協議 與 §⑤ 風控透明化。

---

## 📌 現狀分析 (Research Findings)

1.  **下單管線 (S66-A T1.5)**：`StrategyExecutor.cs` 採用「DB Pending First」模式。
    - **時序**：`AddAsync(Order with Status.New)` → `UnitOfWork.Save` → `PlaceOrderAsync` (呼叫交易所)。
    - **風險點**：若 `PlaceOrderAsync`執行前系統崩潰，DB 會留下一筆 `ExchangeOrderId == null` 的孤兒訂單。
2.  **識別邏輯**：`SyncOrdersCommand.cs` 已定義此類訂單為 `pending-assign`。這是對帳巡檢的首要標的。
3.  **技術基礎**：`IExchangeClient` 已具備 `GetOrderByClientOrderIdAsync`，可透過冪等 ID 進行跨系統查詢。

---

## 🏗️ 實作清單 (Implementation List)

- [x] **[Application]** 於 `CryptoBot.Application/Synchronization/` 實作 `OrderReconciliationService`。
- [x] **[Core]** 核心邏輯需嚴格遵守上述 **情境 A/B** 的時間閾值，避免誤殺正常下單流程。
- [x] **[Integration]** 於 `ConsoleApp` 的 `Program.cs` 註冊為 `AddHostedService`。
- [x] **[Log]** 任何狀態變更必須帶有 `[RECONCILIATION]` 前綴，並記錄變更前後的狀態差異。

---

## ✅ 驗收紀錄 (Verification Record)

### 📊 實測診斷證據 (Evidence)
- **環境**：Mode=Demo (VST), SQLite, Guid-based ID.
- **關鍵發現**：**SQLite 中的 Guid 大小寫敏感衝突**。
    - **現象**：PM 使用 `randomblob` 注入的小寫 Guid 導致 EF Core `UPDATE` 語句找不到列，引發 `DbUpdateConcurrencyException`。
    - **對策**：實證了 SQLite 環境下手動注入 Guid 必須大寫一致（EF Core 預設將 Guid 序列化為 UPPERCASE TEXT，SQLite TEXT 比對大小寫敏感）。
    - **Repository 狀態**：`OrderRepository.UpdateAsync` 維持 S53 T3 原始實作不動 —— 第一輪 hotfix 嘗試的「強制 Modified」分支已回退；ChangeTracker 在原始實作下工作正常。

### 🧪 歷史驗收 Log
- **2026-04-25 12:57**：[失敗] `DB persistence mismatch! changed=2 but SaveChanges affected 0 rows.` 揭露持久化失效。
- **2026-04-25 13:13**：[失敗] `DbUpdateConcurrencyException` 揭露 Guid 比對失敗。
- **2026-04-25 13:27**：[成功] `tick complete: 1/6 orders updated, 1 rows persisted.` (使用大寫 Guid + 原始 Repo)。

---
_「對帳不是為了糾錯，而是為了確保系統與真實世界的最終一致性。」_
