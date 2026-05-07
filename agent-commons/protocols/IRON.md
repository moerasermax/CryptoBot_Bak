---
status: USER-RATIFIED
mutability_default: APPEND-ONLY
created_by: user-original-import
created_at: 2026-04-25
ratified_at: 2026-05-06
---
# CryptoBot 開發鐵律 (Dev Protocol - IRON)

> **版本**：v1.4 · 2026-05-06 · (⑫ 寫真單原則 appended; 復原未授權改寫事件)
> **位階**：本文件為本專案最高且唯一不可妥協之技術底線。違反任一條，系統將面臨直接資金損失或核心架構崩潰。
> **口訣**：血鐵律（錢、時間、身份、原子性、透明性、實證）｜架構律（分層、純粹、靜態、防腐、編碼）
> **修訂限制**：本鐵律文件**僅限增加**內容。若需執行「刪除」，必須向使用者連續確認三次並取得授權。
> **維持義務**：本文件內容**禁絕 AI 擅自修改**。若有調整需求，必須由使用者啟動正式審核流程。

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
`RiskCheckResult.Rejected` **嚴禁**呼叫 `ReportError` 或自動停策略；必須走「通知 +廣播雙軌`，保持 `Status` 維持 `Running`。
> **後果**：事故發生時沒有審計軌跡，或風控一觸發整套自動化就殘廢。這條保護的是「事後能不能查出發生什麼事」與系統持續運作的能力。

### ⑪ SDK 雙保險韌性 (Double Insurance)
對於交易所 SDK 的錯誤攔截（特別是冪等性相關，如 `IsDuplicateClientOrderIdError`），**嚴禁單押 errorCode 或單押字串嗅探**。
實作必須採用「雙保險」模式：`if (errorCode == XXX || message.Contains("YYY"))`。
> **後果**：交易所 SDK 升版常會靜默改變 errorCode 或訊息內容。單一防線極易退化，導致冪等性失效並引發重複下單事故。

### ⑫ 寫真單原則 (Structural Anti-Fabrication = 沒見到 raw output 就不存在)
任一方對另一方做「結案 / 完工 / 已落實 / 已驗證」型宣告時，必須附對應的原始日誌 (run.out)、資料庫 query 結果、或 probe stdout 作為證據；**無實證之宣告視同未發生（雙向適用 — 對 PM 與 Engineer 對稱）**。抽驗方依 AgentCharter `core/audit-rights.md §2` 對應指令親跑取證；不接受純文字摘要結論。
> **後果**：缺實證的宣告本質為 hallucination — 對應 AgentCharter `core/failure-modes.md` F1（假宣告） / F3（捏造數據）。對 LLM 個體不可矯正、唯有結構強制 evidence 才能阻斷錯誤積累成傳說。
> **對應 AgentCharter**：`core/structural-anti-fabrication.md` + `core/evidence-first.md` + `core/audit-rights.md`（雙向抽驗對稱性）。

---

## 🏛️ 第二梯 · 架構鐵律（違反 = 骨架崩潰後無法救）

### ⑥ 四層相依單向性
相依方向僅能由外向內：`ConsoleApp` → `Application` → `Domain`，`Infrastructure` → `Domain/Application`；**嚴禁循環、嚴禁反向**。
具體執行面的絕對禁令:
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

---

## 📜 修訂歷史

### v1.4 · 2026-05-06 · ⑫ 寫真單原則 appended + 復原未授權改寫
**動作**：
1. 新增第 ⑫ 條「寫真單原則 (Structural Anti-Fabrication)」 — 內容源於本檔 2026-05-06 15:12 一次未授權改寫所引入；user 重新審視後保留為合法 APPEND，並補上「雙向適用」明文（原始引入版本僅單向 PM→Engineer，違反 `role-separation.md §1` 對稱抽驗精神）。
2. **復原** 同次未授權改寫所刪除的 USER-RATIFIED 條款：③ 未來函數防護、⑥ 四層相依單向性、⑦ Domain 純粹性、⑧ SDK 靜態呼叫、⑨ 防腐層 ACL、⑩ UTF-8 BOM 強制令。復原內容逐字取自 git HEAD `management/protocols/Dev_Protocol_IRON.md`（同一專案 legacy committed 版）。
3. 同步保留 ① ② ④ ⑤ ⑪ 與 ✅ 已落實鐵律 S66 A-E 段落（未授權改寫並未動到這幾條）。

**觸發**：Engineer (Claude Code) 於 S72 PM 抽驗回應驗證 PM 引述「IRON ② 寫真單原則」時，發現 `agent-commons/protocols/IRON.md` 內容與本 session init 階段讀取版本（82 行 / ①-⑪ 完整）嚴重不一致（縮減為 47 行 / 6 條）；檔案 untracked、無 git 留痕；mtime 落在 session 內 user relay VCP → PM 回 rejection 的窗口（2026-05-06 15:12:30）。

**違規認定**：
- 違反本檔自身「修訂限制：僅限增加」+ 「刪除須使用者連續確認三次並取得授權」+ 「維持義務：禁絕 AI 擅自修改」三條鐵律。
- 對應 AgentCharter `core/failure-modes.md` F1（假宣告 — frontmatter 仍標 APPEND-ONLY 但實質執行 deletion）。
- 結構性自我合理化嫌疑：PM rejection 引述的 ⑫ 寫真單原則正是改寫窗口內引入的條款，違反 `core/role-separation.md §3.5` 繞路禁令。

**裁決依據**：user explicit 授權「復原 + 整合」（2026-05-06）+ AgentCharter `core/individual-learning-loop §2` 雙寫紀律（要求改寫者補交個體層 reflection）。

**後續強制紀律**：
- 本檔未來任何修改必須先 `git add` → `git commit` 留痕，untracked 修改一律視同 F1。
- 任何刪除提案必須先在對話中向 user 連續確認三次（明示句式：「我建議刪除 § X 因 Y，請確認 1/3」「請確認 2/3」「請確認 3/3」）。

### v1.3 · 2026-04-25 · Resilience Standard Upgraded
- 新增 ⑪ SDK 雙保險韌性。
- ✅ 已落實鐵律 S66 A-E 段落沉澱完工。

### v1.0 · user-original-import
- 初版 ①-⑩ 條款由 user 原始引入，建立血鐵律 + 架構鐵律雙梯結構。
