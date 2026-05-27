import { Routes, Route } from 'react-router-dom'
import Home from '../pages/Home'
import CropScan from '../pages/DrishtiScan'
import MandiPredict from '../pages/MandiPredict'
import YieldSense from '../pages/YieldSense'
import KrishiBot from '../pages/KrishiBot'
import UnifiedDashboard from "../pages/UnifiedDashboard";
export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/crop-scan" element={<CropScan />} />
      <Route path="/mandi-bazaar-ai" element={<MandiPredict />} />
      <Route path="/yield-sense" element={<YieldSense />} />
      <Route path="/krishi-bot" element={<KrishiBot />} />
      <Route path="/krishibot" element={<KrishiBot />} />
      <Route path="/dashboard" element={<UnifiedDashboard/>} />
    </Routes>
  )
}
