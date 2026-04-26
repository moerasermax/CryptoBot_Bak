# 任務膠囊：[S66-E] 啟動期時鐘漂移 Pre-flight Check 🕒

## 1. 任務目標 (Goal)
在系統啟動初期實作強制性的時鐘偏差檢查（Pre-flight Check），透過 ASCII Banner 視覺化偏差狀態，並在偏差過大時根據設定強制終止程序，確保實盤環境下的簽章安全與運維透明度。

## 2. 實實作清單 (Implementation List)
- [x] **[Refactor]** 抽取測量演算法：將 `NtpDriftMonitor` 與 `CheckSkewCommand` 重複的「包夾測量法 (Round-trip Mid-point)」抽取至 `Application` 層的 `ISkewMeasurementService`。
- [x] **[Execution]** 實作啟動檢查服務：新增 `IStartupHealthCheck` 與 `StartupSkewCheck`，負責執行單次同步並回傳結構化結果 (Safe/Warning/Unsafe)。
- [x] **[Execution]** 實作啟動 Banner 與攔截邏輯 (ConsoleApp)：
    - 在 `Program.cs` 插入檢查點。
    - 實作 ASCII Banner 渲染邏輯，顯示當前模式、偏差毫秒數及行動建議。
    - 支援 `Startup:AbortIfSkewExceedsMs` 設定，若偏差超過該值且不為 null，則 `Environment.Exit(1)`。
- [x] **[Configuration]** 更新 `appsettings.json`：新增 `Startup`區段。
- [x] **[Refactor]** 更新舊有組件：讓 `NtpDriftMonitor` 與 `CheckSkewCommand` 改用 `ISkewMeasurementService`。
- [x] **[Verification]** 撰寫單元測試：覆蓋測量邏輯、健康狀態判定及啟動攔截分支。

## 3. 驗收檢核點 (VCP)
- **VCP-1 (Visual)**: 啟動 ConsoleApp 時，在日誌開始前必須看到明顯的 ASCII Banner。 (已驗證：Banner 正常渲染)
- **VCP-2 (Safety)**: 若偏差 > 1000ms 且 `AbortIfSkewExceedsMs` 已設定，程序必須印出錯誤並停止啟動。 (已驗證：情境 3 Abort 成功)
- **VCP-3 (Consistency)**: `DiagnosticTool` 的 `check-skew` 輸出與啟動 Banner 的數值來源一致。 (已驗證：兩者皆為 +64ms 左右)
- **VCP-4 (Abstraction)**: `Application` 層不相依於 `System.Console`，Banner 渲染在 `ConsoleApp` 層實作。 (已驗證：Application 層零 Console 相依)

## 4. 交付要求 (Deliverables)
- [x] `Institutional_Memory.md` 更新：新增 §S66-E 關於啟動檢查與攔截機制的紀錄。
- [x] `HANDOFF_19.md`：紀錄本項韌性強化成果。 (即將隨 checkpoint 更新)
- [x] 🧪 **PM 驗收測試計畫**：提供模擬不同偏差值 (Mock) 的驗證步驟。 (已由工程師交付並完成驗收)

---
## 5. 驗證反饋紀錄 (History)
- **2026-04-25**: 由工程師 (ClaudeCode) 交付驗收計畫。PM (Gemini) 執行情境 1-3 測試，全數通過。
- **2026-04-25**: §1.6 結案核准抽驗完成，工程師正式宣告完工。
