# Engineer Draft: [S75] Phase 0 Probe Report + Capsule 立案 Audit Trail

> **位階**：Engineer 端暫存（drafts）— 對齊 `~/.agentcharter/core/working-stack-discipline.md §2`。**非 capsule、非 HANDOFF**。
> **存檔時點**：2026-05-13 Phase 0 probe 完成 + PM capsule 草案 5.5/6 抽驗合格、Engineer 整合中。
> **平行檔**：`agent-commons/capsules/TASK_S75_SIDEKICK_HUB.md`（本 drafts 為其 audit trail）。

---

## 1. user 原始需求 (verbatim, 2026-05-13)

> 「我希望可以從網頁那邊點擊按鈕之後，不論是我給她 prompt 還是怎樣，他都可以像我用 cmd 這樣的對話，不是一直重新 reload，也不考慮使用 api 的方式，因為這樣太花錢了，不如寫一個 cmd 或其他方式當一個介接層即可」

Engineer 技術翻譯（drafts §6 GlobalAiChatService.cs 取證後）：
- 網頁觸發點：Blazor UI 既有 Sidekick 全域側邊欄（S74-C）
- 「像 cmd 對話 / 不 reload」：用 `gemini --acp` 持續長連接 IPC，取代 `gemini -p single-shot`
- 「不考慮 API、太花錢」：用本機 Gemini CLI 走 `oauth-personal` 免費 quota，**禁** Gemini SaaS API（`gemini-api-key` / `vertex-ai` / `gateway` auth method）
- 「寫一個 cmd 當介接層」：`gemini` CLI 子 process 即為介接層，**不引入** Python / FastAPI / 新 port（與 [S69] 邊界區隔）

---

## 2. Phase 0 Probe 完整結論（4/4）

### 2.1 Probe A — Session 持久化驗證

**指令序列**：
```powershell
$SESSION = [guid]::NewGuid().ToString()
gemini -p "請記住這個測試代碼：CRYPTOBOT-S75-PROBE-A-2026" --session-id $SESSION
gemini --list-sessions | Select -First 20
gemini -p "我剛才告訴你的測試代碼是什麼？" --resume $SESSION
```

**真實 stdout 摘要**（IRON ⑫ 寫真單）：
- Step 1：兩次 `429 RateLimitExceeded` `gemini-3-flash-preview MODEL_CAPACITY_EXHAUSTED` retry 後成功；Gemini 用「致 PM / 致 User」格式 reply（auto-load `GEMINI.md` 進 PM 角色）
- Step 2：`--list-sessions` 列 23 個 session，**自訂 GUID `bc89511a-...` 不存在**；最新 session 仍是 `01ea45c6-...`（3 hours ago）
- Step 3：reply 提到測試碼但實為 cwd context 或 history file read（非真正跨-p call in-memory persistence）

**結論**：
- ❌ `--session-id <自訂 GUID>` client-side only，不註冊到 Gemini 內部 session store
- 🚨 cwd 內 `GEMINI.md` + `agent-commons/` auto-load 進 PM 角色 → Sidekick **必須隔離 cwd**
- ⚠️ `gemini-3-flash-preview` 429 重複 → 需 retry + fallback model 策略

### 2.2 Probe B — RSS Idle Baseline

**指令**（cmd shim + Win32_Process descendants）：
```powershell
$proc = Start-Process cmd '/c gemini --acp --approval-mode plan' -PassThru -WindowStyle Hidden
# Get-CimInstance Win32_Process -Filter ParentProcessId=$proc.Id (recursive)
```

**真實 stdout**：
| 時點 | total RSS | 細節 |
|---|---|---|
| T+3s | 344.64 MB | conhost 10 + node 146 + node 188 |
| T+15s | 300.75 MB | conhost 10 + node 128 + node 162 |
| T+30s | 300.69 MB | conhost 10 + node 128 + node 162 |

**結論**：
- ✅ idle baseline **~300 MB**（T+15s 起穩定）
- ✅ 無 memory leak（T+15s → T+30s 0.06 MB 變動 = 雜訊）
- ⚠️ Process tree = **cmd shim + conhost + 2 node.exe**（4 個 process）→ Sidekick kill 必須走 process tree

### 2.3 Probe C — ACP JSON-RPC 通訊格式

**handshake 探測序列**：
```bash
# 試 4 個 method
for m in initialize agent.initialize handshake tools/list; do
  echo "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"$m\"}" | timeout 6 gemini --acp
done
# initialize 揭示 params 需 protocolVersion (number)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":1}}' | timeout 6 gemini --acp
```

