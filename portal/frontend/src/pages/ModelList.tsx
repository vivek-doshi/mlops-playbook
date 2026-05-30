import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

interface ModelSummary {
  name: string;
  latest_versions: { version: string; stage: string }[];
}

export default function ModelList() {
  const [models, setModels] = useState<ModelSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/mlops-portal/api/models/")
      .then((r) => r.json())
      .then(setModels)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) return <p>Error: {error}</p>;

  return (
    <div>
      <h1>Registered Models</h1>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Latest Version</th>
            <th>Stage</th>
          </tr>
        </thead>
        <tbody>
          {models.map((m) => {
            const latest = m.latest_versions[0];
            return (
              <tr key={m.name}>
                <td>
                  <Link to={`/models/${m.name}`}>{m.name}</Link>
                </td>
                <td>{latest?.version ?? "—"}</td>
                <td>{latest?.stage ?? "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
