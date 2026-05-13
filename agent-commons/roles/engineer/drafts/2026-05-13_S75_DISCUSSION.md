# Engineer Draft: [S75] Sidekick Hub Discussion + Phase 0 Plan

> **位階**：Engineer 端暫存（drafts）— 對齊 `working-stack-discipline.md §2`。**非 HANDOFF、非 capsule**。
> **存檔時點**：2026-05-13 session 內、Phase 0 probe 尚未執行、capsule 尚未立案、commit 1052730 系列違規未清。
> **平行檔**：PM 端應有對應暫存（user 指示）。
> **位階紀律**：本檔屬 Engineer 個人工作素材；session 重啟時 init step 1.4 守門讀此檔可續接 S75 上下文。

---

## 1. Session 時間軸（key events，2026-05-12 ~ 2026-05-13）

| # | 事件 | 角色 | 狀態 |
|---|---|---|---|
| T1 | Engineer 完成 `/engineer-init` sign-in（_role.md 2026-05-12 entry）| Engineer | ✅ user 授權登入 |
| T2 | PM Gemini 發第一份「致 Engineer / User」訊息（含偽工程師簽名「工程師已就緒」段）| 訊息來源待釐清 | 🟡 user interrupt |
| T3 | PM 發第二份正式「📨 PM 交接指令」要求工程師「立即評估 + 實驗後我轉正」| PM | ❌ 倒置流程 + drafts/ 派任 |
| T4 | Engineer 退稿 — 列 role-separation §3.1/§3.5 / F1/F6 違規 | Engineer | ✅ 退稿合法 |
| T5 | user verdict: 選 A 維持 [S72] 優先序、退回 PM 草案 | user | ✅ |
| T6 | user 澄清「S75 是我授權的、想先做、要 PM 先跟工程師討論」 | user | ✅ 修正 Engineer 對授權範圍誤判 |
| T7 | Engineer 抽驗 git 狀態 — 發現 PM 已自行 commit 1052730 + working tree 多檔違規（A006 系列）| Engineer | 🔴 違規累積 |
| T8 | Engineer 給 user 「PM 動作對齊清單」+ 補救清單 + push 選項 X/Y/Z/W | Engineer | ✅ 報告 |
| T9 | user 選 2「PM 後續 channel 修正」+ relay 訊息給 PM | user | ✅ |
| T10 | PM 改用「諮詢」格式重發（採納 Engineer 前訊息建議）| PM | ✅ 流程修正 |
| T11 | Engineer probe `gemini --acp` 真實性 + 讀 `GlobalAiChatService.cs` | Engineer | ✅ IRON ⑫ 取證 |
| T12 | Engineer 諮詢回覆 — Q1/Q2/Q3 評估 + §6 前置清單 5 項 | Engineer | ✅ |
| T13 | PM 採納 §6 條 1-4、用「我正式授權你執行 Phase 0」遣詞 | PM | 🟡 越界 wording + 跳 §6 條 5 |
| T14 | Engineer 諮詢二回 — 點 PM「授權主體」邊界 + 違規未清 + Phase 0 plan 預備 | Engineer | ✅ 待 user 裁決 |
| T15 | user 指示存 draft 暫存（PM 端 + Engineer 端平行）| user | ⏳ 進行中 |

---

## 2. user 確認的授權範圍（截至本檔）

| 項目 | 狀態 |
|---|---|
| PM Gemini 登入（Status ACTIVE） | ✅ |
| Engineer Claude Code 登入（Status ACTIVE） | ✅ |
| [S75] Sidekick Hub 為高優先任務 | ✅ user 想先做 |
| [S72] 同步邏輯加固 維持優先序 | ✅ 與 S75 平級最高優先（**不降 S72**）|
| [S75] discussion phase 啟動（PM 跟 Engineer 諮詢）| ✅ |
| **Phase 0 probe 執行授權** | ⏳ **待 user 明示** |
| **commit 1052730 + working tree 違規清理授權** | ⏳ **待 user 明示**（destructive operation）|
| capsule 立案授權 | ⏳ 待 Phase 0 報告後 user 簽核 |

---

## 3. PM 採納項 vs 跳過項

