import { createContext, useContext, useState } from 'react'

const LanguageContext = createContext()

export const translations = {
  en: {
    appName: 'JaivikDrishti AI',
    tagline: 'From Soil to Sale — Smarter Decisions with AI',
    home: 'Home',
    CropScan: 'CropScan',
    "MandiBazaar AI": 'MandiBazaar AI',
    yieldSense: 'YieldSense',
    krishiBot: 'KrishiBot',
    uploadImage: 'Upload Image',
    analyzing: 'Analyzing...',
    diseaseDetected: 'Disease Detected',
    confidence: 'Confidence',
    treatment: 'Treatment',
    organicTreatment: 'Organic Treatment',
    prevention: 'Prevention Tips',
    selectCrop: 'Select Crop',
    selectState: 'Select State',
    predictedPrice: 'Predicted Price',
    marketTrend: 'Market Trend',
    bestSell: 'Best Time to Sell',
    soilType: 'Soil Type',
    temperature: 'Temperature (°C)',
    rainfall: 'Rainfall (mm)',
    predictYield: 'Predict Yield',
    estimatedYield: 'Estimated Yield',
    askQuestion: 'Ask me anything about farming...',
    send: 'Send',
    weather: 'Weather',
    farmingTips: 'Farming Tips',
    quickStats: 'Quick Stats',
    todayInsights: "Today's Farming Insights",
    recentScans: 'Recent Scans',
    scanNow: 'Scan Now',
    checkPrices: 'Check Prices',
    estimateYield: 'Estimate Yield',
    chatNow: 'Chat Now',
    govSchemes: 'Government Schemes',
    viewDetails: 'View Details',
    language: 'Language',
    welcome: 'Welcome to Smart Farming',
    heroDesc: 'AI-powered solutions for modern agriculture. Detect diseases, predict prices, estimate yields, and get expert advice — all in one place.',
    getStarted: 'Get Started',
    learnMore: 'Learn More',
  },
  hi: {
    appName: 'जैविकदृष्टि एआई',
    tagline: 'मिट्टी से बिक्री तक — एआई से स्मार्ट निर्णय',
    home: 'होम',
    CropScan: ' कृषि स्कैन',
    "MandiBazaar AI": 'मंडीबाजार एआई',
    yieldSense: 'यील्डसेंस',
    krishiBot: 'कृषिबॉट',
    uploadImage: 'छवि अपलोड करें',
    analyzing: 'विश्लेषण हो रहा है...',
    diseaseDetected: 'रोग का पता चला',
    confidence: 'विश्वास स्कोर',
    treatment: 'इलाज',
    organicTreatment: 'जैविक इलाज',
    prevention: 'रोकथाम के उपाय',
    selectCrop: 'फसल चुनें',
    selectState: 'राज्य चुनें',
    predictedPrice: 'अनुमानित कीमत',
    marketTrend: 'बाजार रुझान',
    bestSell: 'बेचने का सबसे अच्छा समय',
    soilType: 'मिट्टी का प्रकार',
    temperature: 'तापमान (°C)',
    rainfall: 'वर्षा (mm)',
    predictYield: 'पैदावार का अनुमान',
    estimatedYield: 'अनुमानित पैदावार',
    askQuestion: 'खेती के बारे में कुछ भी पूछें...',
    send: 'भेजें',
    weather: 'मौसम',
    farmingTips: 'खेती के टिप्स',
    quickStats: 'त्वरित आंकड़े',
    todayInsights: 'आज की खेती जानकारी',
    recentScans: 'हालिया स्कैन',
    scanNow: 'स्कैन करें',
    checkPrices: 'कीमत जांचें',
    estimateYield: 'पैदावार अनुमान',
    chatNow: 'चैट करें',
    govSchemes: 'सरकारी योजनाएं',
    viewDetails: 'विवरण देखें',
    language: 'भाषा',
    welcome: 'स्मार्ट खेती में आपका स्वागत है',
    heroDesc: 'आधुनिक कृषि के लिए एआई-संचालित समाधान। रोग का पता लगाएं, कीमतों का अनुमान लगाएं, पैदावार का आकलन करें और विशेषज्ञ सलाह प्राप्त करें — सब एक ही जगह।',
    getStarted: 'शुरू करें',
    learnMore: 'और जानें',
  }
}

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState('en')
  
  const toggleLang = () => setLang(prev => prev === 'en' ? 'hi' : 'en')
  
  const t = translations[lang]
  
  return (
    <LanguageContext.Provider value={{ lang, toggleLang, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export const useLanguage = () => useContext(LanguageContext)