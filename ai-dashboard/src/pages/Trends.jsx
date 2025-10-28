import React, { useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Filler
);

export default function Trends({ uploadedFile }) {
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ✅ Function to trigger backend trends generation
  const handleGenerateTrends = async () => {
    if (!uploadedFile) {
      alert("Please upload a CSV first!");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", uploadedFile);

      const response = await fetch("http://localhost:8000/trends", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to generate trends");

      const data = await response.json();
      setTrends(data.trends);
    } catch (err) {
      console.error("⚠️ Trend generation error:", err);
      setError("Failed to generate trends. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // ✅ Display placeholders or errors
  if (!trends) {
    return (
      <div className="text-gray-200 p-6 flex flex-col items-center justify-center min-h-[300px]">
        <button
          onClick={handleGenerateTrends}
          disabled={loading}
          className={ "choose-btn"
          }
        >
          {loading ? "Generating..." : "Generate Trends"}
        </button>

        {error && <p className="mt-3 text-red-400">{error}</p>}

        {!error && !loading && (
          <p className="text-gray-400 mt-4 text-center">
            Click the button above to generate forecast trends for your dataset.
          </p>
        )}
      </div>
    );
  }

  const forecastInfo = trends.forecast_info || {};
  const forecastData = trends.forecast_data || {};

  const hasData =
    (forecastData.labels && forecastData.labels.length > 0) ||
    (forecastData.x && forecastData.x.length > 0);

  if (!forecastInfo.forecast_possible || !hasData) {
    return (
      <div className="text-gray-400 text-center p-6">
        ⚠️ {forecastInfo.reason || "No suitable columns for trends."}
      </div>
    );
  }

  // ✅ Prepare chart data
  const labels = forecastData.labels || forecastData.x || [];
  const values =
    (forecastData.series && forecastData.series[0]?.values) || forecastData.y || [];
  const yName =
    (forecastData.series && forecastData.series[0]?.name) ||
    forecastData.y_col ||
    "Forecast";

  const chartData = {
    labels,
    datasets: [
      {
        label: `Forecasted ${yName}`,
        data: values,
        borderColor: "rgba(56, 189, 248, 1)",
        // backgroundColor: "rgba(56, 189, 248, 0.15)",
        borderWidth: 2,
        tension: 0.4,
        // fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: "#ccc" } },
      tooltip: { mode: "index", intersect: false },
    },
    scales: {
      x: { ticks: { color: "#939393ff" } },
      y: { ticks: { color: "#909090ff" } },
    },
  };

  return (
    <div className="text-gray-200 p-4">
      <div className="bg-slate-800 p-4 rounded-xl shadow mb-6 flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold mb-1">
            Forecasting Trends for{" "}
            <span className="text-blue-400">{yName}</span>
          </h2>
          <p className="text-sm text-gray-400">
            Based on {forecastData.x_col || forecastData.x_axis || "Date/Time"} using Prophet forecasting.
          </p>
        </div>
        <button
          onClick={handleGenerateTrends}
          disabled={loading}
          className="choose-btn"
        >
          {loading ? "Regenerating..." : "Regenerate Trends"}
        </button>
      </div>

      {/* ✅ Chart Box */}
      <div
        className="bg-slate-900 border border-slate-700 rounded-xl shadow-md p-6"
        style={{ height: "550px" }}
      >
        <Line data={chartData} options={chartOptions} />
      </div>

      {/* ✅ Additional heuristic insights if available */}
      {trends.insights?.heuristics && (
        <div className="bg-slate-800 mt-6 p-4 rounded-xl shadow text-gray-300">
          <h3 className="text-md font-semibold mb-2 text-blue-300">
            Model Insights
          </h3>
          <p>{trends.insights.heuristics}</p>
        </div>
      )}
    </div>
  );
}
