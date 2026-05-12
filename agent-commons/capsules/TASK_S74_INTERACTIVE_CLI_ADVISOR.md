# Task Capsule: S74 Interactive CLI AI Advisor Implementation

## 1. 任務背景 (Context)
為提升「AI 建議參數」的人機協作體驗，需實作一個基於本地端 `gemini` CLI 的互動式策略提供者 (`InteractiveCliAdvisorService`)。當用戶在 UI 點擊「生成」時，將彈出一個全新的終端機視窗，由 PM/AI 以對話方式與用戶探討當前行情。
考量到未來其他 AI 代理人需要進行「失敗策略根因分析 (Post-mortem)」，用戶決定**永久保留**這些人機討論所產出的最終 JSON 結果，作為系統的歷史軌跡。

## 2. 目標 (Goals)
- [ ] 實作 `InteractiveCliAdvisorService` 繼承 `IAiAdvisorService`。
- [ ] 設定專屬儲存目錄 `ai_ops/state/advisor_history/`，以 Timestamp 作為檔名（如 `advice_20260508_143000.json`）。
- [ ] 使用 `System.Diagnostics.Process` 彈出新視窗（`cmd.exe /c start cmd /k gemini -i ...`）。
- [ ] 實作 File System Polling，等待該 JSON 檔案產生並解析，隨後將結果回傳 UI。
- [ ] 在 `DependencyInjection.cs` 提供機制，根據配置切換至此實作。

## 3. 關鍵路徑 (Critical Path)
1. **儲存架構定義**:
   - 確保啟動時建立 `ai_ops/state/advisor_history/` 目錄。
   - 每次請求生成唯一的檔案路徑，並傳遞給 AI。
2. **Prompt 設計**:
   - 在 `BuildPrompt` 中附加明確指示：「當討論結束且參數確認後，請**務必**將最終的純 JSON 結果寫入到此絕對路徑：`{targetFilePath}`，C# 系統正在等待該檔案」。
3. **非同步等待機制**:
   - 在 `GetAdviceAsync` 中使用 `Task.Delay` 進行輪詢 (Polling)，檢查檔案是否存在且內容有效。
   - 設定合理的 Timeout（例如 10 分鐘，考量到人工討論需要時間）。若超時，回傳 `AiAdviceResult.Success = false`。
4. **CLI 呼叫封裝**:
   - 處理字串跳脫，確保 Prompt 安全地透過 CMD 傳遞給 `gemini` CLI。
5. **依賴注入與切換**:
   - 擴充 `GeminiOptions` 或於 `appsettings.json` 新增開關 `AdvisorProvider: "InteractiveCli"`（或於 `DependencyInjection` 中處理邏輯）。

## 4. 鐵律遵循 (IRON Protocol)
- **IRON §⑥ (四層相依單向性)**: `InteractiveCliAdvisorService` 實作必須放在 `Infrastructure` 層。
- **IRON §⑩ (UTF-8 BOM)**: 所有新增的 `.cs` 檔案必須包含 UTF-8 BOM。
- **IRON §⑫ (寫真單原則)**: 完工時，Engineer 必須出示實際彈出視窗並成功將檔案寫入 `advisor_history/`，且 UI 成功抓取參數的流程紀錄。

## 5. 資源引用 (References)
- `IAiAdvisorService.cs`: 需滿足此介面合約。
- `GeminiAiAdvisorService.cs`: 參考既有的 Prompt 生成與 JSON Sanitization 邏輯。