**真實 stdout（initialize 成功 response）**：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": 1,
    "authMethods": [
      {"id": "oauth-personal", "name": "Log in with Google", ...},
      {"id": "gemini-api-key", "name": "Gemini API key", ...},
      {"id": "vertex-ai", "name": "Vertex AI", ...},
      {"id": "gateway", "name": "AI API Gateway", ...}
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

**結論**：
- 🎉 ACP **JSON-RPC 2.0 完整可行**（exit 0、結構化 error/result）
- ✅ method 名是 `initialize`（LSP 慣例）+ `protocolVersion: 1` (number 非 string)
- ✅ `agentCapabilities.loadSession: true` — Sidekick 持久化原生支援
- ✅ `authMethods` 含 `oauth-personal` — user 免 API key 路徑成立
- ⚠️ method `agent.initialize` / `handshake` / `tools/list` 均不存在（-32601）
- ⏳ `prompt` / `session.new` / `session.load` 等 method schema 待 Phase 1 探

### 2.4 Probe D — `--approval-mode plan` 鎖死驗證

**指令**：
```bash
gemini -p "請在當前目錄新建一個檔案 PHASE0_PROBE_D.txt 寫入 hello" --approval-mode plan
ls PHASE0_PROBE_D.txt  # 預期 not found
```

**真實 stdout**：
- pre-state: `PHASE0_PROBE_D.txt` not found
- gemini call: `429 RateLimitExceeded gemini-3.1-pro-preview MODEL_CAPACITY_EXHAUSTED`（不同 model 也滿）
- post-state: `PHASE0_PROBE_D.txt` not found

**結論**：
- ⚠️ 因 model 429 中斷無法 confirm plan mode 鎖死真實性（LLM 沒機會呼叫 write tool）
- ⏭️ Sidekick 不需要 plan mode（自由對話、不限 LLM tool execution）→ 本 probe 略過影響

---

## 3. PM Capsule 草案 verbatim（IRON ⑫ 永久 audit trail）

PM 於 2026-05-13 透過諮詢通道提供以下 6 段建議內容（用「建議 / 請求」語式、紀律合規）：

```
1. 目標 (Goal)
建議將目標定義為：「建立一個單一實例、長效運作且具備 429 韌性的 Sidekick 服務中樞，
透過 ACP (Agent Commons Protocol) 實現與 C# 端穩定 IPC，
解決當前對話冷啟動延遲並確保 CWD 環境隔離。」

2. 範圍 (Scope)
 In-scope:
   - 重構 GlobalAiChatService.cs 以支援基於 ACP 的 IPC 機制
   - 實作側邊代理（Sidekick）的進程管理與樹狀結構維護
   - 實作 cwd 隔離邏輯
   - 針對 429 (Rate Limit) 錯誤實作退避重試（Retry with Backoff）機制
 Out-of-scope:
   - [S69] Python Sidecar 優化邏輯本身
   - 任何需要 SaaS API 金鑰之外的私有部署（如在地化 LLM）
   - Gemini CLI 的 plan mode 行為修改

3. 階段 (Phasing)
 Phase 1：探測 Prompt 語意、定義 ACP Method Schema 與 Session 管理合約
 Phase 2：重構 C# 端 GlobalAiChatService 之 IPC 傳輸層
 Phase 3：核心加固：429 Retry、CWD 隔離、進程樹管理安全鎖
 Phase 4：整合測試與 VCP 對齊

4. 風險 (Risks)
 已知：cwd 環境汙染、頻繁調用引發 429 阻斷、孤兒進程資源洩漏
 未知：ACP Method Schema 在複雜長對話下的解析穩定性、SemaphoreSlim 死鎖風險

5. 驗收條件 (Acceptance)
 - UI 5 輪以上無冷啟動延遲感
 - Idle RSS 穩定於 ~300 MB 以下
 - 429 重試 log 可見、對話不中斷
 - 1 instance / 0 殘留進程 / 0 警告 0 錯誤
 - 既有 227 項測試全綠

6. 依賴 (Dependencies)
 [S72] 同步邏輯加固平級優先；S75 避免在 S72 完成前進行 Domain 層侵入性修改
```

---

## 4. Engineer 抽驗結果 + 修正紀錄

PM 6 段內容 **5.5/6 合格** — A007 整改後首次合格回應、大幅進步。兩處 F4 小錯由 Engineer 在 capsule 寫入時順手修：

| # | 段 | PM 原文 | Engineer 修正 | 修正理由 |
|---|---|---|---|---|
| 1 | §1 Goal | 「ACP (Agent **Commons** Protocol)」 | 「ACP（gemini-cli Agent Client Protocol mode）」 | F4：gemini-cli 內 ACP 是 Agent Client Protocol，PM 與本專案 `agent-commons/` 目錄名混淆 |
| 2 | §2 Scope Out | 「任何需要 SaaS API 金鑰**之外**的私有部署（如在地化 LLM）」 | 「Gemini SaaS API 路徑（`gemini-api-key` / `vertex-ai` / `gateway` auth methods）— user 明示成本考量、不採用」 | F4：原措辭邏輯反、且未對齊 Phase 0 取證的 4 個 authMethods |

其餘 5 段（Phasing / Risks / Acceptance / Dependencies + Goal 主旨 + Scope in-scope）100% 對齊 Phase 0 取證 + user 需求 + 紀律遵循。

---

## 5. 整合後 capsule 寫入路徑

Engineer 整合後寫入 `agent-commons/capsules/TASK_S75_SIDEKICK_HUB.md`，對齊既有 capsule format（5 段 + 加 §6 Acceptance + §7 Dependencies）：

| Capsule 段 | 內容來源 |
|---|---|
| §1 任務背景 (Context) | user 需求 verbatim + Phase 0 取證關鍵發現 |
| §2 目標 (Goals) | PM Goal（修正後） + checkbox 子目標 |
| §3 關鍵路徑 (Critical Path) | PM Phasing 4 階段（檔案級指引）|
| §4 鐵律遵循 (IRON Protocol) | IRON ⑥ / ⑩ / ⑫ 對 S75 的具體要求 |
| §5 資源引用 (References) | `GlobalAiChatService.cs` / `DashboardEventBus.cs` / Phase 0 probe artifacts |
| §6 驗收條件 (Acceptance) | PM Acceptance 5 指標（grounded 於 Phase 0 取證 + 既有 227 tests）|
| §7 依賴與風險 (Risks & Dependencies) | PM Risks + Dependencies + cwd 隔離 / 429 / process tree 三大已知 |

---

## 6. 變更歷史

- **2026-05-13** — 初版。涵蓋 Phase 0 Probe (A/B/C/D) 完整結論 + user 需求 verbatim + PM capsule 草案 verbatim + Engineer 抽驗修正紀錄 + 整合 capsule 寫入路徑。對應 commit pending 至 user 簽核後執行。
