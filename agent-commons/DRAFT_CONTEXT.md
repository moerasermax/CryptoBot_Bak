# 暫存堆疊 (Draft Context)

> **狀態**：accumulating — 2026-05-12 S74-C 進行中、Phase 1/2 完成、Phase 3-5 待續。
> **依 working-stack-discipline §5 接班動作**：下個 session 進來必讀本檔。

---

## 接班指引（給下個 Engineer Claude Code session）

當前任務：**TASK_S74_C_GLOBAL_AI_SIDEBAR.md**（位於 `agent-commons/capsules/`），PM 已完成所有設計裁決（Q1-Q4 全採我建議 + 採用 `--session-id` 自管 + 接受 S74-B churn）。Capsule 內容無 blocking 疑點，可直接續做。

### 已完成（Phase 1 + 2，build 0 警告 0 錯誤、測試 227 全綠）

**Phase 1 — S74-B 全量清理**：
- 已刪 7 檔：
  - `CryptoBot/src/CryptoBot.Application/Ai/IInteractiveChatSession.cs`
  - `CryptoBot/src/CryptoBot.Application/Ai/IChatSessionManager.cs`
  - `CryptoBot/src/CryptoBot.Infrastructure/Ai/InteractiveChatSession.cs`
  - `CryptoBot/src/CryptoBot.Infrastructure/Ai/ChatSessionManager.cs`
  - `CryptoBot/src/CryptoBot.ConsoleApp/Realtime/AiChatHub.cs`
  - `CryptoBot/src/CryptoBot.ConsoleApp/Realtime/AiChatHubBridge.cs`
  - `CryptoBot/src/CryptoBot.ConsoleApp/Components/Lab/AiChatModal.razor`
- `InteractiveCliAdvisorService.cs` 已**重寫為 `gemini -p` 單發模式**（不再依賴 ChatSessionManager）
- `Infrastructure/DependencyInjection.cs` 已移除 IChatSessionManager 註冊、ctor 改回 IOptions
- `ConsoleApp/Program.cs` 已移除 `MapHub<AiChatHub>` + `AddHostedService<AiChatHubBridge>`
- `ConsoleApp/Api/AiAdvisorEndpoints.cs` 已移除 `/api/ai/chat/{start,send,cancel}` + 相關 4 DTO（**保留** `/api/ai/config`）
- `ConsoleApp/Components/Pages/BacktestLab.razor` 已移除 `<AiChatModal>` 渲染 + `_aiChatOpen` / `_aiAdvisorProvider` state + `OnAiChatAdviceReadyAsync` / `OnAiChatClosed` / `LoadAiAdvisorProviderAsync` 方法；Step 2 按鈕回到固定「🪄 AI 建議」標籤、走 `/api/ai/advise`

**Phase 2 — AiAdvicePayloadParser 共用 helper**：
- 已新建 `CryptoBot/src/CryptoBot.Infrastructure/Ai/AiAdvicePayloadParser.cs` ✅ BOM
- 公開 API 為 `TryParse(rawJson, expectedKeys, out commentary, out parameters, out error)` 一個方法
- `InteractiveCliAdvisorService.cs` 已引用該 helper
- **未做** GeminiAiAdvisorService 的 refactor（既有 private copy 仍在但 work；下個 session 可選擇是否順手抽掉，capsule 未強制）

### 待做（Phase 3-5）

**Phase 3 — GlobalAiChat 後端 + EventBus**（PM 拍板規格）：

1. 新建 `Application/Ai/IGlobalAiChatService.cs`：
   ```
   - Guid SessionUuid { get; }            // 給 gemini --session-id 用
   - IReadOnlyList<ChatMessage> History { get; }  // UI 渲染用副本
   - event Action? HistoryChanged;
   - Task SendAsync(string userText, CancellationToken ct);
   - Task ClearAsync();
   ```
   `ChatMessage` record：`(string Role /* "user"|"ai" */, string Text, DateTimeOffset At, bool HasJson, ApplyAiParametersUpdate? Payload)`

2. 新建 `Application/Realtime/ApplyAiParametersUpdate.cs`：
   ```
   public sealed record ApplyAiParametersUpdate(
       string? TargetStrategyKey,
       IReadOnlyDictionary<string, ParameterGridRange> Parameters,
       string Commentary);
   ```

3. 修改 `ConsoleApp/Realtime/DashboardEventBus.cs`：加 `event Action<ApplyAiParametersUpdate>? ApplyAiParametersRequested;` + 對應 Raise 方法

4. 新建 `Infrastructure/Ai/GlobalAiChatService.cs`（**Scoped** 註冊）：
   - SessionUuid 在 ctor 中 `Guid.NewGuid()` 一次
   - `SendAsync` 每次組 prompt = system_preamble + history dump + new user msg → call `gemini -p "<prompt>" --session-id <uuid>` → 等 stdout
   - 用 `Process.Start` + `ArgumentList`（已驗證的 pattern from InteractiveCliAdvisorService）
   - stdout 收完後 append 到 History、嘗試用 `AiAdvicePayloadParser.TryParse` 偵測 JSON、若成功則 `HasJson=true` 且帶 `Payload`
   - 注意 cmd 8191 字元上限：每次組 prompt 前 check length；若超出，丟舊歷史（sliding window 從尾保留 N 輪）
   - **TargetStrategyKey 來源策略**：optional — 可在 prompt 內請 AI 在 JSON 中夾 `"strategyKey": "sma"` 欄位、若無則 null（套用時用當前 lab state）
   - **`expectedKeys` 從哪來**：sidebar 是全域、無 strategy context；建議在 `SendAsync` 取 `IStrategyCatalog.AllKeys` 作為 union expected keys 餵 parser；JSON 內帶 strategyKey 時再精準過濾

