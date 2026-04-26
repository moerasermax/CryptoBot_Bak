# CryptoBot 開發鐵律 (Dev Protocol - IRON)

> **版本**：v1.3 · 2026-04-25 · (Resilience Standard Upgraded)
> **位階**：本文件為本專案最高且唯一不可妥協之技術底線。違反任一條，系統將面臨直接資金損失或核心架構崩潰。
> **口訣**：血鐵律（錢、時間、身份、原子性、透明性）｜架構律（分層、純粹、靜態、防腐、編碼）
> **修訂限制**：本鐵律文件**僅限增加**內容。若需執行「刪除」，必須向使用者連續確認三次並取得授權。

---

## 🛑 第一梯 · 血鐵律（違反 = 直接燒錢或汙染系統真相）

### ① 精度絕對論（L1）
**計算面**：策略邏輯與資金管理**嚴禁**使用 `double/float`，一律使用 `decimal`。
**解析面**：解析 SDK 規則時，必須分清「精度位數 (Precision)」與「步進值 (StepSize)」。`StepSize` 為整數時視為異常，須 fallback 讀 `Precision` 轉 `10^(-n)`（詳見 `Institutional_Memory` §2）。
> **後果**：違反結果不是 Bug，是帳目永遠對不上、下單量直接被拒。浮點誤差在金融領域沒有「可接受公差」。

### ② 金鑰唯一路徑
金鑰獲取只能走 `IExchangeCredentialProvider`；**嚴禁**硬編碼、禁落日誌、禁落 Git。
> **後果**：一旦外洩就是公開事故，無例外條款。

### ③ 未來函數防護（切尾 + MTF 動態對齊 / L2）
執行引擎必須實作 `TrimInProgressTail`；多週期對齊必須用 `interval.ToTimeSpan()` 動態推算，**禁寫死偏移**。
> **後果**：違反會讓回測永遠亮眼、實盤永遠虧——這是金融系統最安靜的殺手。

### ④ 原子轉換協議（S45 / S52）
策略更換 (Morph) 必走「停-換-起 (Stop-Change-Start)」；所有啟動動作必須受 `_mutateLock` 保護。
> **後果**：違反 = 殭屍 Executor、同一倉位被雙開、重複下單。每一個都是直接損失。

### ⑤ 風控透明化（S56 / S59）
風控攔截或下單量修正**禁靜默失敗**，必須使用 `[RISK]` 或 `[SIZE]` 前綴廣播原因。
`RiskCheckResult.Rejected` **嚴禁**呼叫 `ReportError` 或自動停策略；必須走「通知 +廣播雙軌」，保持 `Status` 維持 `Running`。
> **後果**：事故發生時沒有審計軌跡，或風控一觸發整套自動化就殘廢。這條保護的是「事後能不能查出發生什麼事」與系統持續運作的能力。

### ⑪ SDK 雙保險韌性 (Double Insurance)
對於交易所 SDK 的錯誤攔截（特別是冪等性相關，如 `IsDuplicateClientOrderIdError`），**嚴禁單押 errorCode 或單押字串嗅探**。
實作必須採用「雙保險」模式：`if (errorCode == XXX || message.Contains("YYY"))`。
> **後果**：交易所 SDK 升版常會靜默改變 errorCode 或訊息內容。單一防線極易退化，導致冪等性失效並引發重複下單事故。

---

## 🏛️ 第二梯 · 架構鐵律（違反 = 骨架崩潰後無法救）

### ⑥ 四層相依單向性
相依方向僅能由外向內：`ConsoleApp` → `Application` → `Domain`，`Infrastructure` → `Domain/Application`；**嚴禁循環、嚴禁反向**。
具體執行面的絕對禁令：
- **防範抽象洩漏**：外部型別一律封裝在 `Infrastructure`；跨層傳遞只能使用 `Domain` 定義的型別或 `Application` 介面。
- `Domain` 禁 `using Microsoft.EntityFrameworkCore.*` / `BingX.Net.*` / `Microsoft.AspNetCore.*`
- `Application` 禁 `new EntityFrameworkXxx()` / `new BingXClient()`
- `Infrastructure` 禁把 EF / BingX 型別洩漏回 `Application` 簽章

### ⑦ Domain 純粹性
`Domain` 層禁 IO、禁通知、禁資料庫。**禁 `DateTime.UtcNow` / `Guid.NewGuid()`，包含 ctor 預設值在內**。時間與 ID 一律由建構子參數注入，或透過 `IClock` / `IIdGenerator` 取得。
> **後果**：Domain 測試非確定、無法重放、回測失真。

### ⑧ SDK 靜態呼叫（L4）
**嚴禁**用 `dynamic` 呼叫交易所 SDK 方法，一律採靜態型別。
> **後果**：被 BingX internal 類別封鎖的血淚教訓，違反會在 runtime 爆掉，且 SDK 改版會無聲改變行為。

### ⑨ 防腐層（ACL）
外部 SDK 的 DTO **嚴禁**滲透進 `Domain` / `Application`；必須經 `Infrastructure` 層翻譯。
> **後果**：未來換交易所（如 OKX / Bybit）時整層拆到天亮。

### ⑩ UTF-8 BOM 強制令（L3）
含中文字串的 `.cs` 檔**必須**加上 UTF-8 BOM。
> **後果**：Windows 環境編譯期字串腐蝕，日誌變亂碼、指令比對錯誤，讓操作者在事故現場看不懂系統在說什麼。

---

## ✅ 已落實鐵律 · 運維韌性（S66 A-E 完成 2026-04-25）
- ClientOrderId 冪等規約 ✅ S66-A（含 T0 探針 errorCode=101400 雙保險）
- 交易所狀態對帳（Reconciliation）✅ S66-B（OrderReconciliationService + persistence mismatch 偵測器）
- 結構化日誌 + Trace ID ✅ S66-C（Order.TraceId + BeginScope + Serilog Enrich.FromLogContext）
- NTP 時鐘漂移防護 ✅ S66-D（NtpDriftMonitor + IClockSkewState + RiskManager 攔截 1000ms）
- 啟動期 Pre-flight Check ✅ S66-E（StartupSkewCheck + ASCII Banner + Abort 攔截）
