import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Menu, 
  X, 
  Scan, 
  TrendingUp, 
  Wheat, 
  Bot, 
  Home 
} from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import LanguageToggle from './LanguageToggle'
import logo from '../assets/JaivikDrishti_circular.png'

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const { t } = useLanguage()
  const location = useLocation()
  
  const navItems = [
    { path: '/', label: t.home, icon: Home },
    { path: '/crop-scan', label: t.CropScan, icon: Scan },
    { path: '/mandi-bazaar-ai', label: t["MandiBazaar AI"], icon: TrendingUp },
    { path: '/yield-sense', label: t.yieldSense, icon: Wheat },
    { path: '/krishi-bot', label: t.krishiBot, icon: Bot },
  ]
  
  const isActive = (path) => location.pathname === path
  
  return (
    <nav className="sticky top-0 z-50 bg-primary-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-10 h-10 rounded-full overflow-hidden bg-white flex items-center justify-center group-hover:scale-110 transition-transform">
              <img src={logo} alt="JaivikDrishti logo" className="w-full h-full object-cover" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-white font-bold text-lg leading-tight">JaivikDrishti</h1>
              <p className="text-green-200 text-xs">AI</p>
            </div>
          </Link>
          
          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all
                    ${isActive(item.path) 
                      ? 'bg-white text-primary-700 shadow-md' 
                      : 'text-green-100 hover:bg-white/10 hover:text-white'
                    }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              )
            })}
            <div className="ml-4">
              <LanguageToggle />
            </div>
          </div>
          
          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center gap-3">
            <LanguageToggle />
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-white p-2 rounded-lg hover:bg-white/10 transition-colors"
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-primary-800 border-t border-green-600 animate-fade-in">
          <div className="px-4 py-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all
                    ${isActive(item.path) 
                      ? 'bg-white text-primary-700' 
                      : 'text-green-100 hover:bg-white/10'
                    }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              )
            })}
          </div>
        </div>
      )}
    </nav>
  )
}