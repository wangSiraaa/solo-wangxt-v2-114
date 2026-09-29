// API 客户端：优先请求 DRF 后端；后端不可达时回退到内置的虚构数据演示。
// 这样在没有 PostGIS 的开发机上也能打开界面核对展示逻辑。

import demoData from "./demoData.js";

async function tryFetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await jsonSafe(res);
    const err = new Error(body?.detail || `HTTP ${res.status}`);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return res.json();
}

async function jsonSafe(res) {
  try { return await res.json(); } catch { return null; }
}

export async function fetchAnalysis({ surveyT1, surveyT2, releaseId,
                                     allowRecreate = false }) {
  try {
    return await tryFetchJson("/api/analysis-runs/execute/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        survey_t1: surveyT1, survey_t2: surveyT2,
        equation_release: releaseId, allow_recreate: allowRecreate,
      }),
    });
  } catch (err) {
    if (err instanceof TypeError) {
      // fetch 网络层失败（后端未启动）-> 演示数据
      return { _demo: true, ...demoData };
    }
    throw err;
  }
}

export async function fetchPlots() {
  try {
    return await tryFetchJson("/api/plots/");
  } catch (err) {
    if (err instanceof TypeError) return { _demo: true, results: demoData._plots };
    throw err;
  }
}
