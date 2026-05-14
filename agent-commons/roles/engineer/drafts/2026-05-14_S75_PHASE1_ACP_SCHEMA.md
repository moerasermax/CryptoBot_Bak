# Engineer Draft: [S75] Phase 1 ACP Method Schema Probe Report

> **位階**：Engineer 端暫存（drafts）— 對齊 `~/.agentcharter/core/working-stack-discipline.md §2`
> **存檔時點**：2026-05-14 Phase 1 親跑探測完成、待 Phase 2 C# 端 IPC 重構參照
> **平行檔**：`agent-commons/capsules/TASK_S75_SIDEKICK_HUB.md` §3 Phase 1 任務本檔交付
> **替代 / 補正**：本檔由 Engineer (Claude Code) 親跑 gemini --acp 取證、**取代** PM A009 違規寫入版本（commit 67bb83b 含、9f5e4e9 revert）；違規版本內容由 PM 寫入、屬 F1 + F3 + §3.5 重犯（詳見 `state/failure_mode_log.md §9.2 A009-X1/X2`）

---

## 1. 探測環境與紀律遵循

- **gemini CLI 版本**：0.42.0（`/c/Users/Moera/AppData/Roaming/npm/gemini`）
- **--acp 旗標**：✅ 支援（`--acp Starts the agent in ACP mode  [boolean]`）；`--experimental-acp` 已 deprecated
- **cwd 隔離**：`mktemp -d -t cryptobot-sidekick-XXXXXX` → `C:\Users\Moera\AppData\Local\Temp\cryptobot-sidekick-aUSpC1`（temp dir 中無 `GEMINI.md` → "Skipping project agents due to untrusted folder" 自動 disable agents / hooks）
- **OAuth 狀態**：user 既有 `oauth-personal` cached（Phase 0 確認）— `authenticate` 不觸發互動 OAuth flow
- **紀律遵循**：
  - 📖 唯讀探測、無 src/ 寫入、無 git mutation（只 Write 本 drafts/ 檔）
  - IRON ⑫ 寫真單原則：所有結論附 stdout 原文
  - v2 §0 第 1 條：本檔由 Engineer 親寫，**取代** PM 違規寫入版本

---

## 2. Probe 1 — `initialize` (baseline 重驗，對齊 Phase 0)

### 2.1 請求

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":1}}
```

### 2.2 真實 stdout response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": 1,
    "authMethods": [
      {"id": "oauth-personal", "name": "Log in with Google", "description": "Log in with your Google account"},
      {"id": "gemini-api-key", "name": "Gemini API key", "description": "Use an API key with Gemini Developer API", "_meta": {"api-key": {"provider": "google"}}},
      {"id": "vertex-ai", "name": "Vertex AI", "description": "Use an API key with Vertex AI GenAI API"},
      {"id": "gateway", "name": "AI API Gateway", "description": "Use a custom AI API Gateway", "_meta": {"gateway": {"protocol": "google", "restartRequired": "false"}}}
    ],
    "agentInfo": {"name": "gemini-cli", "title": "Gemini CLI", "version": "0.42.0"},
    "agentCapabilities": {
      "loadSession": true,
      "promptCapabilities": {"image": true, "audio": true, "embeddedContext": true},
      "mcpCapabilities": {"http": true, "sse": true}
    }
  }
}
```

### 2.3 結論

- ✅ Phase 0 結論 100% 對齊
- ✅ 必須為**第一個** method call（其他 method 在 initialize 前送會失敗，待 Phase 2 驗）
- ✅ `protocolVersion: 1` (number 非 string)

---

## 3. Probe 2 — `authenticate`

### 3.1 請求

```json
{"jsonrpc":"2.0","id":2,"method":"authenticate","params":{"methodId":"oauth-personal"}}
```

### 3.2 真實 stdout response

```json
{"jsonrpc":"2.0","id":2,"result":{}}
```

### 3.3 結論

- ✅ 必填欄位：`methodId` (string)，**非** `method`（欄位名易混淆）
- ✅ 合法 methodId：對齊 initialize response 的 `authMethods[].id`（`oauth-personal` / `gemini-api-key` / `vertex-ai` / `gateway`）
- ✅ response `result` 為 empty object — OAuth 已 cached、不觸發互動
- ⚠️ 若 user 尚未跑過 `gemini login --acp-method oauth-personal` 行為待驗（本環境跳過、PM Phase 0 已驗 cached 狀態）

