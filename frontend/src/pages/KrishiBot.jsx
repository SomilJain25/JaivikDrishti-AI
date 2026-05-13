import { useState, useRef, useEffect } from 'react'
import { 
  Bot, 
  Send, 
  Mic, 
  User, 
  Loader2,
  Sparkles,
  MessageCircle
} from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { getChatResponse } from '../services/api'

const quickQuestions = {
  en: [
    'How to control pests organically?',
    'Best fertilizer for wheat?',
    'When to sow rice?',
    'How to improve soil health?',
    'Drip irrigation benefits?',
    'Crop rotation tips?'
  ],
  hi: [
    'जैविक तरीके से कीट कैसे नियंत्रित करें?',
    'गेहूं के लिए सर्वश्रेष्ठ उर्वरक?',
    'धान कब बोएं?',
    'मिट्टी का स्वास्थ्य कैसे सुधारें?',
    'ड्रिप सिंचाई के फायदे?',
    'फसल चक्र के टिप्स?'
  ]
}

export default function KrishiBot() {
  const { lang, t } = useLanguage()
  const [messages, setMessages] = useState([
    { 
      role: 'bot', 
      text: lang === 'en' 
        ? 'Namaste! I am KrishiBot. How can I help you with farming today?'
        : 'नमस्ते! मैं कृषिबॉट हूं। आज मैं आपकी खेती में कैसे मदद कर सकता हूं?'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  const handleSend = async (text = input) => {
    if (!text.trim()) return
    
    const userMsg = { role: 'user', text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    
    try {
      const response = await getChatResponse(text)
      setMessages(prev => [...prev, { role: 'bot', text: response.message }])
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'bot', 
        text: lang === 'en' ? 'Sorry, I could not process that.' : 'क्षमा करें, मैं इसे प्रोसेस नहीं कर सका।'
      }])
    } finally {
      setLoading(false)
    }
  }
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  return (
    <div className="min-h-screen pb-4 flex flex-col">
      <div className="max-w-4xl mx-auto w-full px-4 flex-1 flex flex-col">
        {/* Header */}
        <div className="text-center py-6 animate-slide-up">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4 shadow-lg">
            <Bot className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">KrishiBot</h1>
          <p className="text-gray-600">
            {lang === 'en' ? 'Your AI farming assistant' : 'आपका एआई कृषि सहायक'}
          </p>
        </div>
        
        {/* Chat Container */}
        <div className="glass-card flex-1 flex flex-col min-h-[500px] mb-4 overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''} animate-fade-in`}
              >
                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0
                  ${msg.role === 'bot' ? 'bg-blue-100' : 'bg-green-100'}`}>
                  {msg.role === 'bot' ? (
                    <Bot className="w-5 h-5 text-blue-600" />
                  ) : (
                    <User className="w-5 h-5 text-primary-700" />
                  )}
                </div>
                <div className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed
                  ${msg.role === 'bot' 
                    ? 'bg-gray-100 text-gray-800 rounded-tl-none' 
                    : 'bg-primary-700 text-white rounded-tr-none'
                  }`}>
                  {msg.text}
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex gap-3 animate-fade-in">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Bot className="w-5 h-5 text-blue-600" />
                </div>
                <div className="bg-gray-100 rounded-2xl rounded-tl-none p-4">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Quick Questions */}
          {messages.length < 3 && (
            <div className="px-4 pb-3">
              <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                {lang === 'en' ? 'Try asking:' : 'पूछने का प्रयास करें:'}
              </p>
              <div className="flex flex-wrap gap-2">
                {quickQuestions[lang].map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(q)}
                    className="text-xs bg-blue-50 text-blue-700 px-3 py-2 rounded-full hover:bg-blue-100 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Input Area */}
          <div className="p-4 border-t border-gray-100 bg-white/50">
            <div className="flex gap-3">
              <button 
                className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center hover:bg-gray-200 transition-colors flex-shrink-0"
                title="Voice input (coming soon)"
              >
                <Mic className="w-5 h-5 text-gray-600" />
              </button>
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={t.askQuestion}
                  className="w-full p-3 pr-12 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white"
                />
              </div>
              <button 
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              >
                <Send className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}