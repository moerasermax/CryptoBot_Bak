# Task Capsule: S74-B Integrated Web CLI Advisor Chat

## 1. 任務背景 (Context)
「彈出 CMD 視窗」方案 (Scheme A) 在使用者環境中不穩定（視窗閃退），且頻繁切換視窗體驗欠佳。使用者要求將對話功能整合進網頁 UI，提供類似「對話框」的互動體驗。

## 2. 目標 (Goals)
- [ ] 在 `/lab` 頁面實作 `AiChatModal.razor` 組件，提供對話介面。
- [ ] 實作 `CliProcessBridge`：在後端管理一個持久的 `gemini` 進程，重新導向 StandardInput/Output。
- [ ] 透過 SignalR 或簡單的 API Long-polling 將 CLI 的 StandardOutput 串流至前端 UI，並將 UI 輸入傳回 StandardInput。
- [ ] 當進程完成 JSON 寫檔後，自動關閉 Modal 並套用參數。
- [ ] 繼續保留 Step 1/Step 2 佈局。

## 3. 關鍵路徑 (Critical Path)
1. **進程管理 (Backend)**:
   - 建立 `InteractiveChatSession` 類別，封裝 `Process` 物件。
   - 使用 `RedirectStandardInput = true` 與 `RedirectStandardOutput = true`。
   - 監聽 `OutputDataReceived` 並快取至記憶體緩衝區供 UI 讀取。
2. **UI 對話介面 (Frontend)**:
   - 實作簡易對話流：[AI] (CLI output) <-> [User] (Text input)。
   - 當 user 按下 Enter 或點擊傳送時，透過 API 送至進程的 `StandardInput.WriteLine`。
3. **完成判定**:
   - 沿用既有的「監控 JSON 檔案」機制。一旦 `InteractiveCliAdvisorService` 偵測到檔案出現，通知 UI 結束對話。
4. **清理機制**:
   - 確保 Modal 關閉或 Timeout 時，正確 `Kill()` 掉後端的 `gemini` 子進程。

## 4. 鐵律遵循 (IRON Protocol)
- **IRON §⑥ (相依單向性)**: UI 與 Process Bridge 需透過 Application 層定義的介面溝通。
- **IRON §⑩ (UTF-8 BOM)**: 所有新組件需包含 BOM。

## 5. 資源引用 (References)
- 既有的 `InteractiveCliAdvisorService.cs` (可作為 Session 管理者的參考)。
- `gemini` CLI 互動模式行為。
