import { X, Bike, CircleDot, TrendingUp, Cloud } from 'lucide-react';
import { BikeStation } from './Map';

interface StationPopupModalProps {
  station: BikeStation | null;
  onClose: () => void;
}

function getStationColor(station: BikeStation): 'red' | 'green' | 'blue' | 'grey' {
  if (station.status === 'closed' || (station.availableBikes === 0 && station.availableDocks === 0)) {
    return 'grey';
  }
  if (station.availableBikes === 0) {
    return 'red';
  }
  if (station.availableDocks === 0) {
    return 'blue';
  }
  return 'green';
}

// Generate predictive availability based on station ID (varies per station)
function getPredictiveAvailability(station: BikeStation): string {
  const predictions = [
    '8 bikes expected',
    '12 bikes expected',
    '5 bikes expected',
    '15 bikes expected',
    '3 bikes expected',
    '10 bikes expected',
    '6 bikes expected',
    '14 bikes expected',
    '20 bikes expected',
    '7 bikes expected',
    '4 bikes expected',
    '9 bikes expected',
    '11 bikes expected',
    '2 bikes expected',
    '13 bikes expected',
    '16 bikes expected',
    '18 bikes expected',
    '10 bikes expected',
    '5 bikes expected',
    '1 bike expected'
  ];
  return predictions[(station.id - 1) % predictions.length];
}

// Generate weather condition based on station ID (varies per station)
function getStationWeather(station: BikeStation): string {
  const weatherConditions = [
    'Partly cloudy, 12°C',
    'Sunny, 14°C',
    'Light rain, 11°C',
    'Cloudy, 13°C',
    'Clear, 15°C',
    'Overcast, 12°C',
    'Drizzle, 10°C',
    'Partly sunny, 14°C',
    'Mostly cloudy, 11°C',
    'Fair, 13°C',
    'Light wind, 12°C',
    'Breezy, 13°C',
    'Calm, 14°C',
    'Cloudy, 12°C',
    'Clear sky, 15°C',
    'Scattered clouds, 13°C',
    'Mild, 14°C',
    'Cool, 11°C',
    'Pleasant, 13°C',
    'Gentle breeze, 12°C'
  ];
  return weatherConditions[(station.id - 1) % weatherConditions.length];
}

export function StationPopupModal({ station, onClose }: StationPopupModalProps) {
  if (!station) return null;

  const color = getStationColor(station);
  
  const colorClasses = {
    red: 'bg-red-50 border-red-300',
    green: 'bg-green-50 border-green-300',
    blue: 'bg-blue-50 border-blue-300',
    grey: 'bg-gray-50 border-gray-300',
  };

  const statusColors = {
    red: '#dc2626',
    green: '#16a34a',
    blue: '#2563eb',
    grey: '#9ca3af',
  };

  let statusText = '';
  if (color === 'grey') {
    statusText = 'No data available';
  } else if (color === 'red') {
    statusText = 'No bikes available';
  } else if (color === 'blue') {
    statusText = 'Full - No docks available';
  } else {
    statusText = 'Bikes & docks available';
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <div 
              className="w-8 h-8 rounded-full flex items-center justify-center" 
              style={{ backgroundColor: statusColors[color] }}
            >
              <span className="text-lg">🚲</span>
            </div>
            <div>
              <h2 className="font-semibold">{station.name}</h2>
              <p className="text-xs text-gray-500">{station.address}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Status Badge */}
          <div className={`px-3 py-2 rounded-lg border-2 ${colorClasses[color]}`}>
            <span className="text-sm font-semibold" style={{ color: statusColors[color] }}>
              {statusText}
            </span>
          </div>

          {/* Availability Info */}
          {color !== 'grey' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <Bike className="w-5 h-5 text-blue-600" />
                  <span className="text-sm text-gray-600">Available Bikes</span>
                </div>
                <span className="text-xl font-bold text-gray-900">{station.availableBikes}</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CircleDot className="w-5 h-5 text-purple-600" />
                  <span className="text-sm text-gray-600">Available Docks</span>
                </div>
                <span className="text-xl font-bold text-gray-900">{station.availableDocks}</span>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-gray-600">
                  <span>Capacity</span>
                  <span>{station.totalDocks} total docks</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${(station.availableBikes / station.totalDocks) * 100}%` }}
                  />
                </div>
              </div>

              {/* Predictive Availability */}
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg border border-purple-200">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-purple-600" />
                  <span className="text-sm text-gray-600">Next hour</span>
                </div>
                <span className="text-sm font-semibold text-purple-700">{getPredictiveAvailability(station)}</span>
              </div>

              {/* Weather */}
              <div className="flex items-center justify-between p-3 bg-sky-50 rounded-lg border border-sky-200">
                <div className="flex items-center gap-2">
                  <Cloud className="w-5 h-5 text-sky-600" />
                  <span className="text-sm text-gray-600">Weather</span>
                </div>
                <span className="text-sm font-semibold text-sky-700">{getStationWeather(station)}</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer - Book Button */}
        {color !== 'grey' && (
          <div className="p-4 border-t">
            <button 
              disabled={station.availableBikes === 0}
              className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-semibold transition-colors ${
                station.availableBikes > 0 
                  ? 'bg-blue-600 text-white hover:bg-blue-700' 
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              <Bike className="w-5 h-5" />
              {station.availableBikes > 0 ? 'Book Bike' : 'No Bikes Available'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}