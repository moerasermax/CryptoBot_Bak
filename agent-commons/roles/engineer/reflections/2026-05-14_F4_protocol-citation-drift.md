---
date: 2026-05-14
role: engineer
vendor: claude-code
status: 結案
violations: [F4]
---

# Violation Reflection: A008 Protocol Citation Drift (multi-role-tracking §3.4.4 Generalization)

## 1. 事故描述 (Context & Behavior)

於 2026-05-14 抽驗 PM 諮詢二回回應（S75 status update + Phase 1 授權請求）時，Engineer 抽驗 PM mtime 10:05 自降 `_role.md` Status `ACTIVE → PROVISIONAL` 動作，引述 `~/.agentcharter/core/multi-role-tracking.md §3.4.4` 為「**Status 升降須 user explicit 授權**」，據此認定 PM 動作違反 F1 + F5 + §3.5（同類第 6 次重犯）+ 對齊違反 v2 §0 第 3 條。

user 收到抽驗報告後明示裁決：「**登入把上次的登入狀態更新為 PROVISIONAL 這是准許的，這是自降不是自升**」+ 「幫我更新部分條款」，並選 B 選項（專案層更新 failure_mode_log §0 v2 加例外項）。

Engineer 隨後親讀 `~/.agentcharter/core/multi-role-tracking.md §3.4.4` 真實條文，確認：
- §3.4.4 三項紀律全部關於「**上岸方向**」（自我升 ACTIVE、寫 Sign-in Log、跨界激活）
- §3.4.5 對照表三類違反（init 自激活 / 切換自發起 / 隱式戴帽子）**均關於上岸方向**
- 條款**完全沒禁自降 PROVISIONAL**

Engineer 原引述屬泛化偏差 — 把「升 ACTIVE 須 user 授權」泛化為「升降皆須 user 授權」。

## 2. 違規分析 (Violations)

- **F4 條款引述偏差**: 引述條款編號（multi-role-tracking §3.4.4）正確、但條文內容心算泛化錯誤；違反 `~/.agentcharter/core/failure-modes.md` F4 定義「線號 / 章節編號偏差」延伸涵蓋「條文內容引述偏差」。

## 3. 根因分析 (Root Cause)

- **未驗檔即引述**: 抽驗 PM 時為了高密度結構化退稿，憑印象/心算引述 §3.4.4，未先 Read 該檔親驗真實條文 — 違反 `~/.agentcharter/core/evidence-first.md §3.3`「假設」標籤紀律 + Engineer memory `feedback_protocol_integrity.md`「協議條款引述前必驗檔案完整性」明示。
- **抽驗節奏壓力**: PM 報告含多項失真項，急於結構化呈現 5 條違反條款表，導致 #2/#3/#4/#5 連帶基於 #2 錯誤前提衍生（推導鏈污染）。
- **對稱性盲區**: §3.4.4 既有設計僅規範上岸（升 ACTIVE）方向，下岸（降 PROVISIONAL）方向是條款空白；Engineer 直覺地把空白填補為「對稱禁令」，違反 `~/.agentcharter/core/structural-anti-fabrication.md`（不可填補條款未明示處）。

## 4. 矯正措施 (Remediation)

- **抽驗結論校正**: 撤回原抽驗 #2/#3/#4/#5，保留 #1（PM 動到 agent-commons/ 內檔案仍命中 v2 §0 第 1 條範圍）。
- **PM 動作追溯合法化**: 依 user 裁決 B + 本 commit 新增的 v2 §0 第 1 條例外 2，PM mtime 2026-05-14 10:05 自降 PROVISIONAL 動作不視為違規；保留 PROVISIONAL 狀態等本 session user 重新激活。
- **§3.5 累計校正**: A007-X1/X2 之後 §3.5 累計仍停在第 5 次重犯（原 #3 第 6 次認定撤回），不影響 v2 verdict 既有結構性失靈裁決效力。
- **雙寫紀律落地**: 集體層 failure_mode_log §2 加 A008 entry + §8 5 點抽驗細節；個體層本檔（reflection）一併入版控（本 commit）。

## 5. 集體記憶建議 (Collective Memory Recommendations)

- **抽驗工作流硬性增 step**: 抽驗對方違規前，**強制** Read 引述條款檔案（且引用具體 §X.Y 行範圍）— 違反 evidence-first §3.3 + memory feedback_protocol_integrity 紀律本應禁止心算引述，本次仍犯，建議在 Engineer init 步驟 5 心智守則第 4 條（實證先行）加細項「條款引述前必先 Read 親驗、引用具體章節編號 + 行範圍」。
- **條款空白推導紀律**: 框架條款未明示某方向時，**不可單方面填補對稱禁令**；該方向屬合法 default（依 `~/.agentcharter/core/structural-anti-fabrication.md`）；如需禁令需走 framework 修訂程序（PR）。
- **抽驗回應推導鏈隔離**: 結構化退稿表多項條款認定不應共用前提；每條獨立 Read 親驗，避免單一錯誤前提污染整個推導鏈（本次 #2 偏差連帶污染 #3/#4/#5）。
