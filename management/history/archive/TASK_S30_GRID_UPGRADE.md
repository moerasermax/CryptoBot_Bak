# 任務膠囊：[S30-GRID] AI 智慧網格生成器

## 🎯 任務目標
將 AI 顧問從「點建議」升級為「網格建議」。讓 Gemini 根據市場波動率，自動建議優化掃描的範圍 (Min, Max) 與精細度 (Step)。

## 🛠️ 技術上下文 (Full Picture)
- **目前 Bug**：套用 AI 建議後，Min=Max=Value，導致 GridSize=1，失去了優化掃描的意義。
- **目標結構**：AI 應回傳 `{"ParameterName": {"min": 10, "max": 50, "step": 5}}`。
- **影響範圍**：`IAiAdvisorService` 契約、`GeminiAiAdvisorService` 實作、以及所有 `ParameterForm.razor` 元件。

## 📋 實作清單
### T1. 契約與解析升級 (Application & Infrastructure)
- [ ] **DTO 更新**：修改 `AiAdviceResult` 與 `AiPayload`，將 `SuggestedParameters` 的型別由 `Dictionary<string, decimal>` 改為能承載 `Min/Max/Step` 的結構（建議定義 `ParameterGridRange` 類別）。
- [ ] **Prompt 進化**：在 `GeminiAiAdvisorService.BuildPrompt` 中明確要求 AI 回傳 JSON 網格。
    - *要求例*：針對波動率高的市場，擴大 Min/Max 區間；針對需要精細回測的參數，縮小 Step。
- [ ] **解析韌性**：更新 `SanitizeParameters` 以解析巢狀 JSON 對象。若 AI 回傳的是單一值，自動將其轉化為 `min=max=val, step=1` 以相容舊邏輯。

### T2. 表單元件重構 (ConsoleApp / Lab)
- [ ] **Base Class 更新**：修改 `StrategyParameterFormBase.ApplyParametersAsync` 接收新的網格 DTO。
- [ ] **具體表單更新**：
    - [ ] `SmaParameterForm.razor`
    - [ ] `B46ParameterForm.razor`
    - [ ] `TrendFollowingParameterForm.razor`
    - [ ] `MeanReversionParameterForm.razor`
    - **動作**：將 `_min`, `_max`, `_step` 三個欄位同步更新。

### T3. 智慧安全鎖 (Safety Check)
- [ ] **GridSize 防護**：在 UI 套用建議後，若計算出的 `CurrentGridSize > 2000`，自動在畫面上顯示提示，並建議使用者手動調大 Step 以保護瀏覽器效能。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Grid]**：點擊「問問 Gemini 的看法」，確認 AI 回傳了包含 Min, Max, Step 的結構。
- **[VCP-Apply]**：點擊「填入建議參數」，確認表單的三個欄位同時變動，且 `GridSize` **大於 1**（除非 AI 認為該點極其精確）。
- **[VCP-Optimize]**：直接按「開始優化掃描」，確認能跑出一系列基於 AI 建議範圍的排行榜結果。

## 📤 交付要求
- 完成後回報「AI 智慧網格生成器已就緒」。
- **必須附上受影響的表單清單。**
