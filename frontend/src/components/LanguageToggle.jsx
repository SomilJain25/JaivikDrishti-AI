import { Globe } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'

export default function LanguageToggle() {
  const { lang, toggleLang, t } = useLanguage()
  
  return (
    <button
      onClick={toggleLang}
      className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm 
                 text-white hover:bg-white/30 transition-all border border-white/30"
      aria-label="Toggle language"
    >
      <Globe className="w-4 h-4" />
      <span className="text-sm font-medium">{lang === 'en' ? 'हिंदी' : 'English'}</span>
    </button>
  )
}