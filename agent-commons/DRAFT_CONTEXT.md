# 暫存堆疊 (Draft Context)

> **狀態**：clean — 2026-05-07 於 HANDOFF_24 寫入後清空（依 `~/.agentcharter/core/working-stack-discipline §3.3` step 6 紀律）。
> **下次累積規則**：本 session 任何持續超過單次推論週期的工作，必須在此檔累積關鍵 stdout / 決策軌跡 / 未結案 capsule 中間狀態 / 違規事件，依 `working-stack-discipline §2.1`。
> **save 觸發**：依 `§3.1` 由 user 明示（如 `/checkpoints save`）或依 `§3.2` 自動候選條件觸發；save 必同步 git commit（§4 鐵律）。
