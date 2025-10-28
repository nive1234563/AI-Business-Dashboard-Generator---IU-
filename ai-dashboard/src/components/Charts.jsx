import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  TimeScale,
} from "chart.js";
import { Line, Bar, Pie } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  TimeScale
);

ChartJS.defaults.color = "#cbd5e1";
ChartJS.defaults.borderColor = "#334155";

const COLORS = [
  "#7b9fff", "#60a5fa", "#a78bfa", "#34d399", "#f59e0b",
  "#f87171", "#22d3ee", "#f472b6", "#94a3b8", "#c084fc"
];

export default function ChartRenderer({ chart }) {
  if (!chart || !chart.data || !chart.data.labels) {
    return <div style={{ color: "#94a3b8" }}>No chart data</div>;
  }

  const labels = chart.data.labels;
  const datasets = (chart.data.series || []).map((s, idx) => ({
    label: s.name || `Series ${idx + 1}`,
    data: s.values || [],
    fill: true,
    borderColor: COLORS[idx % COLORS.length],
    backgroundColor: COLORS[idx % COLORS.length] + "33", // 20% transparent
    pointRadius: 3,
    borderWidth: 2,
    tension: 0.4,
  }));

  const chartData = { labels, datasets };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "top", labels: { color: "#e2e8f0", font: { size: 11 } } },
      tooltip: {
        backgroundColor: "#1e293b",
        borderColor: "#334155",
        borderWidth: 1,
        titleColor: "#f8fafc",
        bodyColor: "#e2e8f0",
      },
    },
    scales: {
      x: {
        grid: { color: "#1e293b" },
        ticks: { color: "#cbd5e1", font: { size: 10 } },
      },
      y: {
        grid: { color: "#1e293b" },
        ticks: { color: "#cbd5e1", font: { size: 10 } },
      },
    },
    animation: {
      duration: 1800,
      easing: "easeOutQuart",
    },
  };

  switch ((chart.type || "").toLowerCase()) {
    case "bar":
      return <Bar data={chartData} options={options} />;
    case "pie":
      return (
        <div style={{ maxWidth: "240px", margin: "0 auto" }}>
          <Pie
            data={{
              labels,
              datasets: [
                {
                  data: datasets[0].data,
                  backgroundColor: COLORS.slice(0, labels.length),
                  borderColor: "#0f172a",
                  borderWidth: 2,
                },
              ],
            }}
            options={{
              plugins: { legend: { position: "bottom" } },
              animation: { animateRotate: true, duration: 1500 },
            }}
          />
        </div>
      );
    default:
      return <Line data={chartData} options={options} />;
  }
}