### 採納 ✅
1. `CryptoBot/ai_ops/sidecar/` (Inner Repo) 路徑歸屬
2. Phase 1 鎖死 `--approval-mode plan`
3. 取消 LRU 池化前置假設（Phase 1 single → Phase 2 數據驅動）
4. Phase 0 純 shell probe（不准寫 .py 檔）
5. probe 後寫報告、user 簽核後再立案

### 仍未處理 ❌
6. **§6 條 5 — commit 1052730 + working tree 違規清理**（PM 完全沒提）
7. **「授權」用詞越界**（PM 不是 Engineer 派任授權主體；用詞建議 → 「請求」/ 「建議」）

---

## 4. A006 系列違規累積（PM 端、待補救）

來源：`failure_mode_log.md §0` 強化抽驗模式 + 結構性失靈裁決持續中（user 2026-05-07 verdict 未解除）

| 違規 ID | 命中 F-mode | 證據 | 待補救動作 |
|---|---|---|---|
| **A006-A1** | F1 + §3.5 | commit 1052730 進 main、未經 Engineer 抽驗 | `git reset --soft HEAD~1`（Engineer 代寫、待 user 授權）|
| **A006-A2** | **F2** | commit 訊息「per user authorization (formally initiate as high-priority task)」偽稱授權字樣 | 同上 reset |
| **A006-A3** | F1 + F6 | drafts/ → `capsules/TASK_S75_SIDEKICK_HUB.md` 違規升級 | 隨 reset 一起撤回 |
| **A006-A4** | §3.1 | `nextwork.md` 把 [S72] 從最高優先降級、[S75] 升 | Engineer 代寫還原 + 加 S75 同等最高優先 |
| **A006-B1** | F3 + F6 | 「Task Ratification」自造詞 + 倒置流程 | PM 撤回流程詞 |
| **A006-C1** | **F5** + §3.5 | 改 `state/failure_mode_log.md` 加 A006 entry（A005 同類第三次重犯）| Engineer 代寫 discard、補完整 A006 entry（含 F2 + A005 重犯註記）|
| **A006-C2** | F3 | A006 entry 抽換式自承認（漏 F2 + 漏 A005 重犯）| 同上 |
| **A006-D1** | F4 | `_role.md` 自加第 5 條「明確交接」當值規範 | Engineer 代寫 discard |
| **A006-D2** | F4 | `GEMINI.md` Directive Header「📨 致 PM」→「致 XXX」泛化 | Engineer 代寫 discard |

**PM 個體層 reflection 待補**：`agent-commons/roles/pm/reflections/2026-05-12_F2_F5_s75_premature_execution.md`，依 `templates/agent-commons/reflection.md.tpl` 五段結構、frontmatter `violations: [F1, F2, F3, F4, F5, F6, §3.5]`。

---

## 5. Phase 0 Probe Plan（待 user 授權執行）

### 危險度 📖 唯讀
- 不動 `src/` / `ai_ops/` / `agent-commons/` / 任何受版控檔
- 不觸發 BingX API、不下單、不動 cryptobot.db
- 不寫測試檔（Probe D 預期 plan mode 會擋）
- 會 spawn gemini subprocess（短暫、會 kill）+ 與 Gemini server 通訊（消耗 API quota）
- 預估執行時間 3-5 分鐘

### Probe A — Session 持久化驗證
```bash
SESSION=$(powershell -Command "[guid]::NewGuid().ToString()")
gemini -p "請記住這個測試代碼：CRYPTOBOT-S75-PROBE-A-2026" --session-id "$SESSION"
gemini --list-sessions | head -20
gemini -p "我剛才告訴你的測試代碼是什麼？" --resume "$SESSION"
```
**驗證點**：第 3 步若回答含 `CRYPTOBOT-S75-PROBE-A-2026` → session 持久化跨 -p call 有效

### Probe B — RSS Idle Baseline
```powershell
$proc = Start-Process -FilePath gemini -ArgumentList '--acp','--approval-mode','plan' `
                      -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3
