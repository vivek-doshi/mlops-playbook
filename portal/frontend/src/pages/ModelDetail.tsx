import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

interface Version {
  version: string;
  stage: string;
  run_id: string;
}

interface ModelDetail {
  name: string;
  description: string;
  tags: Record<string, string>;
  versions: Version[];
}

export default function ModelDetail() {
  const { modelName } = useParams<{ modelName: string }>();
  const [model, setModel] = useState<ModelDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!modelName) return;
    fetch(`/mlops-portal/api/models/${encodeURIComponent(modelName)}`)
      .then((r) => r.json())
      .then(setModel)
      .catch((e) => setError(String(e)));
  }, [modelName]);

  if (error) return <p>Error: {error}</p>;
  if (!model) return <p>Loading…</p>;

  return (
    <div>
      <h1>{model.name}</h1>
      <p>{model.description}</p>
      <h2>Versions</h2>
      <table>
        <thead>
          <tr>
            <th>Version</th>
            <th>Stage</th>
            <th>Run ID</th>
          </tr>
        </thead>
        <tbody>
          {model.versions.map((v) => (
            <tr key={v.version}>
              <td>{v.version}</td>
              <td>{v.stage}</td>
              <td>{v.run_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
