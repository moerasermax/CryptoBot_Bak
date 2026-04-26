# 任務膠囊：[S30-LITE] Gemini 2.5 Flash-Lite 升級與 429 韌性防禦

## 🎯 任務目標
將模型切換至 **Gemini 2.5 Flash-Lite**，並實作 **指數退避重試機制**，徹底解決「點一下就 429」的問題。

## 🛠️ 技術上下文 (Full Picture)
- **模型名稱**：使用 **`gemini-2.5-flash-lite`**。
- **端點版本**：鎖定為 **`v1`** 穩定版。
- **速率限制對策**：針對免費版 RPM (15次) 與 RPD (1000次) 的限制，建立自動化防禦層。

## 📋 實作清單
### T1. 模型輕量化 (Infrastructure)
- [ ] **模型切換**：將 `GeminiOptions.cs` 的 `Model` 預設值改為 **`gemini-2.5-flash-lite`**。
- [ ] **參數微調**：維持 `TimeoutSeconds = 30`，確保 Lite 模型即便在尖峰時段也能完整回應。

### T2. 實作自動重試機制 (Exponential Backoff)
- [ ] **GetAdviceAsync 改造**：在 `GeminiAiAdvisorService.cs` 中封裝重試邏輯。
    - **觸發條件**：當收到的 HTTP Status 為 **429** 或 **503** 時。
    - **重試策略**：最大重試 **3 次**。
    - **延遲間隔**：`2秒 -> 4秒 -> 8秒` (使用 `Task.Delay`)。
    - **日誌追蹤**：每次重試時在日誌記錄 `[AI-RETRY] Attempt X due to 429...`。

### T3. 自主驗證腳本 (Self-Verification)
- [ ] **建立 `GeminiResilienceTest.cs`**：
    - 模擬連續呼叫 API 3 次，觀察退避邏輯是否生效。
    - **若連續 5 次重試後依然失敗**：停止執行，並將最後一次 Google 回傳的詳細錯誤 JSON (包含 `quota` 或 `overloaded` 訊息) 存入 `ai_ops/diagnostics/GEMINI_429_DETAIL.log`。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Lite]**：確認 `GeminiOptions.cs` 已正確更新為 `gemini-2.5-flash-lite`。
- **[VCP-Retry]**：在日誌中確認重試機制能正確處理 429 錯誤。
- **[VCP-Success]**：在 `/lab` 頁面點擊 AI 建議，確認能穩定獲得回應且無 UI 噴錯。

## 📤 交付要求
- 完成後回報「Gemini 2.5 Flash-Lite 韌性修復已就緒」。
- **若自主驗證失敗，必須附上 `GEMINI_429_DETAIL.log` 內容協助排錯。**