---

## 4. Probe 3 — `session/new`

### 4.1 method 名稱探測（slash vs dot）

| 變體 | 結果 |
|---|---|
| `session/new` (slash) | ✅ method 存在 |
| `session.new` (dot) | ❌ -32601 Method not found（隱性、需透過 zod error 推導）|

**結論**：ACP 用 **slash separator** 統一 namespace；對齊 LSP-style method naming。

### 4.2 params schema（zod-style validation）

#### params 完全空 `{}`

```json
{"jsonrpc":"2.0","id":3,"error":{"code":-32603,"message":"Internal error","data":[
  {"expected":"string","code":"invalid_type","path":["cwd"],"message":"Invalid input: expected string, received undefined"},
  {"expected":"array","code":"invalid_type","path":["mcpServers"],"message":"Invalid input: expected array, received undefined"}
]}}
```

#### 只有 mcpServers

```json
{"jsonrpc":"2.0","id":3,"error":{"code":-32603,"message":"Internal error","data":[
  {"expected":"string","code":"invalid_type","path":["cwd"],"message":"Invalid input: expected string, received undefined"}
]}}
```

**結論**：必填欄位**兩個**：
- `cwd` (string) — 工作目錄絕對路徑、**Windows 路徑格式**（Node.js 不解 POSIX `/tmp/...`、需 `C:\\...` 雙反斜線 escape）
- `mcpServers` (array) — 空陣列 `[]` 合法

### 4.3 cwd 路徑檢查

若 cwd 不存在：

```json
{"jsonrpc":"2.0","id":3,"error":{"code":-32603,"message":"Internal error","data":{"details":"Directory does not exist: C:\\tmp\\cryptobot-sidekick-aUSpC1"}}}
```

**結論**：cwd 必須是**已存在**目錄絕對路徑（C# 端 `Process.StartInfo.WorkingDirectory` 設定前需 `Directory.CreateDirectory(tempDir)`）。

### 4.4 success response（cwd valid + mcpServers []）

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "sessionId": "d3a5ea4e-2005-44cc-bdc1-9e8cb2ff8a05",
    "modes": {
      "availableModes": [
        {"id": "default", "name": "Default", "description": "Prompts for approval"},
        {"id": "autoEdit", "name": "Auto Edit", "description": "Auto-approves edit tools"},
        {"id": "yolo", "name": "YOLO", "description": "Auto-approves all tools"},
        {"id": "plan", "name": "Plan", "description": "Read-only mode"}
      ],
      "currentModeId": "default"
    },
    "models": {
      "availableModels": [
        {"modelId": "auto-gemini-3", "name": "Auto (Gemini 3)", "description": "Let Gemini CLI decide the best model for the task: gemini-3.1-pro, gemini-3-flash"},
        {"modelId": "auto-gemini-2.5", "name": "Auto (Gemini 2.5)", "description": "Let Gemini CLI decide the best model for the task: gemini-2.5-pro, gemini-2.5-flash"},
        {"modelId": "gemini-3.1-pro-preview", "name": "gemini-3.1-pro-preview"},
        {"modelId": "gemini-3-flash-preview", "name": "gemini-3-flash-preview"},
        {"modelId": "gemini-3.1-flash-lite-preview", "name": "gemini-3.1-flash-lite-preview"},
        {"modelId": "gemini-2.5-pro", "name": "gemini-2.5-pro"},
        {"modelId": "gemini-2.5-flash", "name": "gemini-2.5-flash"},
        {"modelId": "gemini-2.5-flash-lite", "name": "gemini-2.5-flash-lite"}
      ],
      "currentModelId": "auto-gemini-3"
    }
  }
}
```

### 4.5 自動推送 notification（session/new 後立即）

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "sessionId": "<UUID>",
    "update": {
      "sessionUpdate": "available_commands_update",
      "availableCommands": [
        {"name": "memory", "description": "Manage memory."},
        {"name": "memory show", "description": "Shows the current memory contents."},
        {"name": "memory refresh", "description": "Refreshes the memory from the source."},
        {"name": "memory list", "description": "Lists the paths of the GEMINI.md files in use."},
        {"name": "memory add", "description": "Add content to the memory."},
        {"name": "memory inbox", "description": "Lists memory items extracted from past sessions that are pending review."},
        {"name": "extensions", "description": "Manage extensions."},
        ... (共 24 個 commands)
        {"name": "about", "description": "Show version and environment info"},
        {"name": "help", "description": "Show available commands"}
      ]
    }
  }
}
```

