import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export interface BikeStation {
  id: number;
  name: string;
  address: string;
  lat: number;
  lng: number;
  availableBikes: number;
  availableDocks: number;
  totalDocks: number;
  status: 'open' | 'closed';
}

interface MapProps {
  stations: BikeStation[];
  onStationClick?: (station: BikeStation) => void;
}

// Helper function to determine station status color
function getStationColor(station: BikeStation): 'red' | 'green' | 'blue' | 'grey' {
  if (station.status === 'closed' || (station.availableBikes === 0 && station.availableDocks === 0)) {
    return 'grey'; // No data available
  }
  if (station.availableBikes === 0) {
    return 'red'; // Empty of bikes
  }
  if (station.availableDocks === 0) {
    return 'blue'; // Full of bikes
  }
  return 'green'; // Mix of bikes and docks
}

export function Map({ stations, onStationClick }: MapProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.Marker[]>([]);

  useEffect(() => {
    // Initialize map
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current).setView([53.3498, -6.2603], 13);
    mapRef.current = map;

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;

    const map = mapRef.current;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Color mapping
    const colorMap = {
      red: '#dc2626',
      green: '#16a34a',
      blue: '#2563eb',
      grey: '#9ca3af',
    };

    // Add markers for stations
    stations.forEach((station) => {
      const color = getStationColor(station);
      const bgColor = colorMap[color];
      
      // Create custom div icon with bike emoji
      const customIcon = L.divIcon({
        html: `<div style="width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background-color: ${bgColor}; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-size: 18px;">🚲</div>`,
        className: '',
        iconSize: [36, 36],
        iconAnchor: [18, 18],
        popupAnchor: [0, -20],
      });

      const marker = L.marker([station.lat, station.lng], {
        icon: customIcon,
      });

      let statusText = '';
      let statusColor = '';
      
      if (color === 'grey') {
        statusText = 'No data available';
        statusColor = '#6b7280';
      } else if (color === 'red') {
        statusText = 'No bikes available';
        statusColor = '#dc2626';
      } else if (color === 'blue') {
        statusText = 'Full - No docks available';
        statusColor = '#2563eb';
      } else {
        statusText = 'Bikes & docks available';
        statusColor = '#16a34a';
      }

      const popupContent = `
        <div style="padding: 8px; min-width: 220px;">
          <h3 style="font-weight: 600; margin-bottom: 4px; font-size: 1rem;">${station.name}</h3>
          <p style="font-size: 0.875rem; color: #4b5563; margin-bottom: 8px;">${station.address}</p>
          ${
            color !== 'grey'
              ? `
            <div style="padding: 6px 10px; background-color: ${color === 'red' ? '#fee2e2' : color === 'blue' ? '#dbeafe' : '#dcfce7'}; border-radius: 6px; margin-bottom: 8px;">
              <span style="font-size: 0.875rem; color: ${statusColor}; font-weight: 600;">${statusText}</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px;">
              <div style="display: flex; justify-content: space-between; font-size: 0.875rem;">
                <span>Available Bikes:</span>
                <span style="font-weight: 600; color: ${color === 'blue' ? '#2563eb' : '#1f2937'};">${station.availableBikes}</span>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 0.875rem;">
                <span>Available Docks:</span>
                <span style="font-weight: 600; color: ${color === 'red' ? '#dc2626' : '#1f2937'};">${station.availableDocks}</span>
              </div>
              <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid #e5e7eb; font-size: 0.75rem; color: #6b7280;">
                Total: ${station.totalDocks} docks
              </div>
            </div>
          `
              : `<div style="padding: 6px 10px; background-color: #f3f4f6; border-radius: 6px;">
              <span style="font-size: 0.875rem; color: ${statusColor}; font-weight: 600;">${statusText}</span>
            </div>`
          }
        </div>
      `;

      marker.bindPopup(popupContent);

      marker.on('click', () => {
        if (onStationClick) {
          onStationClick(station);
        }
      });

      marker.addTo(map);
      markersRef.current.push(marker);
    });
  }, [stations, onStationClick]);

  return <div ref={mapContainerRef} className="w-full h-full relative z-0" />;
}