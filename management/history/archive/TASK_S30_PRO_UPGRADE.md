# 任務膠囊：[S30-PRO] 升級至 Gemini 2.5 Pro & 自主驗證機制

## 🎯 任務目標
將 AI 顧問模型正式切換至 **Gemini 2.5 Pro**，並實作 **「先驗證、後交付」** 的自動化檢核流程。

## 🛠️ 技術上下文 (Full Picture)
- **模型名稱**：使用 **`gemini-2.5-pro`**。
- **端點版本**：鎖定為 **`v1`** 穩定版。
- **關鍵要求**：執行端必須在「不依賴 UI 手動操作」的情況下，先自行呼叫 API 成功，才能宣告任務完成。

## 📋 實作清單
### T1. 配置更新 (Infrastructure)
- [ ] **模型切換**：`GeminiOptions.cs` 的 `Model` 預設值改為 **`gemini-2.5-pro`**。
- [ ] **Timeout 調整**：`TimeoutSeconds` 預設值調高至 **30** 秒。

### T2. 實作自主驗證腳本 (Verification Loop)
- [ ] **建立診斷工具**：在 `tests/` 或 `scripts/` 下建立一個臨時的 `GeminiSmokeTest.cs` 或腳本。
- [ ] **真實呼叫測試**：該腳本必須從資料庫讀取金鑰，並向 `v1/models/gemini-2.5-pro:generateContent` 發送測試請求。
- [ ] **重試與熔斷**：
    - 允許嘗試不同模型組合（如 `gemini-2.5-pro`, `gemini-1.5-pro`）。
    - **若錯誤超過 5 次**：必須立即停止，並將最後一次失敗的 **完整 HTTP Header 與 Body 日誌** 存入 `ai_ops/diagnostics/GEMINI_ERROR.log`。

### T3. 錯誤回報機制
- [ ] **日誌捕獲**：在 `GeminiAiAdvisorService.cs` 強化針對 400/404/429 的原始錯誤訊息補獲，並確保其能被正確記錄到 `ILogger`。

## ✅ 驗證檢核點 (VCP)
- **[VCP-SelfTest]**：執行端必須回報：「已通過自主驗證腳本測試，成功取得 AI 回應」。
- **[VCP-FailReport]**：若失敗 5 次，執行端必須回報：「驗證失敗已達 5 次，日誌已存至 ai_ops/diagnostics/GEMINI_ERROR.log」。

## 📤 交付要求
- **成功交付**：回報「Gemini 2.5 Pro 升級已就緒」，並附上測試成功的 Model 字串。
- **異常回報**：若 5 次皆失敗，請將 `GEMINI_ERROR.log` 的內容貼在回報訊息中，由 PM 進一步診斷。
