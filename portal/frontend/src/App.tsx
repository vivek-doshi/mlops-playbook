import React from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import ModelList from "./pages/ModelList";
import ModelDetail from "./pages/ModelDetail";
import Deploy from "./pages/Deploy";
import Budgets from "./pages/Budgets";
import CostDashboard from "./pages/CostDashboard";

export default function App() {
  return (
    <BrowserRouter basename="/mlops-portal">
      <nav style={{ padding: "1rem", borderBottom: "1px solid #ddd" }}>
        <NavLink to="/">Models</NavLink> |{" "}
        <NavLink to="/deploy">Deploy</NavLink> |{" "}
        <NavLink to="/budgets">Budgets</NavLink> |{" "}
        <NavLink to="/costs">Costs</NavLink>
      </nav>
      <main style={{ padding: "1rem" }}>
        <Routes>
          <Route path="/" element={<ModelList />} />
          <Route path="/models/:modelName" element={<ModelDetail />} />
          <Route path="/deploy" element={<Deploy />} />
          <Route path="/budgets" element={<Budgets />} />
          <Route path="/costs" element={<CostDashboard />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
