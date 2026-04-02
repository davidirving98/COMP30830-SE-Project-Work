import { Cloud, CloudRain, Sun, Wind } from 'lucide-react';

export function WeatherBar() {
  // Mock weather data for Dublin
  const weather = {
    temperature: 12,
    condition: 'Partly Cloudy',
    windSpeed: 15,
    humidity: 68,
  };

  return (
    <div className="bg-white border-b px-6 py-3 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <Cloud className="w-5 h-5 text-gray-600" />
          <span className="text-sm">Dublin City Centre</span>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Sun className="w-5 h-5 text-orange-500" />
            <span className="font-semibold">{weather.temperature}°C</span>
          </div>
          
          <div className="h-4 w-px bg-gray-300"></div>
          
          <span className="text-sm text-gray-600">{weather.condition}</span>
          
          <div className="h-4 w-px bg-gray-300"></div>
          
          <div className="flex items-center gap-1.5">
            <Wind className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">{weather.windSpeed} km/h</span>
          </div>
          
          <div className="h-4 w-px bg-gray-300"></div>
          
          <div className="flex items-center gap-1.5">
            <CloudRain className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">{weather.humidity}%</span>
          </div>
        </div>
      </div>
      
      <div className="text-xs text-gray-500">
        Last updated: {new Date().toLocaleTimeString('en-IE', { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  );
}