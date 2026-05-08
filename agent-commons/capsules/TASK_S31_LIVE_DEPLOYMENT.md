# 任務膠囊：[S31-LIVE] 小額實盤首單試車 (GO LIVE!) 💰

## 1. 任務目標 (Goal)
在實盤環境下，使用真實 USDT 進行首筆小額成交測試（5-10 USDT, 1x 槓桿），驗證全鏈路（下單、冪等、對帳、時鐘、風控）在真實交易所環境下的運作正確性。

## 2. 實作清單 (Implementation List)

### 階段一：[Setup & Environment] - 工程師與使用者協作
- [ ] **[Setup]** 金鑰注入防護 (IRON §②)：由工程師建立 `src/CryptoBot.ConsoleApp/appsettings.Local.json` 模板，並指示使用者填入 API Key。
- [ ] **[Setup]** 環境切換：工程師修改 `appsettings.json` 將 `TradingMode` 設為 `Live`，`UseDemoTrading` 設為 `false`。
- [ ] **[User-Local]** 時鐘預檢 (Step 0)：使用者執行 `dotnet run --project ../CryptoBot.DiagnosticTool -- check-skew`。
- [ ] **[Verification]** VCP-1 判定：偏差絕對值必須 < 500ms（使用者回報 2026-04-26 已校時，待實證 log 閉環）。

### 階段二：[Live Diagnostic] - 使用者執行
- [ ] **[User-Local]** 實盤連通性預檢：執行 `env` 指令驗證金鑰有效性與 USDT 餘額 (需 > 20 USDT)。
- [ ] **[User-Local]** 實盤精度探針：執行 `sizing --symbol BTC-USDT --entry <Price>` 取得實務 StepSize 與 MinNotional。

### 階段三：[Execution & Verification] - 閉環驗收
- [ ] **[User-Local]** 啟動實盤下單：執行 `ConsoleApp` 或 `DiagnosticTool` 模擬下單指令。
- [ ] **[Verification]** 訂單生命週期追蹤：由工程師判讀 log，確認 TraceId 正確產生並透傳。
- [ ] **[Verification]** 對帳回歸：觀察 `OrderReconciliationService` 是否完成 `New -> Filled` 同步。

## 3. 驗收檢核點 (VCP)
- **VCP-0 (Authorization)**: 使用者必須在此對話中明確輸入「**我已確認時鐘與金鑰安全，授權執行實盤首單測試**」。
- **VCP-1 (Environment)**: `check-skew` 偏差絕對值 < 500ms。
- **VCP-2 (Balance)**: `env` 顯示 USDT 餘額足以支付首單 (5-10 USDT)。
- **VCP-3 (Execution)**: 成功下達一張訂單，且本地 DB 狀態同步為 `Filled`。
- **VCP-4 (TraceId)**: `check-order` 顯示 TraceId 與 ClientOrderId 對齊，且無重複下單異常。

## 4. 交付要求 (Deliverables)
- [ ] `Institutional_Memory.md` 更新：紀錄實盤 `errorCode: 101400` 是否與 Demo 一致。
- [ ] `HANDOFF_20.md`：紀錄 Milestone 10 (Go Live) 成果。

---
## 5. 驗證反饋紀錄 (History)
- 2026-04-26: 工程師因 IRON §② 風險、指令缺失與邊界模糊執行退稿。
- 2026-04-26: PM 完成膠囊修訂，補齊金鑰路徑、時鐘預檢與角色分工。