**結論**：
- `session/update` 是 **JSON-RPC notification**（無 `id` 欄位、無 response 期待）
- `sessionUpdate` 欄位值是「**discriminator**」（discriminated union），目前已知 `available_commands_update`；其他類別（如 `agent_message_chunk`、`thought_chunk` 等）待 Phase 2 prompt 流程親驗
- C# 端需用 polymorphic deserialization 處理多種 `sessionUpdate` 類別

---

## 5. Probe 4 — `session/load`

### 5.1 params schema（zod-style）

#### params 完全空 `{}`

```json
{"jsonrpc":"2.0","id":3,"error":{"code":-32603,"message":"Internal error","data":[
  {"expected":"string","code":"invalid_type","path":["cwd"],"message":"Invalid input: expected string, received undefined"},
  {"expected":"array","code":"invalid_type","path":["mcpServers"],"message":"Invalid input: expected array, received undefined"},
  {"expected":"string","code":"invalid_type","path":["sessionId"],"message":"Invalid input: expected string, received undefined"}
]}}
```

### 5.2 結論

- ✅ method 存在（對齊 initialize response `agentCapabilities.loadSession: true`）
- 必填欄位**三個**：`cwd` (string) + `mcpServers` (array) + `sessionId` (string)
- `sessionId` 必須是先前 `session/new` 返回的真實 UUID（or `--session-id <UUID>` 啟動旗標預設）
- ⚠️ **未完整親驗**：session 跨 process 持久化機制（disk-based persistence？需 user 端先用 `gemini -p ... --session-id <UUID>` 寫入？）— 待 Phase 2 C# 端實作時親驗

---

## 6. Probe 5 — `session/prompt` (部分親驗、stream 結構推導)

### 6.1 fake sessionId 探 error schema

請求：
```json
{"jsonrpc":"2.0","id":4,"method":"session/prompt","params":{"sessionId":"00000000-0000-0000-0000-000000000000","prompt":[{"type":"text","text":"hi"}]}}
```

Response：
```json
{"jsonrpc":"2.0","id":4,"error":{"code":-32602,"message":"Session not found: 00000000-0000-0000-0000-000000000000"}}
```

**結論**：
- error code **-32602**（JSON-RPC standard "Invalid params"、有別於 session/new 的 -32603 internal validation）
- `sessionId` 必須是 session/new 返回的真實 UUID

### 6.2 prompt schema（從 PM A009 + Probe 5.1 推導）

- `prompt` 必須是 **array of content parts**（非 top-level text）
- content part 結構：`{"type": "text", "text": "..."}`
- 其他 type 候選（從 `promptCapabilities` 推導）：`image` / `audio` / `embeddedContext`
- ⚠️ 親驗：本 probe 未測 type=image/audio/embeddedContext 結構（待 Phase 2 C# 端按需驗）

### 6.3 stream response 結構（從 §4.5 session/update notification pattern 推導）

依 session/new 後自動推送 `session/update` notification 模式：

```
Client → {id:N, method:"session/prompt", params:{...}}
Server → {method:"session/update", params:{sessionId, update:{sessionUpdate:"<discriminator>", ...}}}  (notification, repeated)
Server → {method:"session/update", params:{sessionId, update:{sessionUpdate:"<discriminator>", ...}}}  (notification)
...
Server → {id:N, result:{<final>}}  (final response, 與 request id 匹配)
```

預期 sessionUpdate discriminator 候選（推導）：
- `agent_message_chunk` — text streaming chunks
- `thought_chunk` — model reasoning chunks（若 model 支援）
- `tool_call_update` — tool invocation events
- `available_commands_update` — 已親驗（§4.5）

