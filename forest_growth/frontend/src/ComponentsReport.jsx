import React from "react";

const CN = { growth: "生长量", mortality: "死亡量", ingrowth: "进界量" };

function ci(arr) {
  if (!arr || arr[0] == null || Number.isNaN(arr[0])) return "SE/CI 无法估计（层内样地不足）";
  return `95% CI [${fmtKg(arr[0])}, ${fmtKg(arr[1])}]`;
}

function fmtKg(v) {
  if (v == null || Number.isNaN(v)) return "—";
  if (Math.abs(v) >= 1000) return `${(v / 1000).toFixed(1)} t`;
  return `${v.toFixed(0)} kg`;
}

export default function ComponentsReport({ data }) {
  if (!data) return null;
  const pop = data.population;
  return (
    <div className="panel report">
      <div className="panel-head">
        <h3>分量来源与不确定性（按抽样设计加权）</h3>
        <div className="meta">
          调查：{data.survey_t1} → {data.survey_t2} ｜ 方程版本：
          <code>{data.release_id}</code>
        </div>
      </div>

      <table className="pop">
        <thead>
          <tr><th>总体分量</th><th>估计总量（烘干 kg）</th>
          <th>SE（kg）</th><th>95% 置信区间</th><th>自由度</th></tr>
        </thead>
        <tbody>
          {Object.keys(CN).map((k) => {
            const key = `${k}_kg_ha`;
            return (
              <tr key={k}>
                <td><b>{CN[k]}</b></td>
                <td>{fmtKg(pop.totals_kg[key])}</td>
                <td>{fmtKg(pop.se_kg[key])}</td>
                <td>{ci(pop.ci95_kg[key])}</td>
                <td>{pop.degrees_of_freedom[key]}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="estimator">
        估计量：<code>{pop.source.estimator}</code>
        <br />分层面积：{Object.entries(pop.source.stratum_areas_ha)
          .map(([k, v]) => `${k}=${v} ha`).join("，")}；
        抽样权重：{pop.source.weighting}
      </p>

      <h4>各样地分量（每公顷）与来源 / 假设</h4>
      <div className="plot-cards">
        {data.plots.map((p) => (
          <div key={p.plot_id} className="plot-card">
            <header>{p.plot_id} <small>{p.area_ha} ha · {p.stratum_id}</small></header>
            {["growth", "mortality", "ingrowth"].map((k) => {
              const c = p[k];
              return (
                <div key={k} className="comp">
                  <div className="comp-title">
                    {CN[k]}：{fmtKg(c.biomass_kg)}
                    <small>（{fmtKg(c.biomass_kg_per_ha)}/ha，{c.n_trees} 株）</small>
                  </div>
                  <div className="kv"><b>来源：</b>{c.source.kind}</div>
                  <div className="kv"><b>株号：</b>
                    {c.source.tree_tags.join("、") || "（无）"}</div>
                  <div className="kv"><b>测量假设：</b>
                    胸径 ±{c.uncertainty.measurement.dbh_sd_cm} cm
                    {c.uncertainty.measurement.height_sd_m != null &&
                      `，树高 ±${c.uncertainty.measurement.height_sd_m} m`}
                  </div>
                  <div className="kv"><b>方程残差：</b>
                    {c.uncertainty.equation_mean_cv != null
                      ? `均值 CV ${(c.uncertainty.equation_mean_cv * 100).toFixed(1)}%`
                      : "—"}
                  </div>
                  <div className="kv"><b>缺测处理：</b>
                    {c.uncertainty.missing_treatment}</div>
                </div>
              );
            })}
            <div className="balance">
              平衡核对残差：{fmtKg(p.balance_check.residual_kg)}
              （{p.balance_check.note}）
            </div>
          </div>
        ))}
      </div>
      {data._demo && <p className="demo-note">
        当前为内置虚构数据演示；连接 DRF 后端后自动切换为 /api 实时结果。</p>}
    </div>
  );
}
