# Task Capsule: S75 Sidekick Hub — gemini --acp 長連接 IPC 重構

## 1. 任務背景 (Context)

S74-C 完工後既有 Sidekick 全域側邊欄走 `Process.Start("gemini", "-p ...")` per-prompt single-shot 模式 — 每次對話冷啟動 ~1-3 秒、受 Win32 `CreateProcess` **28K wchar 字串上限**（既有 `sliding window prompt budget = 28K wchar`）。

User 明示需求（2026-05-13 verbatim）：
> 「我希望可以從網頁那邊點擊按鈕之後，不論是我給她 prompt 還是怎樣，他都可以像我用 cmd 這樣的對話，不是一直重新 reload，也不考慮使用 api 的方式，因為這樣太花錢了，不如寫一個 cmd 或其他方式當一個介接層即可」

技術翻譯：用 `gemini --acp` 持續長連接 IPC（JSON-RPC 2.0 / stdin-stdout）取代 single-shot，消除冷啟動 + 消除 28K 字串上限；走 `oauth-personal` 免 API key、免費 quota。

**Phase 0 Probe 取證關鍵發現**（詳見 `agent-commons/roles/engineer/drafts/2026-05-13_S75_PHASE0_REPORT.md`）：
- ✅ `gemini --acp` JSON-RPC 2.0 handshake 成功（`initialize` + `protocolVersion: 1`）
- ✅ `agentCapabilities.loadSession: true` — session 持久化原生支援
- ✅ idle RSS ~300 MB / no leak
- ⚠️ Process tree = cmd shim + 2 node.exe → kill 必須走 tree
- 🚨 cwd 內 `GEMINI.md` auto-load 進 PM 角色 → Sidekick 必須隔離 cwd
- 🚨 model 429 `MODEL_CAPACITY_EXHAUSTED` 多次重現 → 需 retry + fallback

## 2. 目標 (Goals)

建立**單一實例、長效運作、429 韌性**的 Sidekick 服務中樞，透過 ACP（gemini-cli Agent Client Protocol mode）實現與 C# 端穩定 IPC，解決對話冷啟動延遲並確保 cwd 環境隔離。

- [ ] **ACP IPC 重構**：`GlobalAiChatService.cs` 從 `Process.Start gemini -p` per-prompt 改為持有 long-lived `gemini --acp` 子 process + stdin/stdout line-delimited JSON-RPC 2.0
- [ ] **Process tree 管理**：用 `Win32_Process` CIM query 走 tree kill（cmd shim → 2 node.exe 子代）；確保關閉 0 殘留進程
- [ ] **cwd 隔離**：Sidekick gemini 啟動於 dedicated temp dir（避免 `GEMINI.md` + `agent-commons/` auto-load 進 PM 角色）
- [ ] **429 retry + fallback model**：遇 `MODEL_CAPACITY_EXHAUSTED` 退避重試 (3x)、按 `gemini-3.1-pro → gemini-2.5-flash → 用戶可見錯誤 UI` 鏈降級
- [ ] **Session 持久化**：使用 ACP `loadSession` capability 取代既有 `--session-id` per-prompt 模式

## 3. 關鍵路徑 (Critical Path)

### Phase 1 — ACP Method Schema 探測（純 shell / 📖 唯讀）

- 探 `authenticate` method（auth methods: oauth-personal）
- 探 `session.new` / `session.load` params schema
- 探 `prompt` method params + response stream schema
- 探 `cancel` method（取消 in-flight prompt）
- 探 connection lifecycle（process exit 條件 / 重連語意）
- 寫進 `roles/engineer/drafts/2026-05-13_S75_PHASE1_ACP_SCHEMA.md`

### Phase 2 — C# 端 IPC 傳輸層重構

- `Application` 層加 `IGeminiAcpClient` 介面（依 IRON ⑥）
- `Infrastructure` 層 `GeminiAcpClient` 實作：
  - `Process` + `StandardInput`/`StandardOutput` 持有
  - JSON-RPC 2.0 framing（line-delimited、`id` 追蹤、`Pending<TaskCompletionSource>` map）
  - async `InitializeAsync` / `AuthenticateAsync` / `SendPromptAsync(prompt) → IAsyncEnumerable<chunk>`
- 改 `GlobalAiChatService` 從 `Process.Start gemini -p` 切換到 `IGeminiAcpClient`
- 保持既有 `SendAsync` 永不拋合約 / `DashboardEventBus` 整合 / `ApplyAiParametersUpdate` 不動

### Phase 3 — 核心加固

- 429 retry policy（exponential backoff、3 次上限、fallback model chain）
- cwd 隔離：`Process.StartInfo.WorkingDirectory = Path.GetTempPath() / "cryptobot-sidekick"` + dedicated temp 目錄
- Process tree 管理：`Win32_Process` query + recursive kill on dispose / app exit
- `SemaphoreSlim(1,1)` 並發語意重評估（ACP 長連接下單 service 可序列 prompt，但 stream 中途 cancel 須 ACP `cancel` method 對應）

### Phase 4 — 整合測試與 VCP

- 既有 227 tests 全綠 / 0 警告 0 錯誤
- 新增整合測試：5 輪連續對話 / RSS idle 監控 / 429 retry log assertion / 關閉後 0 殘留 process
- 完工交付 VCP（依 `~/.agentcharter/core/completion-delivery.md`）含 Directive Header + Demo 雙保險 + 3-5 個情境 + 失敗解讀表

## 4. 鐵律遵循 (IRON Protocol)