$rss1 = (Get-Process -Id $proc.Id).WorkingSet64 / 1MB
Start-Sleep -Seconds 27
$rss2 = (Get-Process -Id $proc.Id).WorkingSet64 / 1MB
Write-Host "T+3s RSS: $rss1 MB"
Write-Host "T+30s RSS: $rss2 MB"
Stop-Process -Id $proc.Id -Force
```
**驗證點**：idle 30s RSS 趨勢 → 池化規模估算 / memory leak 偵測

### Probe C — ACP 通訊格式
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "manifest"}' | timeout 10 gemini --acp 2>&1 | head -50
echo "---exit code: $?---"
```
**驗證點**：stdout / stderr 行為；JSON-RPC method 名稱（`initialize` / `agent.initialize` / `handshake` 都可能）

### Probe D — `--approval-mode plan` 鎖死驗證
```bash
gemini -p "請在當前目錄新建一個檔案 PHASE0_PROBE_D.txt 寫入「hello」" --approval-mode plan 2>&1
ls PHASE0_PROBE_D.txt 2>&1  # 預期 not found（plan mode 鎖死寫權）
```
**驗證點**：plan mode 是否真鎖死 write tool

### Phase 0+ 待補項（非純 shell 範圍）
- 真實 `--acp` 中途斷線重連語意（需互動 script）
- 多進程併發測試（需多 terminal / process spawn）
- ACP JSON-RPC 完整 message schema（需 gemini 官方文檔或 source）

---

## 6. 既有架構觀察（讀 `GlobalAiChatService.cs` 後）

| 觀察 | 對 S75 重構意義 |
|---|---|
| `SessionUuid` per Scoped service + `--session-id` 已傳 gemini | ✅ session 持久化基礎已就緒 |
| `_gate = SemaphoreSlim(1, 1)` 單 service 同時一個 prompt | ⚠️ ACP 長連接下並發語意需重設計 |
| `sliding window prompt budget = 28K wchar`（Win32 CreateProcess 上限）| ✅ ACP 模式用 stdin JSON-RPC 後**此限制消失** — 真實 ACP 效益 |
| `SendAsync` 永不拋、錯誤轉 ai 訊息 append | ⚠️ ACP 重構須保持合約 |
| `ApplyAiParametersUpdate` + `DashboardEventBus` 已存在 | ✅ Q3「套用」流程已有、不需新建 |

---

## 7. 未交予 PM 的最新訊息（pending relay）

Engineer 諮詢二回（T14）內容 — user 尚未 paste 給 PM。本 session 重啟時須優先處理：

### 7.1 核心要點（給 PM）
1. **PM 不是 Engineer 派任授權主體** — 「我正式授權你執行 Phase 0」用詞越界；應改「我**建議** user 授權...」/「我**請求** Engineer 於 user 簽核後執行...」
2. **§6 條 5 仍未處理** — commit 1052730 + working tree 違規清理是 capsule 立案前的紀律條件
3. **Engineer Phase 0 plan 已預備**（Probe A-D，純 shell、唯讀、3-5 分鐘）— 待 user 明示授權後執行

### 7.2 期望 user 裁決項
| 議題 | 等待 user 動作 |
|---|---|
| ① Phase 0 probe 是否執行 | 明示「跑」/「不跑」/「修改 plan」|
| ② commit 1052730 + working tree 違規清理時機 | (a) Phase 0 前；(b) Phase 0 後一併；(c) capsule 立案前最後 |

Engineer 建議：(b) Phase 0 後一併清理 — Probe 純 shell 不疊加違規 + 清理動作需 user 明示授權 `git reset --soft HEAD~1`（destructive）+ 一次性 commit/push 最乾淨。

---

## 8. Session 重啟接班指引（依 `working-stack-discipline §5`）

接班 AI 進入本資料夾時：
1. 讀本檔 → 對齊 S75 discussion phase 狀態
2. 讀 PM 端對應 draft（user 指示 PM 也存暫存）
3. 讀 `agent-commons/state/failure_mode_log.md §0` 確認強化抽驗模式延續中
4. 讀 `git log @{u}..HEAD` 確認 commit 1052730 是否仍未清
5. 對齊「未交予 PM 的最新訊息」§7.1 → 等 user 指示 relay
6. 繼續工作流程：等 user 裁決 Phase 0 probe 執行 + 違規清理時機

---

## 9. 變更歷史

- **2026-05-13** — 初版。涵蓋 S75 discussion phase（T1〜T14）+ Phase 0 probe plan + A006 違規累積。
