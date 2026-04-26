# 任務膠囊：[S30-FIX-V2] Gemini 模型名稱最終修正

## 🎯 任務目標
徹底修復 Gemini API 404 錯誤。目前的 `gemini-3.1-flash` 在 `v1` 端點依然不可用。

## 🛠️ 技術上下文 (Full Picture)
- **失敗記錄 1**：`models/gemini-1.5-flash` @ `v1beta` ➡️ 404。
- **失敗記錄 2**：`models/gemini-3.1-flash` @ `v1` ➡️ 404。
- **當前日期**：2026-04-22。

## 📋 實作清單
### T1. 模型名稱容錯化 (Infrastructure)
- [ ] **嘗試穩定模型**：將 `GeminiOptions.cs` 的 `Model` 更改為 **`gemini-2.0-flash`**。這是 2026 年最主流的穩定版本。
- [ ] **端點鎖定**：維持 `BaseUrl` 為 `v1` 穩定版端點 (`https://generativelanguage.googleapis.com/v1/models/`)。

### T2. 增加備援機制 (Service Logic)
- [ ] **Fallback 邏輯**：在 `GeminiAiAdvisorService.cs` 中增加簡單的 404 容錯：若首選模型失敗，嘗試使用 `gemini-1.5-flash-latest` 作為備援（僅限此次熱修補調試）。
- [ ] **明確日誌**：將 Google 回傳的 `Call ListModels to see...` 建議印出到 Console，方便直接從輸出看到可用模型。

## ✅ 驗證檢核點 (VCP)
- **[VCP-API]**：在 `/lab` 點擊 AI 建議，確認不再回傳 404。
- **[VCP-Success]**：必須看到 AI 回傳的「中文評論」與「建議參數」。

## 📤 交付要求
- 完成後回報「V2 修正已就緒」。
- **附上最終選定的 Model 與 BaseUrl。**
