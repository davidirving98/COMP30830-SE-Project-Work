import { X, User, Mail, Phone, CreditCard, MapPin, Calendar } from 'lucide-react';

interface AccountModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AccountModal({ isOpen, onClose }: AccountModalProps) {
  if (!isOpen) return null;

  // Mock user data for Michael
  const user = {
    name: 'Michael O\'Brien',
    email: 'michael.obrien@email.ie',
    phone: '+353 85 123 4567',
    memberSince: 'January 2023',
    totalRides: 127,
    favoriteStation: 'Trinity College',
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="flex items-center gap-2">
            <User className="w-5 h-5 text-blue-600" />
            <span>My Account</span>
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Profile Picture */}
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          {/* User Info */}
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
              <User className="w-5 h-5 text-gray-500" />
              <div>
                <div className="text-xs text-gray-500">Name</div>
                <div className="font-medium">{user.name}</div>
              </div>
            </div>

            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
              <Mail className="w-5 h-5 text-gray-500" />
              <div>
                <div className="text-xs text-gray-500">Email</div>
                <div className="font-medium">{user.email}</div>
              </div>
            </div>

            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
              <Phone className="w-5 h-5 text-gray-500" />
              <div>
                <div className="text-xs text-gray-500">Phone</div>
                <div className="font-medium">{user.phone}</div>
              </div>
            </div>

            {/* Payment Methods */}
            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
              <CreditCard className="w-5 h-5 text-gray-500" />
              <div className="flex-1">
                <div className="text-xs text-gray-500 mb-1">Payment Methods</div>
                <div className="flex gap-2">
                  <img 
                    src="https://upload.wikimedia.org/wikipedia/commons/b/b0/Apple_Pay_logo.svg" 
                    alt="Apple Pay" 
                    className="h-5"
                  />
                  <img 
                    src="https://upload.wikimedia.org/wikipedia/commons/f/f2/Google_Pay_Logo.svg" 
                    alt="Google Pay" 
                    className="h-5"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
              <Calendar className="w-5 h-5 text-gray-500" />
              <div>
                <div className="text-xs text-gray-500">Member Since</div>
                <div className="font-medium">{user.memberSince}</div>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="p-3 bg-blue-50 rounded-lg text-center">
              <div className="text-2xl font-semibold text-blue-700">{user.totalRides}</div>
              <div className="text-xs text-gray-600 mt-1">Total Rides</div>
            </div>
            <div className="p-3 bg-green-50 rounded-lg text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <MapPin className="w-4 h-4 text-green-600" />
              </div>
              <div className="text-xs font-medium text-gray-700">{user.favoriteStation}</div>
              <div className="text-xs text-gray-600 mt-1">Favorite Station</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t flex gap-3">
          <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            Edit Profile
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}