- **IRON §⑥ 四層相依單向性**：`IGeminiAcpClient` 介面定義於 `Application`、實作於 `Infrastructure`；`Domain` 完全不接觸 ACP；`ConsoleApp` / `Web` 不直接 spawn process。S75 不進入 Domain 層（依 PM Dependencies §7）。
- **IRON §⑦ Domain 純粹性**：Domain 不接觸 IO / time / process；任何時間注入須走 `IClock`、ID 走 `IIdGenerator`。
- **IRON §⑩ UTF-8 BOM**：所有新 / 改 `.cs` 檔含中文字串必含 BOM（驗 `head -c 3 <file> | xxd -p` 應為 `efbbbf`）。
- **IRON §⑪ SDK 雙保險韌性**：429 偵測雙保險 — `if (statusCode == 429 || message.Contains("RESOURCE_EXHAUSTED") || message.Contains("MODEL_CAPACITY_EXHAUSTED"))`。
- **IRON §⑫ 寫真單原則**：完工 VCP 須附 stdout 實證 — 5 輪對話 log / RSS 監控數據 / 429 retry log / process tree kill 證據。

## 5. 資源引用 (References)

- `CryptoBot/src/CryptoBot.Web/AiChat/GlobalAiChatService.cs` — 重構主檔（既有 Scoped service + `_gate` SemaphoreSlim + `SendAsync` 合約）
- `CryptoBot/src/CryptoBot.Web/AiChat/DashboardEventBus.cs` — `ApplyAiParametersUpdate` 整合點不動
- `CryptoBot/src/CryptoBot.Web/Components/Layout/MainLayout.razor` — Sidebar 掛載點不動
- `agent-commons/roles/engineer/drafts/2026-05-13_S75_PHASE0_REPORT.md` — Phase 0 Probe 完整結論 + 證據
- `agent-commons/roles/engineer/drafts/2026-05-13_S75_DISCUSSION.md` — S75 discussion phase 時間軸 (T1-T15)
- Gemini CLI `0.42.0`（本機 `C:\Users\Moera\AppData\Roaming\npm\gemini`）
- ACP `initialize` response capabilities：`loadSession: true` / `promptCapabilities.{image, audio, embeddedContext}` / `mcpCapabilities.{http, sse}` / authMethods (oauth-personal 路徑)

## 6. 驗收條件 (Acceptance)

依 PM 建議 + Phase 0 取證 grounded：

- [ ] **冷啟動消除**：UI 持續對話 ≥ 5 輪、第 2+ 輪回應啟動延遲 ≤ 500ms（vs 既有 single-shot ~1-3s）
- [ ] **RSS 穩定性**：Sidekick 啟動後 idle RSS ≤ 350 MB（Phase 0 baseline ~300 MB）、連續使用 ≥ 10 分鐘 RSS 漂移 ≤ ±50 MB
- [ ] **429 韌性**：模擬 / 真實 429 出現時、log 可見 retry 行為（指數退避）、對話**不中斷** + UI 顯示降級提示
- [ ] **整潔度**：單一 user 場景下僅 1 個 Sidekick instance；app 關閉時 0 殘留 node.exe / cmd.exe / conhost.exe；產出 0 警告 0 錯誤
- [ ] **回歸測試**：既有 **227 項** 自動化測試全綠（不退步）；新增整合測試覆蓋 ACP IPC 主流程
- [ ] **cwd 隔離證實**：Sidekick gemini 子 process 的 `WorkingDirectory` 為 temp dir 非專案根；專案 `git status` 不受 Sidekick 對話影響

## 7. 依賴與風險 (Dependencies & Risks)

### 依賴

- **[S72] 同步邏輯加固**：平級優先（依 `nextwork.md`）。S75 範圍限於 `Application` + `Infrastructure` 層，**不進入 Domain 層**；可與 S72 併行開發，避免 Domain 層侵入性修改撞檔。
- Gemini CLI `0.42.0` 預裝（user 已 `oauth-personal` 登入、quota 由 Google 帳號免費額度提供）。

### 已知風險

- cwd 環境汙染（`GEMINI.md` auto-load 進 PM 角色）→ 已由 cwd 隔離設計緩解
- 頻繁調用引發 429 `MODEL_CAPACITY_EXHAUSTED`（Phase 0 兩 model 都中過）→ 已由 retry + fallback chain 緩解
- 孤兒進程資源洩漏（cmd shim 拿不到 child node PID）→ 已由 Win32_Process tree kill 緩解

### 未知風險（Phase 1 探完降到已知）

- ACP `prompt` method response stream schema 在長對話 / 跨 turn / image 多模態下的解析穩定性
- `SemaphoreSlim(1,1)` 在 ACP 長連接 + 中途 cancel 場景下是否有死鎖路徑（須 ACP `cancel` method schema 對應）
- ACP connection lifecycle（process exit 條件、stdin EOF 行為、重連語意）

---

## 8. 立案脈絡

- **Phase 0 Probe**：2026-05-13 user 授權執行、Engineer 親跑 4/4 完成、結論寫進 `drafts/2026-05-13_S75_PHASE0_REPORT.md`
- **PM 諮詢**：2026-05-13 PM 提供 6 段 capsule 草案、Engineer 抽驗 5.5/6 合格、兩處 F4 小錯（§1 ACP 全名 / §2 Scope out 措辭）由 Engineer 於本檔寫入時順手修正
- **紀律遵循**：依 user verdict v2（2026-05-13）— PM 對 `agent-commons/capsules/` 寫權暫停，本檔由 Engineer 代寫 + user 簽核 channel 寫入；PM 個體層 reflection v2 已提交於 `roles/pm/reflections/2026-05-12_F1-F5_s75_premature_execution.md`（commit `b941021`）
- **立案授權**：待 user 簽核 + commit + push 後正式立案
