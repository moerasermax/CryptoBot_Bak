# 任務膠囊：[S30-FIX] AI 參數代入 Bug 修復與開發成本優化

## 🎯 任務目標
1. **修復 Bug**：解決點擊「填入建議參數」後表單無反應的問題。
2. **節省成本**：將預設模型調降至 **Gemini 1.5 Flash** 以利頻繁開發測試。

## 🛠️ 技術上下文 (Full Picture)
- **Bug 診斷**：
    - `GeminiAiAdvisorService` 解析 JSON 時過於嚴格，若 AI 回傳 `minimum` 而非 `min` 則會失敗。
    - Prompt 誘導力不足，導致 AI 偶爾會自行翻譯或簡化 ParameterKey（例如把 `FastSmaPeriod` 改成 `FastSma`），造成過濾器找不到對應 Key。
- **模型調整**：切換回 `gemini-1.5-flash`。

## 📋 實作清單
### T1. 模型與成本控制 (Infrastructure)
- [ ] **模型降級**：將 `GeminiOptions.cs` 的 `Model` 預設值改回 **`gemini-1.5-flash`**。
- [ ] **端點檢查**：確保支援 `v1` 或 `v1beta`（視該模型目前所在的穩定端點而定）。

### T2. 解析韌性與 Prompt 強化 (Service Logic)
- [ ] **Prompt 嚴格化**：在 `BuildPrompt` 中加入強烈指令，要求 AI **絕對禁止修改參數鍵名 (Key)**，必須與給定的 `ExpectedParameterKeys` 100% 匹配。
- [ ] **解析寬容度**：升級 `TryParseGridRange`，支援 `min/minimum/start`, `max/maximum/end`, `step/increment/gap` 等變體鍵名。
- [ ] **錯誤可視化**：若 AI 回傳的參數經過過濾後為空，`GetAdviceAsync` 應回報錯誤訊息：「AI 建議的參數名稱與系統不符，解析失敗」。

### T3. 表單對接與驗證 (ConsoleApp / Lab)
- [ ] **驗證所有表單**：確保 `SmaParameterForm`, `B46ParameterForm`, `TrendFollowingParameterForm`, `MeanReversionParameterForm` 皆已正確覆寫 `ApplyGridParametersAsync`。
- [ ] **UI 狀態同步**：確認套用參數後有正確呼叫 `NotifyChangedAsync()` 以觸發 `GridSize` 的重新計算。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Cost]**：確認模型已切換為 `gemini-1.5-flash`，降低開發點擊成本。
- **[VCP-Apply-Fix]**：在 `/lab` 點擊「填入建議參數」，確認表單欄位**確實發生變動**，且 `GridSize` 更新為 AI 建議的掃描規模。
- **[VCP-KeyMatch]**：檢查日誌，確認沒有出現「參數解析為空」的警告。

## 📤 交付要求
- 完成後回報「AI 參數代入修復與模型降級已就緒」。
- **必須附上修正後的 `ExtractJson` 與 `SanitizeParameters` 代碼片段。**
