import React, { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, Polygon, Polyline, CircleMarker,
         Tooltip, useMap } from "react-leaflet";

const STATUS_COLOR = {
  survivor: "#2e7d32",          // 绿：复测存活
  mortality: "#c62828",         // 红：死亡
  ingrowth: "#1565c0",          // 蓝：进界
  unresolved_location_conflict: "#ef6c00",  // 橙：位置矛盾，待核实
  unresolved_missing: "#757575",
  below_threshold_t2: "#9e9e9e",
};

// GeoJSON [lng, lat] -> Leaflet [lat, lng]
const ll = (c) => [c[1], c[0]];

// 切换样地时把视图飞到该样地范围（bounds 属性只在挂载时生效）
function FlyToBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(bounds, { padding: [30, 30], maxZoom: 19 });
  }, [map, bounds]);
  return null;
}

export default function PlotMap({ plots, selectedPlot, onSelect, plotResult }) {
  const pairs = plotResult?.pairs || [];
  const links = useMemo(() => buildLinks(plots, selectedPlot, pairs),
    [plots, selectedPlot, pairs]);
  const bounds = useMemo(() => {
    if (!selectedPlot) return [[26.45, 117.20], [26.62, 117.45]];
    const ring = selectedPlot.boundary.coordinates[0];
    const lats = ring.map((c) => c[1]), lngs = ring.map((c) => c[0]);
    return [[Math.min(...lats), Math.min(...lngs)],
            [Math.max(...lats), Math.max(...lngs)]];
  }, [selectedPlot]);

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>样地位置与个体复测</h3>
        <div className="plot-tabs">
          {plots.map((p) => (
            <button key={p.plot_id}
                    className={selectedPlot?.plot_id === p.plot_id ? "active" : ""}
                    onClick={() => onSelect(p.plot_id)}>
              {p.plot_id}（{p.area_ha} ha）
            </button>
          ))}
        </div>
      </div>
      <MapContainer bounds={bounds} boundsOptions={{ padding: [30, 30] }}
                    scrollWheelZoom className="map">
        <FlyToBounds bounds={bounds} />
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {plots.map((p) => (
          <Polygon key={p.plot_id}
                   positions={p.boundary.coordinates[0].map(ll)}
                   pathOptions={{
                     color: selectedPlot?.plot_id === p.plot_id ? "#111" : "#888",
                     weight: selectedPlot?.plot_id === p.plot_id ? 2.5 : 1.2,
                     fillOpacity: 0.06,
                   }}
                   eventHandlers={{ click: () => onSelect(p.plot_id) }}>
            <Tooltip>{p.plot_id} · {p.area_ha} ha · {p.stratum_code}</Tooltip>
          </Polygon>
        ))}
        {links.map((l, i) => (
          <Polyline key={i} positions={[ll(l.t1), ll(l.t2)]}
                    pathOptions={{
                      color: STATUS_COLOR[l.status] || "#444",
                      weight: l.status.includes("unresolved") ? 2 : 1.4,
                      dashArray: l.status.includes("unresolved") ? "6 5" : undefined,
                      opacity: 0.85,
                    }} />
        ))}
        {links.flatMap((l) => [[l.t1, "t1", l.status, l.tag_t1],
                               [l.t2, "t2", l.status, l.tag_t2]])
              .filter(([pt]) => pt)
              .map(([pt, phase, st, tag], i) => (
          <CircleMarker key={i} center={ll(pt)} radius={phase === "t1" ? 5 : 6}
                        pathOptions={{
                          color: STATUS_COLOR[st] || "#444",
                          fillColor: phase === "t1" ? "#fff" : STATUS_COLOR[st],
                          fillOpacity: phase === "t1" ? 0.9 : 0.9,
                          weight: 2,
                        }}>
            <Tooltip>
              {tag} · {phase === "t1" ? "第一次调查" : "第二次调查"} ·{" "}
              {labelStatus(st)}
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
      <Legend />
    </div>
  );
}

function buildLinks(plots, selectedPlot, pairs) {
  if (!selectedPlot) return [];
  return pairs
    .filter((p) => p.t1 && p.t2 && p.t1.x_m != null && p.t2.x_m != null)
    .map((p) => {
      // 演示数据中点位由局部坐标生成；这里直接用两期记录内的经纬度。
      // demoData 已带 geom 时优先；否则用样地原点反算（与生成脚本同一公式）。
      const origin = selectedPlot.centroid.coordinates;
      const toLngLat = (o) => o?.geom?.coordinates || local(origin, o.x_m, o.y_m);
      return { ...p, t1: toLngLat(p.t1), t2: toLngLat(p.t2) };
    });
}

function local(origin, x, y) {
  const [ox, oy] = origin;
  return [ox + x / (111320 * 0.894), oy + y / 111320];
}

function labelStatus(st) {
  return {
    survivor: "复测存活", mortality: "死亡", ingrowth: "进界",
    unresolved_location_conflict: "位置矛盾·待核实",
    unresolved_missing: "缺测/状态待核",
    below_threshold_t2: "未达起测径阶",
  }[st] || st;
}

function Legend() {
  const items = [
    ["survivor", "复测存活（空心=t1，实心=t2）"],
    ["mortality", "死亡"], ["ingrowth", "进界"],
    ["unresolved_location_conflict", "位置矛盾（虚线，先核实）"],
    ["unresolved_missing", "缺测待核"],
  ];
  return (
    <div className="legend">
      {items.map(([k, t]) => (
        <span key={k}>
          <i style={{ background: STATUS_COLOR[k] }} /> {t}
        </span>
      ))}
    </div>
  );
}
