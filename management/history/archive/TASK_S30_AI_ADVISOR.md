# 任務膠囊：S30 AI 量化導師整合 (AI Quant Advisor)

## 🎯 任務目標
1. **Gemini API 整合**：實作與 Google Gemini 1.5 Flash 的對接。
2. **智慧市場上下文**：將 K 線與指標自動轉化為 AI 可讀的量化摘要。
3. **自動調參連鎖**：實作 UI 上的「AI 建議」面板，並支援一鍵填入回測表單。

## 🛠️ 技術上下文 (Full Picture)
- **架構**：`IAiAdvisorService` (Application) -> `GeminiAiAdvisorService` (Infrastructure)。
- **安全性**：Gemini API Key 須持久化於 SQLite，嚴禁存入 appsettings.json。
- **UI**：使用 Blazor `AiCopilotPanel.razor` 組件整合於 `/lab`。

## 📋 實作清單
### T1. 核心 AI 服務 (Backend)
- [ ] 定義 `IAiAdvisorService` 介面，支援 `GetAdviceAsync(context)`。
- [ ] 實作 `GeminiAiAdvisorService`：
    - 串接 `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}`。
    - 實作結構化 Prompt，要求 AI 回傳 JSON 格式的參數建議。
- [ ] 實作 `MarketContextBuilder`：
    - 抓取最近 100 根 K 線。
    - 計算 RSI、ATR、BB 並摘要趨勢（例如：RSI=75, Price@BB_Upper）。

### T2. 安全性與金鑰管理 (Security)
- [ ] 在 `ExchangeAccount` 實體或 `AppDbContext` 新增 `GeminiApiKey` 欄位。
- [ ] 修改 `/settings/exchanges` 頁面，增加一個「Gemini AI API Key」輸入框。
- [ ] 實作 `IAiCredentialProvider` 供 Infrastructure 層讀取金鑰。

### T3. 實驗室 AI 面板 (UI)
- [ ] 建立 `AiAdvisorPanel.razor`：
    - 按鈕：`🪄 問問 Gemini 的看法`。
    - 顯示區：顯示 AI 對目前行情的文字評論與建議參數。
    - 按鈕：`✅ 填入建議參數`（聯動 `ApplyParametersAsync`）。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Build]**：`dotnet build` 0 錯誤 0 警告。
- **[VCP-AI]**：在 `/lab` 點擊分析，確認 AI 能辨識出目前 K 線呈現的是「上漲趨勢」還是「區間震盪」。
- **[VCP-Apply]**：點擊「填入」後，回測表單數值自動更新，按「開始優化」能正常跑完。

## 📤 交付要求
- 完成後回報「實作已就緒，請 Gemini 進行 VCP 驗證」。
- **必須附上受影響檔案清單。**
