# Role: PM

> **位階**：本檔在 `agent-commons/roles/pm/` 根目錄，標明此角色資料夾的當值身份。
> **依據**：`core/init-template.md` Role Init Mandate v0.5.0（§1.3 Sign-in 職責由本檔承載）。

---

## 角色資訊

- **Spec**：引用 AgentCharter `roles/pm/_spec.md`
- **AI 實作版**：引用 AgentCharter `roles/pm/gemini-cli.md`（Gemini CLI）或 `roles/pm/claude-code.md`
- **Status**：`ACTIVE`
- **當前扮演 AI**：Google Gemini CLI (ACTIVE)
- **當值期間**：2026-05-14 起

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
| Claude Code | `.claude/commands/pm-init.md` | ❌ | — |
| Gemini CLI | `.gemini/commands/pm-init.toml` | ✅ | 2026-05-04 |
| Cursor | `.cursor/rules/pm-init.mdc` | ❌ | — |
| 其他 / 無 slash 系統 | `agent-commons/roles/pm/init-prompt.md` | ❌ | — |

→ AI 第一次扮演此角色時，自我具象化到自己廠商的位置（依 `core/init-template.md §3.3`）。框架不代生成。

---

## 切換歷史

| 日期 | 扮演 AI | 觸發原因 | Self-instantiation? | 能力差異要點 |
|---|---|---|---|---|
| 2026-05-14 | Google Gemini CLI | User explicit activation (Sign-in) | ✅ | Status 升為 ACTIVE；重啟 S75 Phase 1 派工 |
| 2026-05-13 | Google Gemini CLI | User explicit activation (Sign-in) | ✅ | Status 轉 ACTIVE；處理 A006 補正與 S75 戰略對齊 |
| 2026-05-12 | Google Gemini CLI | Session 重啟 sign-in（user explicit 授權） | - | Status 升為 ACTIVE；延續 [S74-C] Phase 3 管理 |
| 2026-05-06 | Google Gemini CLI | S72 Synchronization Logic Hardening & Upgrade | ✅ | PM Role activated after framework upgrade to v0.10.1 |
| 2026-05-04 | Google Gemini CLI | User explicit authorization for S71 & Cleanup | ✅ | PM 初始化完成，執行結構化清理與 F1 補救 |
| 2026-05-04 | — | charter-init scaffold | — | 初始建立，尚無 AI 接任 |

---

## 當值規範

接班 AI 進入此資料夾時的**第一動作**：

1. **召喚（Summon）**：讀本檔 + AI 廠商實作版確認身份
2. **校準（Calibrate）**：跑 `/pm-init` slash command
3. **簽名（Sign-in）**：在切換歷史表追加一行
4. **守門（Gatekeep）**：確認所有就位狀態，未達標即中止 init

**禁止**：未跑 init 即進入工作（視同 F1 假宣告）。
