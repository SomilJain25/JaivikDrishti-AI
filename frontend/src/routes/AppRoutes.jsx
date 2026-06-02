import { useState, useEffect } from 'react'
import Home from '../pages/Home'
import DrishtiScan from '../pages/DrishtiScan'
import MandiPredict from '../pages/MandiPredict'
import YieldSense from '../pages/YieldSense'
import KrishiBot from '../pages/KrishiBot'
import UnifiedDashboard from "../pages/UnifiedDashboard";

export default function AppRoutes() {
  const [currentPath, setCurrentPath] = useState(window.location.hash.slice(1) || '/')

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentPath(window.location.hash.slice(1) || '/')
    }
    
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  // Simple hash-based routing
  const getComponent = () => {
    const path = currentPath.toLowerCase()
    
    if (path === '/' || path === '') return <Home />
    if (path === '/crop-scan' || path === '/drishti-scan') return <DrishtiScan />
    if (path === '/mandi-bazaar-ai' || path === '/mandi-predict') return <MandiPredict />
    if (path === '/yield-sense') return <YieldSense />
    if (path === '/krishi-bot' || path === '/krishibot') return <KrishiBot />
    if (path === '/dashboard') return <UnifiedDashboard />
    
    return <Home /> // default to home
  }

  return getComponent()
}