5. 修 `Infrastructure/DependencyInjection.cs::AddAiAdvisor` 加：
   ```csharp
   services.AddScoped<IGlobalAiChatService, GlobalAiChatService>();
   ```

**Phase 4 — GlobalAiSidebar UI + MainLayout 掛載**：

1. 新建 `ConsoleApp/Components/Layout/GlobalAiSidebar.razor`：
   - `position: fixed; right: 1rem; bottom: 1rem; z-index: 9999`
   - 浮動小 icon 按鈕 → 點開側邊 panel（slide-in from right）
   - panel 內顯示 history（從 `IGlobalAiChatService.History`）、輸入欄、傳送鍵
   - 訊息含 JSON 時顯示「🪄 套用參數至實驗室」按鈕 → 觸發 `DashboardEventBus.RaiseApplyAiParameters(message.Payload)`
   - 注入 `IGlobalAiChatService`（Scoped）+ `DashboardEventBus`
   - 訂閱 `service.HistoryChanged` 觸發 `InvokeAsync(StateHasChanged)`
   - IAsyncDisposable 解除訂閱

2. 修 `ConsoleApp/Components/Layout/MainLayout.razor` — 在 `@Body` 之後加 `<GlobalAiSidebar />`

3. 修 `ConsoleApp/Components/Pages/BacktestLab.razor`：
   - 注入 `DashboardEventBus`（若未注入）
   - `OnInitializedAsync` 訂閱 `EventBus.ApplyAiParametersRequested += OnApplyAiParameters`
   - `OnApplyAiParameters(ApplyAiParametersUpdate update)`：
     - 比對 `update.TargetStrategyKey` 與 `State.SelectedModel.Key` — 不符時 toast 提示 user 切換策略
     - 若符或 null → `_dynamicRef?.Instance is StrategyParameterFormBase form → form.ApplyGridParametersAsync(update.Parameters)`
   - `DisposeAsync` 解除訂閱

**Phase 5 — build + test + VCP v5**：
- 編譯 0 警告 0 錯誤
- 測試 227 全綠不降
- VCP v5 含 6-7 個情境（sidebar icon 顯示 / 點開 panel / 對話送 prompt / JSON 偵測 / 套用按鈕跨頁套用 / clear / cancel）

### 關鍵設計約束（PM 已裁決）

- **CLI --session-id 自管模式**：每個 Scoped session 一個 UUID、每次 `gemini -p` 帶同樣 `--session-id`、gemini 自己保留歷史
- **C# History 為 UI 渲染副本**（非真理源 — 真理在 gemini session）
- **EventBus 結構化 payload**（`ApplyAiParametersUpdate` record，含已解析好的 dict、不是 raw JSON）
- **JSON 偵測共用 `AiAdvicePayloadParser.TryParse`**（Phase 2 已抽出）
- **套用上下文不對齊處理**：UI 端 toast 提示 user 切策略後再點套用

### gemini CLI 已 probe 確認的旗標（從 `gemini --help`）

- `gemini [query..]` — 預設 interactive
- `-p "<prompt>"` — headless 單發；output stdin
- `--session-id <uuid>` — 起 session 帶指定 UUID
- `-r/--resume <id>` — resume
- `-o text|json|stream-json` — output 格式選項

### 抽驗權狀態提醒

- 強化抽驗模式 + 結構性失靈裁決皆**仍啟動中**（依 `agent-commons/state/failure_mode_log.md §0`）— PM 對 `agent-commons/{protocols, state}/*` 寫權**仍暫停**
- PM 結案宣告默認待抽驗，須附 stdout 原文

### 當前 git 狀態（session 暫停時點）

```
外層 main：剛通過 build 0 警/0 錯、測試 227 全綠
工作樹：許多異動未 commit — 等 user 下指令決定何時 commit
未 commit 變更（內層 CryptoBot/src）：
  - 刪 7 檔（S74-B 遺產）
  - 新建 1 檔：Infrastructure/Ai/AiAdvicePayloadParser.cs
  - 重寫 1 檔：Infrastructure/Ai/InteractiveCliAdvisorService.cs
  - 改 4 檔：Infrastructure/DependencyInjection.cs / ConsoleApp/Program.cs / Api/AiAdvisorEndpoints.cs / Components/Pages/BacktestLab.razor
```

### 下個 session 第一動作

1. 跑 `/engineer-init`
2. 讀本 DRAFT_CONTEXT 接班（已是必跑、依 working-stack-discipline §5）
3. 確認當前 build 仍 green（`dotnet build CryptoBot/CryptoBot.sln`）
4. 進 Phase 3 從 `IGlobalAiChatService` + `ApplyAiParametersUpdate` 開始
5. 依 Phase 3 → 4 → 5 順序執行

---

> **save 觸發**：依 `working-stack-discipline §3.1` 由 user 明示 / `/checkpoints save`；save 必同步 git commit（§4 鐵律）。本檔當前為「跨 session 中斷接班 anchor」，**不視為 save 完成**（未走完 DRAFT → HANDOFF → commit 三件）。
