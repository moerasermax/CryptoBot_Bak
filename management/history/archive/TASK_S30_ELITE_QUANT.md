# 任務膠囊：[S30-ELITE] 高級量化決策鏈 (3.1 Pro 核心)

## 🎯 任務目標
升級 AI 顧問至 **Gemini 3.1 Pro**，實作「高精度市場分析」與「雙 Pro 模型自動備援機制」，以達成最高勝率的參數優化。

## 🛠️ 技術上下文 (Full Picture)
- **核心模型**：**`gemini-3.1-pro`** (Primary) / **`gemini-2.5-pro`** (Fallback)。
- **付費環境**：使用者已升級為 Pay-as-you-go，具備更高的 RPM 權限。
- **目標架構**：AI 不再只給建議，而是要執行「行情定性」並輸出「三維網格 (Min/Max/Step)」。

## 📋 實作清單
### T1. 雙 Pro 模型備援機制 (Infrastructure)
- [ ] **配置擴展**：更新 `GeminiOptions.cs`，支援 `PrimaryModel` (3.1-pro) 與 `FallbackModel` (2.5-pro)。
- [ ] **自動降級鏈 (The Chain)**：在 `GeminiAiAdvisorService.cs` 實作：
    - 發送請求至 `PrimaryModel`。
    - 若收到 **429 (Rate Limit)**、**503 (Overloaded)** 或 **404**：
        1.  執行一次指數退避 (Wait 3s)。
        2.  若失敗，自動切換至 `FallbackModel` 重新嘗試。
    - **日誌追蹤**：明確記錄 `[AI-ELITE] Switched to Fallback (2.5-pro) due to error X...`。

### T2. 高維度行情分析 (Prompt Engineering)
- [ ] **Prompt 進化**：在 `BuildPrompt` 中加入深度量化指令：
    - **行情定性**：要求 AI 先判斷目前是 Trending (趨勢) 還是 Ranging (震盪)。
    - **多目標優化**：明確要求以 **「Sharpe Ratio 最大化」** 與 **「Max Drawdown 最小化」** 為目標。
    - **三維網格輸出**：強制回傳 `{"min": x, "max": y, "step": z}` 結構。

### T3. 結構化數據與 UI 對接 (ConsoleApp / Lab)
- [ ] **DTO 與 解析器**：全面升級 `AiAdviceResult` 與 `SanitizeParameters` 以解析巢狀 JSON 網格物件。
- [ ] **表單同步更新**：確保所有 `ParameterForm.razor` (SMA, B46, Trend, MeanRev) 的 `ApplyParametersAsync` 能正確接收並展開 AI 建議的 Min/Max/Step。

### T4. 閉環自驗證 (Self-Verification)
- [ ] **建立 `GeminiEliteDiagnostic.cs`**：
    - 執行一次 3.1 Pro 真實呼叫。
    - **失敗熔斷**：若兩次 Pro 模型皆失敗超過 5 次，將 **完整 HTTP 封包日誌** 存入 `ai_ops/diagnostics/ELITE_FAILURE.log` 供 PM (Gemini) 遠端診斷。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Elite-Connect]**：成功從 `gemini-3.1-pro` 取得回應。
- **[VCP-Fallback]**：手動停用 3.1 模型，確認系統能自動降級至 2.5 Pro 且回應品質依然優秀。
- **[VCP-Grid-Size]**：確認套用 AI 建議後，`GridSize` 保持在合理範圍（例如 10-200）而非縮小到 1。

## 📤 交付要求
- 完成後回報「ELITE 高級量化決策鏈已上線」。
- **必須附上最終測試成功的 Primary/Fallback 模型字串。**
