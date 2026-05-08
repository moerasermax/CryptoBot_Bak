# Role: Engineer

> **位階**：本檔在 `agent-commons/roles/engineer/` 根目錄，標明此角色資料夾的當值身份。
> **依據**：`core/init-template.md` Role Init Mandate v0.5.0（§1.3 Sign-in 職責由本檔承載）。

---

## 角色資訊

- **Spec**：引用 AgentCharter `roles/engineer/_spec.md`
- **AI 實作版**：引用 AgentCharter `roles/engineer/claude-code.md`（Claude Code）或 `roles/engineer/gemini-cli.md`
- **Status**：`ACTIVE`
- **當前扮演 AI**：Claude Code（Opus 4.7 / 1M context）
- **當值期間**：2026-05-04 ~ （當前 session）

### Status 二態（v0.7.0 加）

依 `core/multi-role-tracking.md §3.4.4` + `core/init-template.md §3.3.2 step 6`：

| 狀態 | 含義 | 觸發 |
|---|---|---|
| **`PROVISIONAL`** | 暫具象化 — slash command 已就緒、但角色身份**未經 user explicit 授權激活** | self-instantiation step 6 簽名後預設值 |
| **`ACTIVE`** | 已激活 — user explicit 授權某 AI 接該角色 | 升 ACTIVE 時才寫 Sign-in Log |

**禁止**：AI 自我發起把 Status 從 PROVISIONAL 升 ACTIVE（違反 multi-role-tracking §3.4.4 = F1）。

---

## 各 AI 的 Init Slash Command 具象化位置

| AI | 具象化位置 | 是否實裝？ | 自我具象化日期 |
|---|---|---|---|
| Claude Code | `.claude/commands/engineer-init.md` | ✅ | 2026-05-04 |
| Gemini CLI | `.gemini/commands/engineer-init.toml` | ❌ | — |
| Cursor | `.cursor/rules/engineer-init.mdc` | ❌ | — |
| 其他 / 無 slash 系統 | `agent-commons/roles/engineer/init-prompt.md` | ❌ | — |

→ AI 第一次扮演此角色時，自我具象化到自己廠商的位置（依 `core/init-template.md §3.3`）。框架不代生成。

---

## 切換歷史

| 日期 | 扮演 AI | 觸發原因 | Self-instantiation? | 能力差異要點 |
|---|---|---|---|---|
| 2026-05-04 | — | charter-init scaffold | — | 初始建立，尚無 AI 接任 |
| 2026-05-04 | Claude Code | 自我具象化完成（doctor schema 通過 0 errors） | ✅ `.claude/commands/engineer-init.md` | Status 維持 PROVISIONAL — 等 user explicit 授權後升 ACTIVE 並寫 Sign-in Log |
| 2026-05-04 | Claude Code（Opus 4.7 / 1M context） | Sign-in：user explicit 授權「你可以登入了」→ Status PROVISIONAL → ACTIVE | - | 首位接任 Engineer；Claude Code 全工具能力（Read/Edit/Bash/Grep/Glob/Agent/Hook）|

---

## 當值規範

接班 AI 進入此資料夾時的**第一動作**：

1. **召喚（Summon）**：讀本檔 + AI 廠商實作版確認身份
2. **校準（Calibrate）**：跑 `/engineer-init` slash command
3. **簽名（Sign-in）**：在切換歷史表追加一行
4. **守門（Gatekeep）**：確認所有就位狀態，未達標即中止 init

**禁止**：未跑 init 即進入工作（視同 F1 假宣告）。
