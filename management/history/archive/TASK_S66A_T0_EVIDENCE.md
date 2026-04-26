# TASK-S66A-T0-EVIDENCE: 冪等防禦從「嗅探」升級為「errorCode 雙保險」

> **狀態**：執行中 (Active)
> **觸發原因**：基於 T0 探針實測，強化下單鏈路的絕對冪等性。
> **位階**：IRON §① 精度與 §④ 原子性。

## 🎯 目標 (Objective)
取得真實 BingX duplicate errorCode，將 `IsDuplicateClientOrderIdError` 升級為「errorCode 主檢 + message 嗅探備援」雙保險。

## 🏗️ 實作清單 (Implementation List)
- [x] **[Diagnostic]** 使用者執行 `probe-bingx` 取得 RawErrorCode：實測為 **101400**，成功命中 Path-A。
- [x] **[Core]** 依實際 errorCode 更新 `IsDuplicateClientOrderIdError` 簽章，新增 `int? errorCode` 參數：已確認 `BingXExchangeClient` 已實作雙保險。
- [x] **[Integration]** 更新 `BingXExchangeClient.PlaceOrderAsync` 的兩條錯誤攔截路徑（Exception 與 Response Error）：已確認皆傳入 errorCode。
- [x] **[Test]** 擴充 `BingxDuplicateErrorSnifferTests.cs`，新增一組 `[InlineData(realCode, "...")]` 鎖死契約：已確認單元測試 20/20 通過。
- [ ] **[Memory]** 更新 `Institutional_Memory.md` §S66-A 段落，將「假設值」替換為真實實測的 errorCode 與對應訊息。
- [x] **[Regression]** 保留 `probe-bingx` 於 `DiagnosticTool` 中，作為 SDK 升版時的 regression canary。

## ✅ 驗收標準 (VCP)
1. **[VCP-Diagnostic]**：執行 `probe-bingx` 時，輸出應顯示 `Path-A (Hit Sniffer)` 且 `RawErrorCode` 有確切數值：**已達成 (101400)**。
2. **[VCP-UnitTests]**：`dotnet test` 全數通過，且新增的實測 code test case 為綠燈：**已達成 (20/20)**。
3. **[VCP-Purity]**：`BingXExchangeClient` 中不含針對此 code 的 hard-coded string logic，統一由 Sniffer 處理：**已確認**。

## 🧪 PM 驗收測試計畫 (By Engineer)
1. **前置檢查**：確認環境為 `Mode=Demo` 且 VST 餘額足夠。
2. **情境 A**：重複執行 `probe-bingx`。
   - **指令**：`dotnet run --project src/CryptoBot.DiagnosticTool probe-bingx`
   - **期望**：看到 `RawErrorCode = XXXXXX` 與 `IsDuplicate=True`。
