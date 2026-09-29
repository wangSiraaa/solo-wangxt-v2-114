import React, { useEffect, useMemo, useState } from "react";
import { fetchAnalysis, fetchPlots } from "./api.js";
import PlotMap from "./PlotMap.jsx";
import RemeasureTable from "./RemeasureTable.jsx";
import ComponentsReport from "./ComponentsReport.jsx";

export default function App() {
  const [plots, setPlots] = useState([]);
  const [selected, setSelected] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetchAnalysis({
          surveyT1: 1, surveyT2: 2, releaseId: 1,
        });
        if (!alive) return;
        setData(res);
        const plotList = res._plots || res.population?._plots || [];
        setPlots(plotList.length ? plotList : demoPlotFallback(res));
      } catch (e) {
        setError(e.message);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (plots.length && !selected) setSelected(plots[0].plot_id);
  }, [plots, selected]);

  const plotResult = useMemo(
    () => data?.plots?.find((p) => p.plot_id === selected) || null,
    [data, selected]);

  const selectedPlot = useMemo(
    () => plots.find((p) => p.plot_id === selected) || null,
    [plots, selected]);

  if (loading) return <div className="loading">加载样地与分析结果…</div>;
  if (error) return <div className="error">加载失败：{error}</div>;

  return (
    <div className="app">
      <header className="app-head">
        <h2>固定样地两次调查：生长 · 死亡 · 进界分析</h2>
        <span className="rule">
          编号相同但位置矛盾 → 先核实；单位必须显式；已确认版本不被新方程静默改变
        </span>
      </header>
      <div className="grid">
        <PlotMap plots={plots} selectedPlot={selectedPlot}
                 onSelect={setSelected} plotResult={plotResult} />
        <RemeasureTable plotResult={plotResult} />
      </div>
      <ComponentsReport data={data} />
    </div>
  );
}

// 当后端只返回分析结果、未返回地块边界时的保底（演示数据自带 _plots）
function demoPlotFallback(_res) {
  return [];
}
