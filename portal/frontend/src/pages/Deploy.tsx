import React, { useState } from "react";

export default function Deploy() {
  const [modelName, setModelName] = useState("");
  const [modelVersion, setModelVersion] = useState("");
  const [targetEnv, setTargetEnv] = useState("staging");
  const [result, setResult] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const resp = await fetch("/mlops-portal/api/models/promote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model_name: modelName,
        model_version: modelVersion,
        target_environment: targetEnv,
      }),
    });
    const data = await resp.json();
    setResult(JSON.stringify(data, null, 2));
  };

  return (
    <div>
      <h1>Trigger Deployment</h1>
      <p>All deployments are executed via GitHub Actions. No direct mutations.</p>
      <form onSubmit={handleSubmit}>
        <label>
          Model name:
          <input value={modelName} onChange={(e) => setModelName(e.target.value)} required />
        </label>
        <br />
        <label>
          Model version:
          <input value={modelVersion} onChange={(e) => setModelVersion(e.target.value)} required />
        </label>
        <br />
        <label>
          Target environment:
          <select value={targetEnv} onChange={(e) => setTargetEnv(e.target.value)}>
            <option value="dev">dev</option>
            <option value="staging">staging</option>
            <option value="production">production</option>
          </select>
        </label>
        <br />
        <button type="submit">Promote →</button>
      </form>
      {result && <pre>{result}</pre>}
    </div>
  );
}
