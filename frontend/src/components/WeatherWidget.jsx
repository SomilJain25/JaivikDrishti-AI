import { useEffect, useState } from "react";
import { Cloud, Droplets, Wind } from "lucide-react";

export default function WeatherWidget() {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWeather();
  }, []);

  const getWeather = () => {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;

          const apiKey =
            import.meta.env.VITE_OPENWEATHER_API_KEY;

          console.log("API KEY:", apiKey);

          const res = await fetch(
            `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&units=metric&appid=${apiKey}`
          );

          const data = await res.json();

          console.log("Weather API Response:", data);

          // Prevent crash if API fails
          if (data.cod !== 200) {
            console.error(
              "Weather API Error:",
              data.message
            );
            setWeather(null);
            return;
          }

          setWeather({
            city: data.name,
            temp: Math.round(data.main.temp),
            humidity: data.main.humidity,
            wind: Math.round(
              data.wind.speed * 3.6
            ),
            condition:
              data.weather[0].description,
          });
        } catch (err) {
          console.error("Weather error:", err);
          setWeather(null);
        } finally {
          setLoading(false);
        }
      },
      (error) => {
        console.error("Location error:", error);
        setLoading(false);
      }
    );
  };

  if (loading) {
    return (
      <div className="glass-card p-5">
        Loading weather...
      </div>
    );
  }

  if (!weather) {
    return (
      <div className="glass-card p-5">
        Weather unavailable
      </div>
    );
  }

  return (
    <div className="glass-card p-5 rounded-3xl">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-800">
          Weather
        </h2>

        <span className="text-sm bg-green-100 text-green-700 px-3 py-1 rounded-full">
          Live
        </span>
      </div>

      <div className="flex items-center gap-4 mb-5">
        <div className="w-16 h-16 rounded-2xl bg-blue-500 flex items-center justify-center">
          <Cloud className="text-white w-8 h-8" />
        </div>

        <div>
          <h3 className="text-4xl font-bold">
            {weather.temp}°C
          </h3>

          <p className="text-gray-600 capitalize">
            {weather.condition}
          </p>

          <p className="text-sm text-gray-500">
            {weather.city}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-100 rounded-2xl p-4">
          <div className="flex items-center gap-2 text-blue-600 mb-1">
            <Droplets className="w-4 h-4" />
            Humidity
          </div>
          <p className="font-bold">
            {weather.humidity}%
          </p>
        </div>

        <div className="bg-green-50 rounded-2xl p-4">
          <div className="flex items-center gap-2 text-green-600 mb-1">
            <Wind className="w-4 h-4" />
            Wind
          </div>
          <p className="font-bold">
            {weather.wind} km/h
          </p>
        </div>
      </div>
    </div>
  );
}