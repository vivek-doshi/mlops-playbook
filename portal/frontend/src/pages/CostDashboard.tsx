import React from "react";

export default function CostDashboard() {
  const grafanaUrl = "/grafana/d/mlops-costs/model-serving-costs";
  return (
    <div>
      <h1>Cost Dashboard</h1>
      <p>
        Live cost data is available in Grafana.{" "}
        <a href={grafanaUrl} target="_blank" rel="noopener noreferrer">
          Open Cost Dashboard →
        </a>
      </p>
      <iframe
        src={grafanaUrl}
        width="100%"
        height="600"
        frameBorder="0"
        title="Cost Dashboard"
      />
    </div>
  );
}
