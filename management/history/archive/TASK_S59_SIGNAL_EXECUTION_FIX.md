# 任務膠囊：[S59-DIAG] 信號執行脫節修復與診斷工具建立

## 🎯 任務目標
解決使用者發現的「有信號、無下單」且「無任何報錯反饋」之現象。將執行層從「靜默失敗」轉為「顯性化警告」，並建立一套專供 PM (Gemini) 使用的環境診斷工具。

## 📋 首席工程師實作清單 (Chief Engineer)

### T1. 執行層透明化修復 (StrategyExecutor)
- [ ] **中斷檢查點顯性化**：修改 `StrategyExecutor.HandleSignalAsync`。
- [ ] **餘額檢核回報**：當 `OrderSizer` 返回數量為 0 時，嚴禁靜默 `return`。必須呼叫 `BroadcastStrategyEvaluationFailedAsync` 並帶上 `[SIZE] 餘額不足以支付最小下單量`。
- [ ] **風控攔截連動**：確保所有 `RiskManager` 的拒絕結果（Rejected）都必須透過 `[RISK]` 前綴廣播至 Dashboard，讓使用者能分辨「攔截」與「故障」。

### T2. 建立 Gemini 診斷工具 (Diagnostic Tooling)
- [ ] **獨立專案**：在 `src/` 下新增 `CryptoBot.DiagnosticTool` (Console App)，並加入方案。
- [ ] **API 透視功能**：讀取當前配置，連線並輸出：
    - 當前 API 模式 (Demo/Live)。
    - 真實資產餘額 (VST/USDT)。
    - API 權限狀態 (Trading Enabled?)。
- [ ] **下單量模擬器**：
    - 提供 CLI 入參，讓 PM 能模擬輸入「價格」與「策略名稱」。
    - 輸出完整的計算鏈：`Balance -> Risk Ratio -> Leverage -> Notional Value -> Final Qty`。
    - 標示是否觸發 `RiskManager` 攔截。

## ✅ 驗證檢核點 (VCP)
- **[VCP-1] 顯性化警告**：手動將模擬盤餘額耗盡或設定極低風控比，確認 Dashboard 出現 `[SIZE]` 琥珀金警告而非靜默。
- **[VCP-2] 診斷可用性**：PM 執行 `dotnet run --project ...` 後，能獲得完整的環境與下單模擬報告，用於自主巡檢。
