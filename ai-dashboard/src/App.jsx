import React, { useState } from "react";
import axios from "axios";
import Dashboard from "./pages/Dashboard";
import Insights from "./pages/Insights";
import Trends from "./pages/Trends";

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [activeTab, setActiveTab] = useState("Dashboard");
  const [renderKey, setRenderKey] = useState(0);

  // ✅ Upload CSV directly to backend — no local parsing
  const handleUpload = async () => {
    if (!file) {
      alert("Please select a CSV file first!");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:8000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log("✅ Backend response:", res.data);

      // Store backend response (KPIs, charts, insights, etc.)
      setResponse({
        industry: res.data.industry || "Unknown",
        kpis: res.data.kpis || [],
        charts: res.data.charts || [],
        insights: res.data.insights || {},
        eda: res.data.eda || {},
      });

      // Force dashboard re-render
      setRenderKey(Date.now());
    } catch (error) {
      console.error("❌ Upload failed:", error);
      alert("Upload failed: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // ✅ Tab renderer
  const renderTab = () => {
    if (loading) return <p>Processing file... please wait ⏳</p>;
    if (!response) return <p>Upload a CSV to generate your AI dashboard.</p>;

    switch (activeTab) {
      case "Dashboard":
        return <Dashboard key={`dash-${renderKey}`} data={response} />;
      case "Insights":
        return <Insights key={`insights-${renderKey}`} data={response} />;
      case "Trends":
        // Pass the uploaded file reference for on-demand trend generation
        return <Trends key={`trends-${renderKey}`} uploadedFile={file} />;
      default:
        return null;
    }
  };

  return (
    <div >
      {/* Navbar */}
      <div className="navbar ">
        {/* <h2 className="font-size: 1.7rem;
  font-weight: 600; color:#1a64daff">AI Dashboard Generator .</h2> */}
      <h2 >
        <span style={{ color: "#2772ebff", fontWeight: 900,fontSize: "1.4rem" }}>AI</span>{" "}
        <span style={{ color: "#2772ebff" ,  fontWeight: 700,fontSize: "1.4rem" }}>Dashboard Generator</span>
      </h2>
          
        
        <p className="font-size: 0.7rem">
          <span style={{ color: "#4c5869ff", fontWeight: 300 }}>Automated KPIs, Charts, and Insights from your CSV</span>{" "}
          
        </p>
      </div>
      <div className="container-full">
      {/* Upload Section */}
      <div className="upload-box ">
        <input
          id="fileInput"
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files[0])}
          className="hidden"
        />

        <label
          htmlFor="fileInput"
          className="choose-btn"
        >
          Choose File
        </label>

        <span className="file-name text-gray-400">
          {file ? file.name : "No file chosen"}
        </span>

        <button
          onClick={handleUpload}
          disabled={loading}
          className="upload-btn"
        >
          {loading ? "Processing..." : "Upload & Generate"}
        </button>
      </div>

      {/* Tabs Navigation */}
      <div className="tabs">
        {["Dashboard", "Insights", "Trends"].map((tab) => (
          <div
            key={tab}
            className={`tab ${activeTab === tab ? "active" : ""}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </div>
        ))}
      </div>

      {/* Tab Body */}
      <div className="container">
        {renderTab()}
      </div>
    </div>
    </div>
  );
}
