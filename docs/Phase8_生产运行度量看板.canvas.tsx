export default function Phase8OpsMetricsCanvas() {
  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h1>Phase 8 生产运行度量看板</h1>
      <p>数据文件：docs/reports/phase8_ops_metrics_dashboard_latest.json</p>
      <ul>
        <li>SLO：Availability 与 Error Budget</li>
        <li>容量：Pending Approvals 与 Timeout Tasks</li>
        <li>结论：GREEN / YELLOW / RED</li>
      </ul>
      <p>说明：该 Canvas 用于固定展示维度，数据由脚本生成后可复制到可视化层。</p>
    </div>
  );
}
