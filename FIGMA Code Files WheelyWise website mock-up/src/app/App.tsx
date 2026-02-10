import { useState } from 'react';
import { Map, BikeStation } from './components/Map';
import { WeatherBar } from './components/WeatherBar';
import { BottomBar } from './components/BottomBar';
import { AccountModal } from './components/AccountModal';
import { WelcomeModal } from './components/WelcomeModal';
import { StationPopupModal } from './components/StationPopupModal';
import { bikeStations } from './data/stations';

export default function App() {
  const [selectedStation, setSelectedStation] = useState<BikeStation | null>(null);
  const [isAccountModalOpen, setIsAccountModalOpen] = useState(false);
  const [isWelcomeModalOpen, setIsWelcomeModalOpen] = useState(true);

  const handleStationSelect = (station: BikeStation) => {
    setSelectedStation(station);
  };

  return (
    <div className="size-full flex flex-col">
      {/* Weather Bar */}
      <WeatherBar />

      {/* Map */}
      <div className="flex-1 overflow-hidden">
        <Map
          stations={bikeStations}
          onStationClick={handleStationSelect}
        />
      </div>

      {/* Bottom Bar */}
      <BottomBar
        stations={bikeStations}
        onStationSelect={handleStationSelect}
        onAccountClick={() => setIsAccountModalOpen(true)}
      />

      {/* Welcome Modal */}
      <WelcomeModal
        isOpen={isWelcomeModalOpen}
        onClose={() => setIsWelcomeModalOpen(false)}
      />

      {/* Station Popup Modal */}
      <StationPopupModal
        station={selectedStation}
        onClose={() => setSelectedStation(null)}
      />

      {/* Account Modal */}
      <AccountModal
        isOpen={isAccountModalOpen}
        onClose={() => setIsAccountModalOpen(false)}
      />
    </div>
  );
}