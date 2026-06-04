import { useEffect, useState } from 'react'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import AppRoutes from './routes/AppRoutes'
import logo from './assets/JaivikDrishti_circular.png'
import KrishiBotWidget from './components/KrishiBotWidget'

export default function App() {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 2500)
    return () => clearTimeout(timer)
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="flex flex-col items-center gap-4 rounded-3xl bg-white/90 border border-slate-200 shadow-2xl shadow-slate-500/10 p-10">
          <img
            src={logo}
            alt="JaivikDrishti logo"
            className="w-24 h-24 object-cover rounded-full"
          />

          <div className="text-center">
            <h1 className="text-2xl font-bold text-slate-900">
              JaivikDrishti AI
            </h1>

            <p className="text-sm text-slate-500">
              Loading smart farming experience…
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative min-h-screen flex flex-col overflow-hidden bg-slate-50">
      <div className="relative z-10 flex-1 flex flex-col">
        <Navbar />

        <main className="flex-1">
          <AppRoutes />
        </main>

        <Footer />
      </div>

      {/* Floating KrishiBot */}
      <KrishiBotWidget />
    </div>
  )
}