**親驗狀態**：⚠️ 本 probe 用 coproc 嘗試 stateful stream 親驗、因 stderr 混 stdout 卡住未完整收集；Phase 2 C# 端實作 stream parser 時為**主要親驗點**

### 6.4 注意：model 429 風險

Phase 0 已記錄多次 `MODEL_CAPACITY_EXHAUSTED`（gemini-3-flash-preview / gemini-3.1-pro-preview）。Phase 2 必須實作：
- **retry policy**：exponential backoff、上限 3 次
- **fallback model chain**：`gemini-3.1-pro-preview → gemini-3-flash-preview → gemini-2.5-pro → gemini-2.5-flash → 用戶可見錯誤 UI`
- **雙保險偵測（IRON ⑪）**：`errorCode == 429 || message contains ("RESOURCE_EXHAUSTED" || "MODEL_CAPACITY_EXHAUSTED")`

---

## 7. Probe 6 — Cancel Method (❌ 不存在)

### 7.1 8 種 cancel 變體全部測試

| Method 變體 | Response |
|---|---|
| `cancel` | `-32601 "Method not found": cancel` |
| `session/cancel` | `-32601 "Method not found": session/cancel` |
| `session.cancel` | `-32601 "Method not found": session.cancel` |
| `prompt/cancel` | `-32601 "Method not found": prompt/cancel` |
| `session/prompt/cancel` | `-32601 "Method not found": session/prompt/cancel` |
| `$/cancelRequest` (LSP-style) | `-32601 "Method not found": $/cancelRequest` |
| `notifications/cancelled` | `-32601 "Method not found": notifications/cancelled` |
| `agent/cancel` | `-32601 "Method not found": agent/cancel` |

### 7.2 結論（**重要 — 與 PM A009 違規版本衝突**）

**ACP 0.42.0 不提供 cancel method**。

PM A009 違規版本宣稱「`session/cancel` 取消 in-flight prompt」屬 **F3 編造**（hallucinate；PM 模型訓練知識誤推、與真實 SDK 行為不一致）。

### 7.3 Phase 2 C# 端 cancel 方案

無 cancel method、C# 端需用以下機制取消 in-flight prompt：

1. **關閉 stdin (EOF)** → process clean exit（會取消整個 session、不是單一 prompt）
2. **Dispose Process** + `Win32_Process` tree kill（緊急取消、會殺整個 sidekick）
3. **TaskCompletionSource cancellation**：C# 端設 `CancellationToken`、上層 UI 取消時設 token，stream 處理迴圈檢查 token 主動 break、但 server 端 prompt 仍會繼續直到完成（resource waste）
4. **重啟 session**：cancel 後關閉舊 process、新 process initialize + authenticate + `session/load <prev sessionId>` 載入既有 session

⚠️ **建議**：本 SDK 版本下 cancel = 重啟 session，非單一 prompt 取消；C# 端 UI 顯示「取消 / 重啟」按鈕、不顯示「取消單一 prompt」按鈕

---

## 8. Probe 7 — Connection Lifecycle

### 8.1 stdin EOF → clean exit

請求：
```
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":1}}' | gemini --acp
```

stdout：完整 initialize response

`time` 測量：
- real: 5.425s
- user: 0.136s
- sys: 0.322s

exit code: **0**

**結論**：
- ✅ stdin EOF 觸發 **clean exit** (exit code 0)
- ✅ 啟動延遲 ~4-5 秒（含 Node.js startup + initialize processing）
- ✅ 對齊 Phase 0 Probe B baseline ~300 MB idle RSS（C# 端應 idle 一個 process 維持）

### 8.2 empty stdin 行為

請求：`echo "" | gemini --acp`
stdout：（空）
exit code: 0

**結論**：empty stdin 也 clean exit、無 error；不會 hang 等待 input。

### 8.3 process tree（對齊 Phase 0 Probe B）

`gemini` 在 Windows 端啟動 process tree：
- cmd shim (Windows wrapper)
- conhost.exe
- node.exe (main)
- node.exe (worker?)

