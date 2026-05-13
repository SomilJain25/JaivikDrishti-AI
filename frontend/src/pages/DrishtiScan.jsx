import { useState, useRef } from 'react'
import { 
  Upload, 
  Camera, 
  Scan, 
  CheckCircle, 
  AlertTriangle, 
  Leaf,
  Droplets,
  Shield,
  Loader2,
  X
} from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { detectDisease } from '../services/api'

export default function CropScan() {
  const { lang, t } = useLanguage()
  const [selectedImage, setSelectedImage] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const fileInputRef = useRef(null)
  
  const handleImageSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedImage(file)
      setPreview(URL.createObjectURL(file))
      setResult(null)
    }
  }
  
  const handleAnalyze = async () => {
    if (!selectedImage) return
    setLoading(true)
    try {
      const data = await detectDisease(selectedImage)
      setResult(data)
    } catch (error) {
      alert('Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }
  
  const clearImage = () => {
    setSelectedImage(null)
    setPreview(null)
    setResult(null)
  }
  
  return (
    <div className="min-h-screen pb-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center py-8 animate-slide-up">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-600 rounded-2xl mb-4 shadow-lg">
            <Scan className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">CropScan</h1>
          <p className="text-gray-600">
            {lang === 'en' 
              ? 'AI-powered crop disease detection' 
              : 'एआई-संचालित फसल रोग पहचान'}
          </p>
        </div>
        
        {/* Upload Area */}
        <div className="glass-card p-6 md:p-8 mb-6">
          {!preview ? (
            <div 
              onClick={() => fileInputRef.current?.click()}
              className="border-3 border-dashed border-green-300 rounded-2xl p-8 md:p-12 text-center cursor-pointer
                       hover:border-green-500 hover:bg-green-50/50 transition-all group"
            >
              <div className="w-20 h-20 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                <Camera className="w-10 h-10 text-primary-700" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                {lang === 'en' ? 'Upload Crop Image' : 'फसल की तस्वीर अपलोड करें'}
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                {lang === 'en' ? 'Click to upload or drag and drop' : 'अपलोड करने के लिए क्लिक करें'}
              </p>
              <button className="btn-primary">
                <Upload className="w-4 h-4 inline mr-2" />
                {t.uploadImage}
              </button>
              <input 
                ref={fileInputRef}
                type="file" 
                accept="image/*" 
                onChange={handleImageSelect}
                className="hidden"
              />
            </div>
          ) : (
            <div className="relative">
              <button 
                onClick={clearImage}
                className="absolute top-2 right-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors z-10"
              >
                <X className="w-4 h-4" />
              </button>
              <img 
                src={preview} 
                alt="Preview" 
                className="w-full max-h-96 object-contain rounded-xl mb-4 bg-gray-100"
              />
              
              {!result && !loading && (
                <button 
                  onClick={handleAnalyze}
                  className="w-full btn-primary flex items-center justify-center gap-2"
                >
                  <Scan className="w-5 h-5" />
                  {lang === 'en' ? 'Analyze with AI' : 'एआई से विश्लेषण करें'}
                </button>
              )}
            </div>
          )}
        </div>
        
        {/* Loading State */}
        {loading && (
          <div className="glass-card p-8 text-center animate-fade-in">
            <Loader2 className="w-12 h-12 text-primary-700 animate-spin mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-800 mb-2">{t.analyzing}</h3>
            <p className="text-sm text-gray-500">
              {lang === 'en' ? 'Our AI is examining your crop image...' : 'हमारा एआई आपकी फसल की तस्वीर की जांच कर रहा है...'}
            </p>
            <div className="mt-4 h-2 bg-gray-200 rounded-full overflow-hidden max-w-xs mx-auto">
              <div className="h-full bg-primary-700 rounded-full animate-pulse w-3/4" />
            </div>
          </div>
        )}
        
        {/* Results */}
        {result && (
          <div className="space-y-6 animate-slide-up">
            {/* Main Result Card */}
            <div className="glass-card p-6 border-l-4 border-green-500">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 bg-green-100 rounded-2xl flex items-center justify-center flex-shrink-0">
                  {result.confidence > 80 ? (
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  ) : (
                    <AlertTriangle className="w-8 h-8 text-yellow-600" />
                  )}
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-gray-800 mb-1">{result.disease}</h2>
                  <p className="text-sm text-gray-500 mb-3">
                    {lang === 'en' ? 'Severity' : 'गंभीरता'}: <span className="font-medium text-orange-600">{result.severity}</span>
                  </p>
                  
                  {/* Confidence Meter */}
                  <div className="mb-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">{t.confidence}</span>
                      <span className="font-bold text-primary-700">{result.confidence}%</span>
                    </div>
                    <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full transition-all duration-1000"
                        style={{ width: `${result.confidence}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Treatment */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Leaf className="w-5 h-5 text-green-600" />
                {t.treatment}
              </h3>
              <ul className="space-y-3">
                {result.treatment.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-green-50 rounded-xl">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700 text-sm">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Organic Treatment */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Droplets className="w-5 h-5 text-teal-600" />
                {t.organicTreatment}
              </h3>
              <ul className="space-y-3">
                {result.organicTreatment.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-teal-50 rounded-xl">
                    <Leaf className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700 text-sm">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Prevention */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5 text-blue-600" />
                {t.prevention}
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {result.prevention.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 bg-blue-50 rounded-xl">
                    <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700 text-sm">{item}</span>
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