import { useLanguage } from '../context/LanguageContext'
import { 
  Scan, 
  TrendingUp, 
  Wheat, 
  Bot, 
  Sprout, 
  ChevronRight,
  Shield,
  Zap,
  Users
} from 'lucide-react'
import ModuleCard from '../components/ModuleCard'
import WeatherWidget from '../components/WeatherWidget'
import GovtSchemes from '../components/GovtSchemes'

const farmingTips = [
  { icon: Sprout, text: 'Rotate crops annually to maintain soil fertility', textHi: 'मिट्टी की उर्वरता बनाए रखने के लिए हर साल फसल बदलें' },
  { icon: Shield, text: 'Use neem oil for organic pest control', textHi: 'जैविक कीट नियंत्रण के लिए नीम का तेल उपयोग करें' },
  { icon: Zap, text: 'Install drip irrigation to save 40% water', textHi: '40% पानी बचाने के लिए ड्रिप सिंचाई लगाएं' },
  { icon: Users, text: 'Join FPOs for better market access', textHi: 'बेहतर बाजार पहुंच के लिए FPO से जुड़ें' },
]

const stats = [
  { label: 'Farmers Helped', value: '50K+', labelHi: 'किसानों की मदद' },
  { label: 'Diseases Detected', value: '12K+', labelHi: 'रोग पता चले' },
  { label: 'Price Predictions', value: '98%', labelHi: 'कीमत भविष्यवाणी' },
  { label: 'States Covered', value: '22+', labelHi: 'राज्य कवर' },
]

export default function Home() {
  const { lang, t } = useLanguage()
  
  const modules = [
    {
      title: 'CropScan',
      description: 'Detect crop diseases using AI-powered image analysis',
      icon: Scan,
      to: '/crop-scan',
      colorClass: 'bg-green-600',
      bgGradient: 'bg-gradient-to-br from-green-400 to-green-600',
    },
    {
      title: 'MandiBazaar AI',
      description: 'Predict crop market prices and selling trends',
      icon: TrendingUp,
      to: '/mandi-bazaar-ai',
      colorClass: 'bg-accent-500',
      bgGradient: 'bg-gradient-to-br from-yellow-400 to-orange-500',
    },
    {
      title: 'YieldSense',
      description: 'Estimate crop yield using weather and soil insights',
      icon: Wheat,
      to: '/yield-sense',
      colorClass: 'bg-secondary-500',
      bgGradient: 'bg-gradient-to-br from-amber-600 to-orange-700',
    },
    {
      title: 'KrishiBot',
      description: 'Ask farming questions in natural language',
      icon: Bot,
      to: '/krishi-bot',
      colorClass: 'bg-blue-600',
      bgGradient: 'bg-gradient-to-br from-blue-400 to-cyan-500',
    },
  ]
  
  return (
    <div className="min-h-screen pb-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-700 via-primary-800 to-primary-900 text-white">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-32 h-32 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-48 h-48 bg-accent-400 rounded-full blur-3xl" />
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 py-16 md:py-24">
          <div className="text-center max-w-3xl mx-auto animate-slide-up">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2 mb-6 border border-white/20">
              <Sprout className="w-5 h-5 text-accent-400" />
              <span className="text-sm font-medium">{t.welcome}</span>
            </div>
            
            <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
              {t.appName}
            </h1>
            
            <p className="text-xl md:text-2xl text-green-200 mb-4 font-light">
              {t.tagline}
            </p>
            
            <p className="text-green-100/80 text-lg mb-8 max-w-2xl mx-auto">
              {t.heroDesc}
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a href="#modules" className="btn-accent inline-flex items-center justify-center gap-2">
                {t.getStarted}
                <ChevronRight className="w-5 h-5" />
              </a>
              <a href="#schemes" className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold border-2 border-white/30 text-white hover:bg-white/10 transition-all">
                {t.learnMore}
              </a>
            </div>
          </div>
        </div>
        
        {/* Wave divider */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="#f0fdf4"/>
          </svg>
        </div>
      </section>
      
      {/* Stats Section */}
      <section className="max-w-7xl mx-auto px-4 -mt-8 relative z-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat, idx) => (
            <div key={idx} className="glass-card p-4 text-center animate-slide-up" style={{ animationDelay: `${idx * 100}ms` }}>
              <div className="text-2xl md:text-3xl font-bold text-primary-700">{stat.value}</div>
              <div className="text-xs md:text-sm text-gray-600 mt-1">
                {lang === 'en' ? stat.label : stat.labelHi}
              </div>
            </div>
          ))}
        </div>
      </section>
      
      {/* Main Content Grid */}
      <div className="max-w-7xl mx-auto px-4 mt-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Modules */}
          <div className="lg:col-span-2" id="modules">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
              <Zap className="w-6 h-6 text-accent-500" />
              {lang === 'en' ? 'AI Modules' : 'एआई मॉड्यूल'}
            </h2>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {modules.map((module, idx) => (
                <ModuleCard key={module.title} {...module} delay={idx * 100} />
              ))}
            </div>
          </div>
          
          {/* Right: Sidebar */}
          <div className="space-y-6">
            <WeatherWidget />
            
            {/* Farming Tips */}
            <div className="glass-card p-5">
              <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Sprout className="w-5 h-5 text-green-600" />
                {t.farmingTips}
              </h3>
              <div className="space-y-3">
                {farmingTips.map((tip, idx) => {
                  const Icon = tip.icon
                  return (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-gradient-to-r from-green-50 to-transparent rounded-xl">
                      <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Icon className="w-4 h-4 text-primary-700" />
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {lang === 'en' ? tip.text : tip.textHi}
                      </p>
                    </div>
                  )
                })}
              </div>
            </div>
            
            {/* Today's Insights */}
            <div className="glass-card p-5">
              <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-accent-500" />
                {t.todayInsights}
              </h3>
              <div className="space-y-3">
                <div className="p-3 bg-yellow-50 border-l-4 border-accent-500 rounded-r-xl">
                  <p className="text-sm text-gray-700">
                    {lang === 'en' 
                      ? 'Wheat prices expected to rise by 5% next week in North India markets'
                      : 'उत्तर भारत के बाजारों में अगले सप्ताह गेहूं की कीमतों में 5% की वृद्धि की उम्मीद'
                    }
                  </p>
                </div>
                <div className="p-3 bg-blue-50 border-l-4 border-blue-500 rounded-r-xl">
                  <p className="text-sm text-gray-700">
                    {lang === 'en'
                      ? 'Monsoon arrival predicted 3 days early this year'
                      : 'इस साल मानसून के आगमन की भविष्यवाणी 3 दिन पहले की गई'
                    }
                  </p>
                </div>
                <div className="p-3 bg-red-50 border-l-4 border-red-400 rounded-r-xl">
                  <p className="text-sm text-gray-700">
                    {lang === 'en'
                      ? 'Alert: Tomato leaf virus detected in Maharashtra region'
                      : 'अलर्ट: महाराष्ट्र क्षेत्र में टमाटर पत्ती वायरस का पता चला'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Government Schemes */}
      <div id="schemes">
        <GovtSchemes />
      </div>
    </div>
  )
}