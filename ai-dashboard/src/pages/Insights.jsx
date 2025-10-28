import React from "react";

export default function Insights({ data }) {
  console.log("🧩 Insights data received:", data);

  if (!data || !data.insights || Object.keys(data.insights).length === 0) {
    return (
      <div style={{ padding: "1rem" }}>
        <h2 style={{ fontSize: "1.3rem", marginBottom: "1rem" }}>AI Insights</h2>
        <p style={{ color: "gray" }}>No insights available.</p>
      </div>
    );
  }

  return (
    <div className="insight-container">
    <div style={{ padding: "1rem" }}>
      <h2 style={{ fontSize: "1.3rem", marginBottom: "1rem",color: "#256ce6ff" }}>AI Insights</h2>

      {Object.entries(data.insights).map(([section, insights]) => (
        <div key={section} style={{ marginBottom: "1.5rem" }}>
          <h3
            style={{
              fontSize: "1rem",
              fontWeight: 600,
              color: "#2e3644ff",
              marginBottom: "0.5rem",
            }}
          >
            {section}
          </h3>
          <ul style={{ paddingLeft: "1.5rem", lineHeight: "0.8" ,fontSize: "0.8rem" }}>
            {insights.map((ins, i) => (
              <p key={i}>{ins}</p>
            ))}
          </ul>
        </div>
      ))}
    </div>
    </div>
  );
}