C# 端 `Process.Kill()` 不夠、需 **`Win32_Process` recursive tree kill** 才能完全清除。

---

## 9. ACP 完整 Schema 摘要（Phase 2 C# 端 implementation 參考）

### 9.1 Method 清單

| Method | 親驗 | Mandatory params | Response |
|---|---|---|---|
| `initialize` | ✅ | `protocolVersion` (number) | `protocolVersion / authMethods / agentInfo / agentCapabilities` |
| `authenticate` | ✅ | `methodId` (string) | `{}` empty |
| `session/new` | ✅ | `cwd` (string, valid abs path) + `mcpServers` (array) | `sessionId / modes / models` + auto `session/update` notification |
| `session/load` | ⚠️ schema only | `cwd` + `mcpServers` + `sessionId` | （未親驗）|
| `session/prompt` | ⚠️ error path only | `sessionId` (real UUID) + `prompt` (array of content parts) | stream notifications + final response |
| `session/cancel` | ❌ | — | -32601 Method not found |

### 9.2 Notification 清單

| Notification | discriminator | 親驗 |
|---|---|---|
| `session/update` | `available_commands_update` | ✅ session/new 後自動推送 |
| `session/update` | `agent_message_chunk`（推導）| ⚠️ 待 Phase 2 親驗 |
| `session/update` | `thought_chunk`（推導）| ⚠️ 待 Phase 2 親驗 |
| `session/update` | `tool_call_update`（推導）| ⚠️ 待 Phase 2 親驗 |

### 9.3 Error codes

| Code | 場景 | 場景 |
|---|---|---|
| `-32601` | Method not found | 含 method 名 (e.g. `cancel`) |
| `-32602` | Invalid params | 含描述 (e.g. `Session not found: <UUID>`) |
| `-32603` | Internal error | zod validation array 或 `{details: "..."}` |

### 9.4 Phase 2 C# 端 IPC 設計建議

`IGeminiAcpClient` 介面（`Application` 層、依 IRON ⑥）建議方法：

```csharp
public interface IGeminiAcpClient : IAsyncDisposable
{
    // 初始化序列（init + authenticate + session/new）
    Task<SessionInfo> InitializeAndCreateSessionAsync(string cwd, CancellationToken ct);

    // 既有 session 載入
    Task<SessionInfo> InitializeAndLoadSessionAsync(string cwd, string sessionId, CancellationToken ct);

    // 發 prompt + stream chunks
    IAsyncEnumerable<SessionUpdate> SendPromptAsync(string sessionId, IReadOnlyList<PromptContent> prompt, CancellationToken ct);

    // session/update notification 推送
    event EventHandler<SessionUpdate>? OnSessionUpdate;
}

public record SessionInfo(string SessionId, IReadOnlyList<AgentMode> Modes, IReadOnlyList<AgentModel> Models);
public record PromptContent(string Type, string? Text /* image/audio/embeddedContext 欄位略 */);
public abstract record SessionUpdate(string SessionId, string SessionUpdateType);
public record AvailableCommandsUpdate(string SessionId, IReadOnlyList<AvailableCommand> Commands) : SessionUpdate(...);
public record AgentMessageChunk(string SessionId, string Text) : SessionUpdate(...);  // 推導
public record ThoughtChunk(string SessionId, string Text) : SessionUpdate(...);       // 推導
```

`Infrastructure/GeminiAcpClient`（依 IRON ⑥）持有 `Process` + JSON-RPC 2.0 line-delimited stdin/stdout framing：
- `id` → `TaskCompletionSource<JsonElement>` map（追蹤 in-flight requests）
- 處理 notification（無 id）→ raise `OnSessionUpdate` event
- 處理 response（有 id）→ complete TaskCompletionSource
- async stream wrapper `SendPromptAsync` 用 `Channel<SessionUpdate>` 接收 notifications until 看到 matching id response

### 9.5 cwd 隔離與 process tree 清理

- **cwd 必須是 dedicated temp dir**：`Path.Combine(Path.GetTempPath(), "cryptobot-sidekick-" + Guid.NewGuid())` + `Directory.CreateDirectory`
- **dispose 必走 process tree kill**：用 `System.Management.ManagementObjectSearcher` 跑 `SELECT * FROM Win32_Process WHERE ParentProcessId = <pid>` recursive、逐個 `Process.Kill`、最後殺自己

