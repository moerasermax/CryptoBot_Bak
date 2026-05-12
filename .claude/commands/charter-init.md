# /charter-init — AgentCharter 接入流程（Claude Code 具象化）

> **位置**：`.claude/commands/charter-init.md`
> **依據**：`~/.agentcharter/tools/init-spec.md` + `~/.agentcharter/core/init-template.md §3.3`
> **具象化日期**：2026-05-04（charter v0.9.9）
> **引用路徑紀律**（v0.7.0）：本檔使用 `~/.agentcharter/` 相對 user home，不寫死絕對路徑

## 用法

```
/charter-init
/charter-init standard
```

---

## 執行流程

### Phase 0 — 互動式收集參數（無參數時觸發）

若未帶參數，**先問齊再跑**，一次問完：

```
請提供以下資訊，我收到後直接跑完接入流程：

1. preset（standard / minimal / strict / essential — 不確定選 standard）
2. 領域公理路徑（以下擇一）：
   a. 路徑 A：我自己寫好了，路徑是 protocols/<檔名>.md
   b. 路徑 B：讓 AI 讀 codebase 幫我起草，我再校正（如有既有協議請告知路徑）
3. 有沒有既有協議 / 鐵律文件需要遷移？若有，請提供路徑
```

收到回答後，帶著這三個值跑 Phase 1-5b，不再中途問人。

### Phase 1 — 前置檢查

1. 確認 `~/.agentcharter/` 存在（框架層）
   - 不存在 → 停止：`git clone https://github.com/moerasermax/AgentCharter ~/.agentcharter`
2. 確認 `agent-commons/_config/` 是否存在
   - 已存在且有 profile.yaml → 警告「已 init 過，charter_version: <X>」
     詢問 user：跳過 / 重新 init
   - 不存在 → 繼續建立

### Phase 2 — 產生 profile.yaml

1. 讀 `~/.agentcharter/tools/profiles/<preset>.yaml` 模板
2. 讀當前 charter 版本（`~/.agentcharter/CHANGELOG.md` 首行）
3. 詢問 user：domain_axioms.primary 路徑（相對 agent-commons/）
   - 若 agent-commons/protocols/ 已有 .md 檔 → 列出，user 確認
4. 寫 `agent-commons/_config/profile.yaml`
   - 確保 `parameters.failure-modes.enable_modes` 含 F6

### Phase 3 — 產生 mapping.yaml

1. 依 `~/.agentcharter/core/charter-config.md §3` schema 填預設值
2. ⚠️ **紀律**：`shared.*` 是 schema namespace，路徑值直接寫頂層（不含 shared/ 中介層）
3. 寫 `agent-commons/_config/mapping.yaml`
   - 必含：`common_memory_root` + `shared.draft_context`

### Phase 3.5 — 建立 agent-commons scaffold

idempotent（已存在則跳過）：
- `handoffs/` `handoffs/archive/` `capsules/` `institutional-memory/`
- `state/` `state/failure_mode_log.md`（空檔 + frontmatter）
- `nextwork.md` `DRAFT_CONTEXT.md`（空檔）
- `protocols/`（若不存在）
- `roles/pm/` `roles/engineer/`（含 sessions/ drafts/ reflections/ private/）

偵測現有 AI 工作產物（Step 8）：
- 掃根目錄 / docs/ 內有 *-sync-point-*.md / checkpoint_*.md / S\d+-*.md
- 若命中 → 提示「偵測到既有 AI 協作產物，建議執行 /charter-doctor --fix 進行 Gap 遷移」
- ⚠️ 僅提示、不自動遷移

### Phase 4 — 建立角色 _role.md

依 `~/.agentcharter/templates/agent-commons/_role.md.tpl`：
- `roles/pm/_role.md`（Status: PROVISIONAL，全 AI 標 ❌）
- `roles/engineer/_role.md`（Status: PROVISIONAL，全 AI 標 ❌）
- **不自動生成任何 AI 的 slash command**（框架不代生成）

### Phase 5 — /charter-doctor 健康檢查

依 `~/.agentcharter/tools/doctor-spec.md` 模式 A 全量：
- §3.1 結構完整性 + §3.2 條款相依 + §3.3 路徑對映
- §3.5 領域公理（存在 + USER-RATIFIED）
- §3.7 頂層完整性 + namespace 校驗 + F6 啟用
- §3.9 axiom frontmatter 紀律
- §3.11 個體學習迴圈合規

**0 errors 才繼續；有 errors 回 Phase 2-3 修補**

### Phase 5b — 他抽（fresh-context sub-agent）

觸發 fresh-context sub-agent（路徑 A）：
- 給它讀 init 產物（agent-commons/_config/ + roles/ + doctor stdout）
- 依 init-spec.md Phase 5b 抽驗集 10 項跑獨立驗證
- 0 errors → 回報「Phase 5b 通過」
- ≥ 1 errors → 修補 + 重跑 Phase 5 + Phase 5b

---

## 完成後回報格式

```
✅ /charter-init 完成（charter v<X> / preset: <preset>）
- agent-commons/ scaffold：就緒
- profile.yaml：<N> 條啟用
- mapping.yaml：common_memory_root = agent-commons/
- 領域公理：<axiom-file>（USER-RATIFIED）
- 角色：pm + engineer（PROVISIONAL，等 AI 自我具象化）
- doctor：0 errors / <N> warnings
- Phase 5b 他抽：通過（10/10）

⚠️ 偵測到舊版 AI 協作產物（若有）：<列出>
建議後續跑 /charter-doctor --fix 進行 Gap 遷移引導

下一步：
1. 對每個要啟用的 AI 角色，打 /<role>-init
2. AI 自我具象化 slash command（依 core/init-template.md §3.3）
3. User explicit 授權 AI 接角色後，AI 升 Status: ACTIVE 並寫 Sign-in Log
```

---

## 紀律提示（來自 init-spec.md）

- domain_axioms status 必須 USER-RATIFIED 才可跑 init（AI-DRAFTED → 退稿）
- _role.md Status 維持 PROVISIONAL（未經 user explicit 授權不可升 ACTIVE）
- 不得寫 Sign-in Log（等 user explicit 授權後才寫）
- 本檔引用 framework 路徑使用 `~/.agentcharter/`，不寫死 `C:/Users/<name>/`
