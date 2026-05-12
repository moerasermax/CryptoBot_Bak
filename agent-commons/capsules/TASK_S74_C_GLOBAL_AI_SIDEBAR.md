# Task Capsule: S74-C Global Persistent AI Sidebar

## 1. 任務背景 (Context)
Scheme B (網頁內嵌 Modal) 遭遇了 CLI 互動模式的 TTY 限制（`gemini` 進程在被重導 StandardInput 時無法正常回應）。同時，使用者提出更高的 UX 期待：
1. **全域常駐**：希望對話框是一個常駐在右下角的浮動小視窗（小 ICON 點開），跨越所有頁面（Dashboard, Lab, Settings 等）都保持 Session 不中斷。
2. **生命週期**：Session 的對話歷史應與使用者的網頁連線（Blazor Scoped）綁定。
3. **兩階段通用對話**：支援先進行廣泛市場分析，再於實驗室頁面執行特定參數套用。

## 2. 目標 (Goals)
- [ ] **全域 UI 組件**：建立 `GlobalAiSidebar.razor` 並掛載於 `MainLayout.razor`。
- [ ] **歷史紀錄管理**：實作 `GlobalAiChatService` (Scoped) 維護 `List<ChatMessage>`。
- [ ] **無狀態 CLI 轉發 (Stateless Execution)**：
  - 放棄單一持久 CLI 進程。
  - 改為每次發言時，組合「對話歷史 + 新訊息」作為單一 Prompt。
  - 使用 `gemini -p "<prompt>"` 一次性呼叫並獲取回應，確保不因 TTY 限制掛起。
- [ ] **參數套用橋樑 (Context Bridge)**：
  - 檢測 AI 回應中的 JSON 區塊。
  - 若有 JSON，Sidebar 顯示「🪄 套用參數至實驗室」按鈕。
  - 按下後透過 `DashboardEventBus` 廣播，讓 `/lab` 接收並自動填表。

## 3. 關鍵路徑 (Critical Path)
1. **清理與遷移**:
   - 移除 S74-B 產出的 `InteractiveChatSession`、`AiChatHub` 與 `AiChatModal`（若已存在）。
2. **服務開發**:
   - `IGlobalAiChatService` (Application) / `GlobalAiChatService` (Infrastructure)。
   - 組合 Prompt 時需注意 Windows CMD 8191 字元限制（實作 Sliding Window）。
3. **全域 UI**:
   - 實作浮動按鈕與側邊彈出面板。
   - 使用 CSS `position: fixed` 與 `z-index` 確保其在最上層且跨頁穩定。
4. **事件整合**:
   - 在 `DashboardEventBus` 補上 `ApplyAiParameters(string json)` 方法與對應事件。
   - 在 `BacktestLab.razor` 訂閱該事件。

## 4. 鐵律遵循 (IRON Protocol)
- **IRON §⑥ (四層相依)**：介面定義於 Application，實作於 Infrastructure。
- **IRON §⑩ (UTF-8 BOM)**：所有新檔案必須帶 BOM。
- **IRON §⑫ (寫真單原則)**：完工須附上「跨頁面對話歷史保留」與「參數一鍵套用」的實測結果。

## 5. 資源引用 (References)
- `MainLayout.razor`：UI 掛載點。
- `DashboardEventBus.cs`：事件通訊參考。
- `gemini --help`：確認 `-p` 旗標行為。
