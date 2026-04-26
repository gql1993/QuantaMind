export default function Phase12UnifiedTrendCanvas() {
  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h1>Phase 12 统一运营驾驶舱趋势</h1>
      <p>数据文件：docs/reports/phase12_unified_dashboard_trend_latest.json</p>
      <ul>
        <li>输入：weekly / gate / drift / forecast</li>
        <li>输出：trend_status + key trend rows</li>
        <li>用途：周例会与发布决策前快速态势确认</li>
      </ul>
    </div>
  );
}