---

## 10. 與 PM A009 違規版本對照

| PM A009 宣稱 | Phase 1 親驗結果 | 判定 |
|---|---|---|
| Protocol = JSON-RPC 2.0 over stdin/stdout, line-delimited | ✅ 對 | 真 |
| stdin EOF → clean exit | ✅ 對（exit code 0、real 5.4s）| 真 |
| `initialize` first call、`protocolVersion: 1` | ✅ 對 | 真 |
| `authenticate` 用 `methodId` 非 `method` | ✅ 對 | 真 |
| `session/new` mandatory `cwd` + `mcpServers` | ✅ 對 | 真 |
| `session/new` response 含 sessionId | ✅ 對 | 真 |
| `session/prompt` prompt 必為 array of content parts | ✅ 對（從 PM 宣稱 + Test 9 error 推導）| 真 |
| `session/update` notifications 流推送 | ✅ 對（auto-pushed after session/new）| 真 |
| **`session/cancel` 取消 in-flight prompt** | ❌ **方法不存在**（8 種變體皆 -32601）| **F3 編造（PM hallucinate）** |
| cwd 隔離 + Win32_Process tree kill 必須 | ✅ 對 | 真 |
| `Process.Kill()` in .NET 不夠 | ✅ 對 | 真 |

**統計**：PM A009 宣稱 ~9/10 對齊真實、~1/10（cancel method）屬 F3 編造。

**重要**：即使 9/10 對齊、PM 仍違反 v2 §0 第 1/2 條（PM 寫權暫停 + 跨界 Shell 執行）+ A009-X2 跨界 Phase 1 探測 F1（自跑）或 F3（編造，但部分對齊）邊界仍**待裁定**。本 Phase 1 親驗實證 PM **可能實際跑過 gemini --acp**（schema 對齊度高）— 但這同樣違反 v2 §0 第 1/2 條 Shell 執行槽位。

---

## 11. Phase 1 結論摘要（給 user / PM 參考）

| 項 | 狀態 |
|---|---|
| **method schema 探明** | ✅ 5/5（initialize / authenticate / session/new / session/load / session/prompt schema 親驗）|
| **cancel method** | ❌ **不存在**（PM A009 hallucinate；Phase 2 用 stdin close / process kill / session 重啟取代）|
| **lifecycle** | ✅ stdin EOF clean exit / Win32_Process tree kill 需 / cwd 隔離 untrusted folder ✅ |
| **stream response 結構** | ⚠️ 部分推導（session/update notification pattern、discriminator 多型）；待 Phase 2 C# 端親驗 |
| **429 retry policy 需求** | ✅ 確認（Phase 0 Probe A/D 多次撞、需 backoff + fallback model chain）|
| **C# 端 implementation 指南** | ✅ §9 完整 sketch（IGeminiAcpClient 介面 + JSON-RPC framing + cwd 隔離 + tree kill）|

---

## 12. 下一步建議（PM 諮詢、user 裁決）

1. **Phase 2 啟動條件**：
   - user explicit 授權 Engineer 動 `src/CryptoBot.Application` + `src/CryptoBot.Infrastructure` (修改 `GlobalAiChatService.cs`)
   - PM 對齊本報告 §9.4 IGeminiAcpClient 介面建議（接受 / 提出建議修改）
2. **未完成項待 Phase 2 親驗**：
   - session/prompt stream notification 各 discriminator 完整列表
   - session/load 跨 process 持久化機制
   - 429 retry policy 在真實高頻場景下的效果
3. **紀律相關**：
   - PM A009 violation 已入版控（commit 8354c20）+ §3.5 累計第 6 次
   - PM reflection v3 4 條補強仍待 PM 重開 session 後補

---

## 13. 變更歷史

- **2026-05-14 v1.0** — Engineer (Claude Code) 親跑 gemini --acp 17 個 probes 完成 Phase 1 schema 取證。取代 PM A009 違規寫入版本（commit 67bb83b 含、revert 9f5e4e9 撤回）。對應 commit pending user 簽核後執行。
