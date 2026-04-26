# 任務膠囊：[S66-D] NTP 時鐘漂移防護 (NTP Drift Protection)

> **任務位階**：IRON §⑦ Domain 純粹性 與 §⑤ 風控透明化
> **執行者**：Claude (Chief Engineer)
> **目標**：實作本地時鐘與交易所（BingX）伺服器時間的同步檢測機制。當偏差超過閾值（1 秒）時，觸發風控攔截，防止下單失敗與數據污染。

---

## 📌 現狀分析 (Research Findings)

1.  **重要性**：交易所 API (REST/WS) 通常要求 `timestamp` 參數與其伺服器時間誤差不得超過一定範圍（BingX 通常為 1-5 秒），否則會回報簽章失效。
2.  **現有工具**：`IExchangeClient` 尚無 `GetServerTimeAsync` 方法；系統雖有 `IClock` 介面，但僅為封裝 `DateTime.UtcNow`，缺乏偏差校準邏輯。
3.  **機制設計**：應採「巡檢-攔截」模式。巡檢服務定期計算偏差，下單前由 `RiskManager` 檢查當前偏差是否安全。

---

## 🏗️ 實作清單 (Implementation List)

### T1：時鐘偏差偵測 (Detection)
- **[Infrastructure]** 在 `IExchangeClient` 與 `BingXExchangeClient` 實作 `GetServerTimeAsync()`。
- **[Application]** 實作 `NtpDriftMonitor : BackgroundService`：
    - 每 5 分鐘執行一次 `GetServerTimeAsync`。
    - 計算 `Offset = ServerTime - LocalTime`。
    - 將 `CurrentOffset` 儲存在單例 (Singleton) 的 `IClockSkewState` 中。

### T2：風控攔截 (Risk Integration)
- **[Application]** 在 `IRiskManager.CheckBeforeOpenAsync` 中加入時鐘檢查：
    - 若 `Math.Abs(CurrentOffset.TotalMilliseconds) > 1000ms`，回傳 `Rejected`。
    - 原因標註為：`[RISK] NTP Drift detected (Skew: {ms}ms). Order rejected for safety.`。

### T3：診斷與透明度 (Visibility)
- **[Diagnostic]** 新增指令 `s66d_check-skew`：顯示當前本地時間、交易所時間、偏差毫秒數與狀態（Safe/Unsafe）。
- **[Log]** 任何偏差超過 500ms 的情況應發出 `Warning` 日誌。

---

## ✅ 驗收標準 (VCP)

1.  **[VCP-Build]**：全專案編譯 0 警告、0 錯誤。
2.  **[VCP-Diagnostic]**：執行 `s66d_check-skew` 能正確輸出與 BingX 的時間差。
3.  **[VCP-Breaker]**：(人工模擬) 透過修改 Mock 服務讓偏差 > 1s，驗證下單流程被 `RiskManager` 攔截並在 Dashboard 決策日誌顯示琥珀金 `RISK` 標籤。
4.  **[VCP-Log]**：啟動時日誌出現 `[INF] NTP sync check complete: skew is {n}ms.`。

---
_「時間是金融系統的座標軸，座標歪了，任何交易都失去了意義。」_
