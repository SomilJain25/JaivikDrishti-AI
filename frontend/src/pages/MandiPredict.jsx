import { useState } from 'react'
import { 
  TrendingUp, 
  MapPin, 
  Wheat, 
  Calendar, 
  ArrowUpRight, 
  ArrowDownRight,
  Loader2,
  IndianRupee
} from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { predictPrice } from '../services/api'

const crops = ['wheat', 'rice', 'cotton', 'sugarcane', 'potato', 'tomato', 'onion', 'soybean']
const states = ['Punjab', 'Haryana', 'UP', 'Madhya Pradesh', 'Maharashtra', 'Gujarat', 'Karnataka', 'AP', 'Telangana', 'Bihar']

export default function MandiPredict() {
  const { lang, t } = useLanguage()
  const [crop, setCrop] = useState('')
  const [state, setState] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  
  const handlePredict = async () => {
    if (!crop || !state) return
    setLoading(true)
    setResult(null)
    try {
      const data = await predictPrice(crop, state)
      console.log("RESULT =", data)
      setResult(data)
    } catch (error) {
      console.error(error)
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
          <div className="inline-flex items-center justify-center w-16 h-16 bg-accent-500 rounded-2xl mb-4 shadow-lg">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">MandiBazaar AI</h1>
          <p className="text-gray-600">
            {lang === 'en' ? 'AI-powered crop price prediction' : 'एआई-संचालित फसल मूल्य भविष्यवाणी'}
          </p>
        </div>
        
        {/* Input Section */}
        <div className="glass-card p-6 md:p-8 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
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
                <option value="">{lang === 'en' ? 'Choose crop...' : 'फसल चुनें...'}</option>
                {crops.map(c => (
                  <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-red-500" />
                {t.selectState}
              </label>
              <select 
                value={state} 
                onChange={(e) => setState(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none bg-white"
              >
                <option value="">{lang === 'en' ? 'Choose state...' : 'राज्य चुनें...'}</option>
                {states.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>
          
          <button 
            onClick={handlePredict}
            disabled={!crop || !state || loading}
            className="w-full btn-accent flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {lang === 'en' ? 'Predicting...' : 'भविष्यवाणी हो रही है...'}
              </>
            ) : (
              <>
                <TrendingUp className="w-5 h-5" />
                {lang === 'en' ? 'Predict Price' : 'कीमत की भविष्यवाणी करें'}
              </>
            )}
          </button>
        </div>
        
        {result && (
            <div className="space-y-6 animate-slide-up">
            {/* Price Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="glass-card p-6 text-center border-l-4 border-blue-500">
                <p className="text-sm text-gray-500 mb-1">{lang === 'en' ? 'Current Price' : 'वर्तमान कीमत'}</p>
                <div className="text-3xl font-bold text-gray-800 flex items-center justify-center gap-1">
                  <IndianRupee className="w-6 h-6" />
                  {result.currentPrice}
                </div>
                <p className="text-xs text-gray-400 mt-1">per quintal</p>
              </div>
              
              <div className="glass-card p-6 text-center border-l-4 border-accent-500">
                <p className="text-sm text-gray-500 mb-1">{t.predictedPrice}</p>
                <div className="text-3xl font-bold text-gray-800 flex items-center justify-center gap-1">
                  <IndianRupee className="w-6 h-6" />
                  {result.predictedPrice}
                </div>
                <div className="flex items-center justify-center gap-1 mt-1 text-green-600 text-sm font-medium">
                  <ArrowUpRight className="w-4 h-4" />
                  +{result.trendPercent}%
                </div>
              </div>
              
              <div className="glass-card p-6 text-center border-l-4 border-green-500">
                <p className="text-sm text-gray-500 mb-1">{t.bestSell}</p>
                <div className="text-2xl font-bold text-gray-800 flex items-center justify-center gap-2">
                  <Calendar className="w-6 h-6 text-green-600" />
                  {result.bestSellMonth}
                </div>
                <p className="text-xs text-green-600 mt-1 font-medium">{result.marketDemand} Demand</p>
              </div>
            </div>
            
            {/* Price History Chart */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-accent-500" />
                Price Trend
              </h3>

              {result?.priceHistory?.length > 0 && (
                <div className="space-y-3">
                  {result.priceHistory.map((item, index) => {
                    const prevPrice =
                      index > 0 ? result.priceHistory[index - 1].price : item.price

                    const rising = item.price >= prevPrice

                    return (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="font-medium">{item.month}</div>

                        <div className="flex items-center gap-2">
                          {rising ? (
                            <ArrowUpRight className="w-4 h-4 text-green-600" />
                          ) : (
                            <ArrowDownRight className="w-4 h-4 text-red-600" />
                          )}

                          <span
                            className={
                              rising
                                ? "text-green-600 font-semibold"
                                : "text-red-600 font-semibold"
                            }
                          >
                            ₹{item.price}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
            
            {/* Market Insights */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4">
                {lang === 'en' ? 'Market Insights' : 'बाजार अंतर्दृष्टि'}
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 bg-green-50 rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <ArrowUpRight className="w-5 h-5 text-green-600" />
                    <span className="font-semibold text-green-800">
                      {lang === 'en' ? 'Price Rising' : 'कीमत बढ़ रही है'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    {lang === 'en' 
                      ? 'Prices are expected to increase by 8.5% in the coming weeks'
                      : 'आने वाले हफ्तों में कीमतों में 8.5% की वृद्धि की उम्मीद है'}
                  </p>
                </div>
                <div className="p-4 bg-blue-50 rounded-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <MapPin className="w-5 h-5 text-blue-600" />
                    <span className="font-semibold text-blue-800">
                      {lang === 'en' ? 'Best Market' : 'सबसे अच्छा बाजार'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    {lang === 'en'
                      ? 'Azadpur Mandi, Delhi offering highest prices'
                      : 'आजादपुर मंडी, दिल्ली सबसे अधिक कीमतें दे रही है'}
                  </p>
                </div>
              </div>
            </div>
              </div>
            )}
      </div>
    </div>
  )
}