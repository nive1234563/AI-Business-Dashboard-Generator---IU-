import React, { useMemo } from "react";
import ChartRenderer from "../components/ChartRenderer";
import "../style.css";



export default function Dashboard({ data }) {
  if (!data) return <div className="text-gray-400 p-4">No data uploaded.</div>;

  const kpis = data.kpis || [];
  const charts = data.charts || [];

  // Split KPIs
  const simpleKpis = kpis.filter((k) => typeof k.value === "number");
  const groupedKpis = kpis.filter((k) => typeof k.value === "object" && k.value !== null);

  const displayedKpis = simpleKpis.slice(0, 5);

  // Memoized valid charts
  const validCharts = useMemo(() => {
    return charts.filter((c) => c?.data?.labels?.length > 0).slice(0, 9);
  }, [charts]);

  const chartDisplayItems = [...validCharts];
  if (chartDisplayItems.length < 9) {
    const remaining = 9 - chartDisplayItems.length;
    chartDisplayItems.push(...groupedKpis.slice(0, remaining));
  }

  return (
    
    <div>

      {/* Industry Header */}
      <div className=" p-4 rounded-xl shadow mb-6">
        <h3 className="text-md font-semibold">
          Industry:{" "}
          <span className="text-blue-400">{data.industry || "Unknown"}</span>
        </h3>
      </div>
      

      {/* KPI Section */}
      {/* KPI Section */}
      <div className="kpi-grid">
        {displayedKpis.map((k, i) => (
          <div key={i} className="kpi-card">
            <div className="kpi-name">{k.name}</div>
            <div className="kpi-value">
              {typeof k.value === "number"
                ? k.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                : k.value}
            </div>
            <div className="kpi-desc">{k.description}</div>
          </div>
        ))}
      </div>


      {/* Chart + Grouped KPI Section */}
      {/* Chart Section */}
      <div className="chart-grid">

        {/* {chartDisplayItems.length > 0 ? (
          chartDisplayItems.map((item, i) => {
            const isChart = !!item.title;
            return (
              <div
                key={i}
                className=" chart-card"

              >
                <h4 className="text-md font-semibold mb-3">
                  {item.title || item.name}
                </h4>

                {isChart ? (
                  <ChartRenderer chart={item} />
                ) : (
                  <div className="text-sm text-gray-300 mt-2 space-y-1 overflow-y-auto max-h-60 pr-1">
                    {Array.isArray(item.value)
                      ? item.value.map((obj, idx) => (
                          <div
                            key={idx}
                            className="flex justify-between border-b border-slate-700 pb-1"
                          >
                            <span>{Object.values(obj)[0]}</span>
                            <span className="font-semibold text-green-400">
                              {Object.values(obj).slice(-1)[0]}
                            </span>
                          </div>
                        ))
                      : Object.entries(item.value || {}).map(([k, v]) => (
                          <div
                            key={k}
                            className="flex justify-between border-b border-slate-700 pb-1"
                          >
                            <span>{k}</span>
                            <span className="font-semibold text-green-400">
                              {v.toLocaleString(undefined, {
                                maximumFractionDigits: 2,
                              })}
                            </span>
                          </div>
                        ))}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <p className="text-gray-400 text-center">No charts available.</p>
        )} */}
        {chartDisplayItems.length > 0 ? (
        chartDisplayItems
          // ✅ Only keep items that actually have chart data
          .filter(
            (item) =>
              item.title && item.data && item.data.labels && item.data.series
          )
          .map((item, i) => (
            <div key={i} className="chart-card">
              
              <ChartRenderer chart={item} />
            </div>
          ))
      ) : (
        <p className="text-gray-400 text-center">No charts available.</p>
      )}

      </div>
   </div>
  );
}