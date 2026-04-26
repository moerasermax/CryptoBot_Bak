# 任務膠囊：[S36-S38] UX 深度優化與 AI 模式轉型

## 🎯 任務目標
1. **強化直觀性 (S36)**：在 Dashboard 標註策略對應的業界術語模型名稱。
2. **AI 降級可控化 (S37)**：將 AI 建議改為「產出 Prompt」模式，減少 API 直接依賴。
3. **效能與視覺優化 (S38)**：實驗室排行榜增加 50 筆分頁，並放寬全站版面寬度。

## 📋 實作清單

### T1. Dashboard 視覺映射 (ConsoleApp/Pages)
- [ ] **Dashboard.razor**：在 Active Strategies 列表中的每一列，加入 `Model: [DisplayName]` 標籤。
- [ ] 確保顏色與業界術語對應（例如順勢策略用藍色標籤、逆勢用紫色）。

### T2. AI 導師 Prompt 轉化 (ConsoleApp/Lab)
- [ ] **AiAdvisorPanel.razor**：
    - 將目前的 `GetAiAdviceAsync` 修改為 `GenerateAdvicePrompt`。
    - 點擊後不呼叫後端 AI Service，而是彙整 `Symbol`, `Interval`, `Indicators` 產出一段深度分析指令。
    - 提供「複製 Prompt」按鈕。

### T3. 表格分頁與版面放寬 (ConsoleApp/UI)
- [ ] **BacktestLab.razor**：
    - 實作客戶端分頁 (Client-side Pagination)，每頁 50 筆資料。
    - 增加「第一頁/上一頁/下一頁/最後一頁」按鈕。
- [ ] **app.css**：
    - 找到主要的 layout container，將 `max-width` 從目前的限制（如 1200px）放寬至 `95%` 或 `1600px`。
    - 確保在寬螢幕上兩側不會留白過多。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Dashboard]**：Dashboard 能清楚看到當前跑的是 `B46 Hybrid Model` 而不只是 `SMA-Test`。
- **[VCP-Prompt]**：點擊建議按鈕後，能成功複製一段包含技術指標數據的指令。
- **[VCP-Pagination]**：回測完畢後，排行榜下方出現分頁標籤，且每頁僅顯示 50 筆。
- **[VCP-Width]**：UI 視覺上有明顯的左右延伸，不再擠在中間。
