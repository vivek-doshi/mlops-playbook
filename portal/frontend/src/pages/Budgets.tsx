import React, { useEffect, useState } from "react";

interface Budget {
  model_name: string;
  monthly_limit_usd: number;
  alert_threshold_pct: number;
}

export default function Budgets() {
  const [budgets, setBudgets] = useState<Budget[]>([]);

  useEffect(() => {
    fetch("/mlops-portal/api/budgets/")
      .then((r) => r.json())
      .then(setBudgets)
      .catch(console.error);
  }, []);

  return (
    <div>
      <h1>Model Budgets</h1>
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>Monthly Limit (USD)</th>
            <th>Alert Threshold</th>
          </tr>
        </thead>
        <tbody>
          {budgets.map((b) => (
            <tr key={b.model_name}>
              <td>{b.model_name}</td>
              <td>${b.monthly_limit_usd.toFixed(2)}</td>
              <td>{(b.alert_threshold_pct * 100).toFixed(0)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
