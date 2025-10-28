import React, { useMemo, useEffect, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale,
  BubbleController,
  ScatterController,
  PolarAreaController,
} from "chart.js";
import {
  Bar,
  Line,
  Pie,
  Doughnut,
  Radar,
  PolarArea,
  Scatter,
  Bubble,
} from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale,
  BubbleController,
  ScatterController,
  PolarAreaController
);

export default function ChartRenderer({ chart }) {
  if (!chart || !chart.data) {
    return (
      <div className="text-gray-400 text-center p-6">
        ⚠️ No chart data available.
      </div>
    );
  }

  const { title, type, data } = chart;
  const chartRef = useRef(null);

  // ✅ Memoize chart data so re-renders are fast
  const colorPalette = [
   
  "#5447CE", // Green
  "#887DFC", // Green
  "#4996FF", // Yellow
  "#16C8C6", // Red
  "#68EAEA", // Green
  
  
//   "#F472B6", // Pink
//   "#38BDF8", // Cyan
  
];

const color1 = ["#5447CE","#16C8C6","#F472B6" // Green
];

// ✅ Create gradient for bars and areas
  const getGradient = (ctx, color) => {
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, color );
    gradient.addColorStop(1, color );
    return gradient;
  };

  const chartData = useMemo(() => {
    const labels = data?.labels || [];
    
    const datasets = (data?.series || []).map((s, i) => {
      const baseColor = colorPalette[i % colorPalette.length];
      const chartColor = color1[i % color1.length]; // ✅ color for this specific chart

      return {
        label: s.name,
        data: s.values,
        borderColor: type === "pie" || type === "doughnut" || type === "polarArea"
            ? baseColor
            : chartColor ,
        backgroundColor:
          type === "pie" || type === "doughnut" || type === "polarArea"
            ? labels.map((_, j) => colorPalette[j % colorPalette.length])
            : chartColor ,
        pointRadius: type === "line" ? 1 : 0,
        pointHoverRadius: type === "line" ? 5 : 0,
        tension: 0.4,
        fill: type === "area",
        borderWidth: type === "line"? 2: 0,
      };
    });
    return { labels, datasets };
  }, [data, type]);

  // ✅ Define consistent chart styling and decimation
  const chartOptions = useMemo(
  () => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom", // ✅ move legend to right side
        align: "right",
        labels: {
          color: "#a4b0beff",
          boxWidth: 14,
          usePointStyle: true,
          padding: 10,
          font: { size: 10 },
        },
      },
      tooltip: {
        mode: "index",
        intersect: false,
        backgroundColor: "rgba(15, 23, 42, 0.9)",
        titleColor: "#9ba2b2",
        bodyColor: "#d1d5db",
        borderColor: "#475569",
        // borderWidth: 1,
      },
      decimation: {
        enabled: true,
        algorithm: "min-max",
        samples: 500,
      },
    },
    scales: {
        x: {
          ticks: { color: "#9ca3af", font: { size: 11 } },
          grid: { color: "rgba(255, 255, 255, 0.3)",drawBorder: false, },
          stacked: type === "stackedBar",
          drawBorder: false, 
           border: {
      display: false,         // removes axis base line
    },
        },
        y: {
          ticks: { color: "#9ca3af", font: { size: 11 } },
          grid: { color: "rgba(255, 255, 255, 0.3)" ,drawBorder: false,},
          stacked: type === "stackedBar",
           
           border: {
      display: false,         // removes axis base line
    },
        },
      },
    
  }),
  []
);


  const chartOptionsPie = useMemo(
  () => ({
    responsive: true,
    maintainAspectRatio: false,
    aspectRatio: 1,
    plugins: {
      legend: {
        position: "right",
        align: "center",
        labels: {
          color: "#a7aab0ff",
          boxWidth: 6,
          usePointStyle: true,
          padding: 15,
          font: { size: 9 },
        },
      },
      tooltip: {
        mode: "index",
        intersect: false,
        backgroundColor: "rgba(15, 23, 42, 0.9)",
        titleColor: "#fff",
        bodyColor: "#d1d5db",
        borderColor: "#475569",
      },
    },
    layout: {
        padding: { left: 10, right: 10, top: 0, bottom: 0 },
        },
    // ✅ Hide all axes (Pie charts shouldn't show any)
    scales: {
      x: {
        display: false, // no axis
        grid: { display: false },
        ticks: { display: false },
        border: { display: false },
      },
      y: {
        display: false,
        grid: { display: false },
        ticks: { display: false },
        border: { display: false },
      },
    },
  }),
  []
);


