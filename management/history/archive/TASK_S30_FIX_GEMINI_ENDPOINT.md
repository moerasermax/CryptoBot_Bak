# 任務膠囊：[S30-FIX] Gemini API 端點與模型升級

## 🎯 任務目標
修復 Gemini API 呼叫時出現的 **HTTP 404** 錯誤。
經診斷，`gemini-1.5-flash` 模型於 2026 年初已正式退役，且 `v1beta` 端點對該模型已不再提供支援。

## 🛠️ 技術上下文 (Full Picture)
- **錯誤訊息**：`models/gemini-1.5-flash is not found for API version v1beta`。
- **配置位置**：`CryptoBot.Infrastructure/Ai/GeminiOptions.cs`。
- **實作位置**：`CryptoBot.Infrastructure/Ai/GeminiAiAdvisorService.cs`。

## 📋 實作清單
### T1. 配置更新 (Infrastructure)
- [ ] **模型升級**：將 `GeminiOptions.cs` 中的 `Model` 預設值由 `gemini-1.5-flash` 修改為 **`gemini-3.1-flash`**。
- [ ] **端點切換**：將 `BaseUrl` 由 `v1beta` 修改為 **`v1`** 穩定版端點 (`https://generativelanguage.googleapis.com/v1/models/`)。

### T2. 健壯性檢查 (Service Logic)
- [ ] **JSON 解析加固**：(已由 PM 初步修正) 確保 `ExtractJson` 邏輯能正確過濾 Markdown 標籤。
- [ ] **錯誤日誌優化**：在發生 404 或 400 錯誤時，日誌應明確提示「模型退役或金鑰無效」，引導使用者檢查 `GeminiOptions`。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Build]**：`dotnet build` 0 錯誤 0 警告。
- **[VCP-API]**：在 `/lab` 頁面點擊「問問 Gemini 的看法」，確認回應不再回傳 404，而是正確取得 AI 評論。
- **[VCP-Schema]**：確認 `gemini-3.1-flash` 回傳的 JSON 結構與現有 `AiPayload` 紀錄相容。

## 📤 交付要求
- 完成後回報「實作已就緒，請 Gemini 進行 VCP 驗證」。
- **必須附上受影響檔案清單。**
