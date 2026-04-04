import { BikeStation } from './Map';
import { Bike, CircleDot, Search, User, ChevronUp } from 'lucide-react';
import { useState } from 'react';

interface BottomBarProps {
  stations: BikeStation[];
  onStationSelect?: (station: BikeStation) => void;
  onAccountClick?: () => void;
}

function getStationColor(station: BikeStation): 'red' | 'green' | 'blue' | 'grey' {
  if (station.status === 'closed' || (station.availableBikes === 0 && station.availableDocks === 0)) {
    return 'grey';
  }
  if (station.availableBikes === 0) {
    return 'red';
  }
  if (station.availableDocks === 0) {
    return 'green';
  }
  return 'blue';
}

export function BottomBar({ stations, onStationSelect, onAccountClick }: BottomBarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  const filteredStations = stations.filter((station) =>
    station.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    station.address.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalBikes = stations.reduce((sum, s) => sum + s.availableBikes, 0);
  const openStations = stations.filter(s => s.status === 'open').length;

  return (
    <div className="bg-white border-t shadow-lg">
      {/* Main Bar */}
      <div className="px-6 py-3 flex items-center justify-between gap-4">
        {/* Left: Logo & Stats */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🚲</span>
            <span className="text-xl font-semibold text-gray-800" style={{ fontFamily: "'Palatino Linotype', 'Book Antiqua', Palatino, serif" }}>
              WheelyWise
            </span>
          </div>
          
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-gray-600">{openStations} Stations Open</span>
            </div>
            <div className="flex items-center gap-2">
              <Bike className="w-4 h-4 text-blue-600" />
              <span className="text-gray-600">{totalBikes} Bikes Available</span>
            </div>
          </div>
        </div>

        {/* Center: Search */}
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search stations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onFocus={() => setIsExpanded(true)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>
        </div>

        {/* Right: Account & Expand */}
        <div className="flex items-center gap-2">
          <button
            onClick={onAccountClick}
            className="flex items-center gap-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg transition-colors"
          >
            <User className="w-4 h-4" />
            <span className="text-sm font-medium">Account</span>
          </button>
          
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronUp className={`w-5 h-5 text-gray-600 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Expanded Station List */}
      {(isExpanded || searchTerm) && (
        <div className="border-t bg-gray-50 px-6 py-4 max-h-64 overflow-y-auto">
          <div className="grid grid-cols-4 gap-3">
            {filteredStations.slice(0, 12).map((station) => (
              <StationCard
                key={station.id}
                station={station}
                onClick={() => {
                  onStationSelect?.(station);
                  setIsExpanded(false);
                  setSearchTerm('');
                }}
              />
            ))}
          </div>
          {filteredStations.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              No stations found
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface StationCardProps {
  station: BikeStation;
  onClick?: () => void;
}

function StationCard({ station, onClick }: StationCardProps) {
  const color = getStationColor(station);
  
  const colorClasses = {
    red: 'border-red-300 bg-red-50',
    green: 'border-green-300 bg-green-50',
    blue: 'border-blue-300 bg-blue-50',
    grey: 'border-gray-300 bg-gray-50',
  };

  const dotColors = {
    red: 'bg-red-500',
    green: 'bg-green-500',
    blue: 'bg-blue-500',
    grey: 'bg-gray-400',
  };

  return (
    <button
      onClick={onClick}
      className={`text-left p-3 border-2 rounded-lg hover:shadow-md transition-all ${colorClasses[color]}`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div className={`w-2 h-2 rounded-full ${dotColors[color]} flex-shrink-0`}></div>
            <h3 className="font-semibold text-sm truncate">{station.name}</h3>
          </div>
          <p className="text-xs text-gray-600 truncate">{station.address}</p>
        </div>
      </div>

      {color !== 'grey' ? (
        <div className="flex items-center justify-between text-xs mt-2">
          <div className="flex items-center gap-1">
            <Bike className="w-3 h-3" />
            <span className="font-semibold">{station.availableBikes}</span>
          </div>
          <div className="text-gray-500">
            {station.availableDocks} docks
          </div>
        </div>
      ) : (
        <div className="text-xs text-gray-500 font-medium mt-2">
          No data
        </div>
      )}
    </button>
  );
}