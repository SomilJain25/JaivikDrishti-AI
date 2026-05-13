import { useEffect, useState } from 'react'
import { Cloud, Sun, CloudRain, Droplets, Wind, Thermometer } from 'lucide-react'
import { getWeather } from '../services/api'

const weatherIcons = {
  'sun': Sun,
  'cloud': Cloud,
  'rain': CloudRain,
}

export default function WeatherWidget() {
  const [weather, setWeather] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    loadWeather()
  }, [])
  
  const loadWeather = async () => {
    try {
      const data = await getWeather()
      setWeather(data)
    } catch (error) {
      console.error('Weather load failed:', error)
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return (
      <div className="glass-card p-5 animate-pulse">
        <div className="h-20 bg-gray-200 rounded-xl" />
      </div>
    )
  }
  
  const CurrentIcon = weatherIcons[weather.forecast[0].icon] || Cloud
  
  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-gray-800 flex items-center gap-2">
          <Cloud className="w-5 h-5 text-blue-500" />
          Weather
        </h3>
        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
          Live
        </span>
      </div>
      
      {/* Current */}
      <div className="flex items-center gap-4 mb-4">
        <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-2xl 
                      flex items-center justify-center shadow-lg">
          <CurrentIcon className="w-8 h-8 text-white" />
        </div>
        <div>
          <div className="text-3xl font-bold text-gray-800">{weather.temp}°C</div>
          <div className="text-sm text-gray-600">{weather.condition}</div>
        </div>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-blue-50 rounded-xl p-3 flex items-center gap-2">
          <Droplets className="w-4 h-4 text-blue-500" />
          <div>
            <div className="text-xs text-gray-500">Humidity</div>
            <div className="font-semibold text-sm">{weather.humidity}%</div>
          </div>
        </div>
        <div className="bg-green-50 rounded-xl p-3 flex items-center gap-2">
          <Wind className="w-4 h-4 text-green-500" />
          <div>
            <div className="text-xs text-gray-500">Wind</div>
            <div className="font-semibold text-sm">{weather.windSpeed} km/h</div>
          </div>
        </div>
      </div>
      
      {/* Forecast */}
      <div className="flex gap-2">
        {weather.forecast.map((day, idx) => {
          const DayIcon = weatherIcons[day.icon] || Cloud
          return (
            <div key={idx} className="flex-1 bg-gray-50 rounded-xl p-2 text-center">
              <div className="text-xs text-gray-500 mb-1">{day.day}</div>
              <DayIcon className="w-5 h-5 mx-auto mb-1 text-gray-600" />
              <div className="text-sm font-semibold">{day.temp}°</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}