import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import RoutesPage from "./pages/RoutesPage";
import StopsPage from "./pages/StopsPage";
import PackPage from "./pages/PackPage";
import BagsPage from "./pages/BagsPage";
import RejectsPage from "./pages/RejectsPage";
import WeightsPage from "./pages/WeightsPage";
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/pack" replace />} />
        <Route path="/routes" element={<RoutesPage />} />
        <Route path="/stops" element={<StopsPage />} />
        <Route path="/pack" element={<PackPage />} />
        <Route path="/bags" element={<BagsPage />} />
        <Route path="/rejects" element={<RejectsPage />} />
        <Route path="/weights" element={<WeightsPage />} />
      </Route>
    </Routes>
  );
}