useEffect(() => {
    const chartInstance = chartRef.current;
    if (!chartInstance) return;
    // Gradient enhancement for bars/areas
    const ctx = chartInstance.ctx;
    chartInstance.data.datasets.forEach((dataset, i) => {
      if (["bar", "stackedBar", "area"].includes(type)) {
        dataset.backgroundColor = getGradient(ctx, colorPalette[i % colorPalette.length]);
      }
    });
    chartInstance.update();
  }, [chartRef, type]);

    return (
    <div
      className="w-full bg-slate-900 rounded-xl p-3 flex flex-col justify-between"
      style={{
        minHeight: "280px",
        maxHeight: "380px",
        height: "350px",
        overflow: "hidden",
      }}
    >
      <h5 className="text-md font-semibold text-gray-300 mb-3">{title}</h5>

      <div
        className="flex-1"
        style={{
          position: "relative",
          height: "100%",
          maxHeight: "320px",
        }}
      >
        {(() => {
          switch (type) {
           case "line":
      case "area":
        return <Line ref={chartRef} data={chartData} options={chartOptions} />;
      case "bar":
      case "horizontal-bar":
        return <Bar ref={chartRef} data={chartData} options={chartOptions} />;
      case "stackedBar":
        return <Bar ref={chartRef} data={chartData} options={chartOptions} />;
      case "pie":
        return <Pie ref={chartRef} data={chartData} options={chartOptionsPie} />;
      case "doughnut":
        return <Doughnut ref={chartRef} data={chartData} options={chartOptions} />;
      case "polarArea":
        return <PolarArea ref={chartRef} data={chartData} options={chartOptions} />;
      case "radar":
        return <Radar ref={chartRef} data={chartData} options={chartOptions} />;
      case "scatter":
        return <Scatter ref={chartRef} data={chartData} options={chartOptions} />;
      case "bubble":
        return <Bubble ref={chartRef} data={chartData} options={chartOptions} />;
            default:
              return (
                <div className="text-gray-400 text-center p-6">
                  ⚠️ Unsupported chart type: {type}
                </div>
              );
          }
        })()}
      </div>
    </div>
  );

}



//   const ChartComponent = (() => {
//     switch (type) {
//       case "line":
//       case "area":
//         return <Line ref={chartRef} data={chartData} options={chartOptions} />;
//       case "bar":
//       case "horizontal-bar":
//         return <Bar ref={chartRef} data={chartData} options={chartOptions} />;
//       case "stackedBar":
//         return <Bar ref={chartRef} data={chartData} options={chartOptions} />;
//       case "pie":
//         return <Pie ref={chartRef} data={chartData} options={chartOptions} />;
//       case "doughnut":
//         return <Doughnut ref={chartRef} data={chartData} options={chartOptions} />;
//       case "polarArea":
//         return <PolarArea ref={chartRef} data={chartData} options={chartOptions} />;
//       case "radar":
//         return <Radar ref={chartRef} data={chartData} options={chartOptions} />;
//       case "scatter":
//         return <Scatter ref={chartRef} data={chartData} options={chartOptions} />;
//       case "bubble":
//         return <Bubble ref={chartRef} data={chartData} options={chartOptions} />;
//       default:
//         return (
//           <div className="text-gray-400 text-center p-6">
//             ⚠️ Unsupported chart type: {type}
//           </div>
//         );
//     }
//   })();

//   return (
//     <div className="h-[380px] w-full flex flex-col">
//       <h5 className="text-md font-semibold text-gray-200 mb-3 border-b border-slate-700 pb-1">
//         {title}
//       </h5>
//       <div className="flex-1">{ChartComponent}</div>
//     </div>
//   );
// }
