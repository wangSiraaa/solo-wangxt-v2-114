import React from "react";

const STATUS_LABEL = {
  survivor: "复测存活",
  mortality: "死亡",
  ingrowth: "进界",
  unresolved_location_conflict: "位置矛盾·待核实",
  unresolved_missing: "缺测/待核",
  below_threshold_t2: "未达径阶",
};

function fmt(v, d = 1) {
  return v == null ? "—" : Number(v).toFixed(d);
}

export default function RemeasureTable({ plotResult }) {
  if (!plotResult) {
    return <div className="panel"><p>请选择样地。</p></div>;
  }
  const pairs = [...plotResult.pairs].sort((a, b) =>
    (a.tag_t1 || a.tag_t2 || "").localeCompare(b.tag_t1 || b.tag_t2 || ""));

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>个体复测明细 · {plotResult.plot_id}
          <small>（{plotResult.area_ha} ha，层 {plotResult.stratum_id}）</small>
        </h3>
      </div>
      <table className="remeasure">
        <thead>
          <tr>
            <th>t1 编号</th><th>t2 编号</th><th>判定</th>
            <th>匹配方式</th><th>位置偏差(m)</th>
            <th>胸径 t1 (cm)</th><th>胸径 t2 (cm)</th>
            <th>树高 t1 (m)</th><th>树高 t2 (m)</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          {pairs.map((p, i) => (
            <tr key={i} className={`st-${p.status}`}>
              <td>{p.tag_t1 || "—"}</td>
              <td>{p.tag_t2 || "—"}</td>
              <td><span className={`badge st-${p.status}`}>
                {STATUS_LABEL[p.status]}</span></td>
              <td>{p.matched_via === "crosswalk" ? "复测改号交叉表"
                  : p.matched_via === "tag" ? "同号+位置核对" : "新记录"}</td>
              <td className={p.distance_m > 1 ? "warn" : ""}>
                {fmt(p.distance_m, 2)}</td>
              <td>{fmt(p.t1?.dbh_cm)}</td>
              <td>{fmt(p.t2?.dbh_cm)}</td>
              <td>{fmt(p.t1?.height_m)}</td>
              <td>{fmt(p.t2?.height_m)}</td>
              <td className="note">{p.note}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flags">
        <Flag title="真实零生长（Δ≈0，保留）" tags={plotResult.zero_growth_tags}
              cls="ok" />
        <Flag title="缺测（不插补、不计零）"
              tags={plotResult.missing_measurement_tags} cls="muted" />
        <Flag title="负生长存疑（待核实）"
              tags={plotResult.negative_growth_tags} cls="warn" />
        <Flag title="身份/位置未决（排除出分量）"
              tags={plotResult.unresolved_tags} cls="alert" />
      </div>
    </div>
  );
}

function Flag({ title, tags, cls }) {
  return (
    <div className={`flag ${cls}`}>
      <strong>{title}</strong>
      <div>{tags && tags.length ? tags.join("、") : "无"}</div>
    </div>
  );
}
