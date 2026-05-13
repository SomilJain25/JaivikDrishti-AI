import { useState } from 'react'
import { 
  Wheat, 
  Thermometer, 
  CloudRain, 
  Layers, 
  Loader2,
  Sprout,
  CheckCircle
} from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { predictYield } from '../services/api'

const soilTypes = ['loamy', 'clay', 'sandy', 'black', 'red', 'alluvial']
const crops = ['wheat', 'rice', 'cotton', 'sugarcane', 'maize']

export default function YieldSense() {
  const { lang, t } = useLanguage()
  const [soilType, setSoilType] = useState('')
  const [temperature, setTemperature] = useState('')
  const [rainfall, setRainfall] = useState('')
  const [crop, setCrop] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  
  const handlePredict = async () => {
    if (!soilType || !temperature || !rainfall || !crop) return
    setLoading(true)
    try {
      const data = await predictYield(soilType, parseFloat(temperature), parseFloat(rainfall), crop)
      setResult(data)
    } catch (error) {
      alert('Prediction failed')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="min-h-screen pb-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center py-8 animate-slide-up">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-secondary-500 rounded-2xl mb-4 shadow-lg">
            <Wheat className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">YieldSense</h1>
          <p className="text-gray-600">
            {lang === 'en' ? 'AI-powered crop yield prediction' : 'एआई-संचालित फसल पैदावार भविष्यवाणी'}
          </p>
        </div>
        
        {/* Input Form */}
        <div className="glass-card p-6 md:p-8 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <Layers className="w-4 h-4 text-secondary-500" />
                {t.soilType}
              </label>
              <select 
                value={soilType} 
                onChange={(e) => setSoilType(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-secondary-500 focus:border-transparent outline-none bg-white"
              >
                <option value="">{lang === 'en' ? 'Select soil...' : 'मिट्टी चुनें...'}</option>
                {soilTypes.map(s => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <Wheat className="w-4 h-4 text-primary-700" />
                {t.selectCrop}
              </label>
              <select 
                value={crop} 
                onChange={(e) => setCrop(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white"
              >
                <option value="">{lang === 'en' ? 'Select crop...' : 'फसल चुनें...'}</option>
                {crops.map(c => (
                  <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <Thermometer className="w-4 h-4 text-red-500" />
                {t.temperature}
              </label>
              <input 
                type="number"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                placeholder="e.g., 28"
                className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-400 focus:border-transparent outline-none bg-white"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <CloudRain className="w-4 h-4 text-blue-500" />
                {t.rainfall}
              </label>
              <input 
                type="number"
                value={rainfall}
                onChange={(e) => setRainfall(e.target.value)}
                placeholder="e.g., 800"
                className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none bg-white"
              />
            </div>
          </div>
          
          <button 
            onClick={handlePredict}
            disabled={!soilType || !temperature || !rainfall || !crop || loading}
            className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {lang === 'en' ? 'Calculating...' : 'गणना हो रही है...'}
              </>
            ) : (
              <>
                <Sprout className="w-5 h-5" />
                {t.predictYield}
              </>
            )}
          </button>
        </div>
        
        {/* Results */}
        {result && (
          <div className="space-y-6 animate-slide-up">
            {/* Yield Result Card */}
            <div className="glass-card p-8 text-center border-t-4 border-primary-700">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Wheat className="w-10 h-10 text-primary-700" />
              </div>
              <h2 className="text-lg text-gray-600 mb-2">{t.estimatedYield}</h2>
              <div className="text-5xl font-bold text-primary-700 mb-2">
                {result.estimatedYield}
              </div>
              <p className="text-gray-500 mb-4">{result.unit}</p>
              <div className="inline-flex items-center gap-2 bg-green-100 text-green-800 px-4 py-2 rounded-full text-sm font-medium">
                <CheckCircle className="w-4 h-4" />
                {result.confidence}% {lang === 'en' ? 'Confidence' : 'विश्वास'}
              </div>
            </div>
            
            {/* Recommendations */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Sprout className="w-5 h-5 text-primary-700" />
                {lang === 'en' ? 'Recommendations' : 'सुझाव'}
              </h3>
              <div className="space-y-3">
                {result.recommendations.map((rec, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-4 bg-gradient-to-r from-green-50 to-transparent rounded-xl border-l-4 border-primary-500">
                    <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-primary-700 font-bold text-sm">{idx + 1}</span>
                    </div>
                    <p className="text-gray-700 text-sm leading-relaxed">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}