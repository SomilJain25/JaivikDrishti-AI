import {Heart } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import Bharat_VISTAAR_circular from '../assets/Bharat_VISTAAR_circular.png'

export default function Footer() {
  const { t } = useLanguage()
  
  return (
    <footer className="bg-primary-900 text-green-100 mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <img src={Bharat_VISTAAR_circular} alt="Bharat VISTAAR" className="w-6 h-6" />
            <span className="font-bold text-lg">JaivikDrishti AI</span>
          </div>
          
          <p className="text-sm text-green-300 text-center">
            Made with <Heart className="w-4 h-4 inline text-red-400" /> for Indian Farmers
          </p>
          
          <div className="text-xs text-green-400">
            © 2026 JaivikDrishti AI. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  )
}