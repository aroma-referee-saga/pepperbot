import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { apiClient } from '../../services/api';
import CreateListModal from '../lists/CreateListModal';

interface ShoppingList {
  id: number;
  title: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

interface Discount {
  id: number;
  title: string;
  description?: string;
  store: string;
  original_price?: number;
  discount_price?: number;
  discount_percentage?: number;
  valid_until?: string;
  url?: string;
  image_url?: string;
  created_at: string;
}

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [shoppingLists, setShoppingLists] = useState<ShoppingList[]>([]);
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [isLoadingLists, setIsLoadingLists] = useState(true);
  const [isLoadingDiscounts, setIsLoadingDiscounts] = useState(true);
  const [error, setError] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    fetchShoppingLists();
    fetchDiscounts();
  }, []);

  const fetchShoppingLists = async () => {
    try {
      const response = await apiClient.getShoppingLists({ limit: 5 });
      setShoppingLists(response.data);
    } catch (err) {
      console.error('Failed to fetch shopping lists:', err);
    } finally {
      setIsLoadingLists(false);
    }
  };

  const fetchDiscounts = async () => {
    try {
      const response = await apiClient.getDiscounts({ limit: 6 });
      setDiscounts(response.data);
    } catch (err) {
      console.error('Failed to fetch discounts:', err);
    } finally {
      setIsLoadingDiscounts(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const handleListCreated = () => {
    fetchShoppingLists(); // Refresh the shopping lists
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">PepperBot</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Welcome, {user?.username}</span>
              <button
                onClick={logout}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Error message */}
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Shopping Lists Section */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Your Shopping Lists</h2>
              <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                Create New List
              </button>
            </div>

            {isLoadingLists ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : shoppingLists.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {shoppingLists.map((list) => (
                  <div key={list.id} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{list.title}</h3>
                    {list.description && (
                      <p className="text-gray-600 text-sm mb-3">{list.description}</p>
                    )}
                    <div className="flex justify-between items-center text-sm text-gray-500">
                      <span>Created {formatDate(list.created_at)}</span>
                      <button className="text-indigo-600 hover:text-indigo-800">View</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-600 mb-4">No shopping lists yet</p>
                <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                  Create Your First List
                </button>
              </div>
            )}
          </div>

          {/* Recent Discounts Section */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Recent Discounts</h2>
              <button className="text-indigo-600 hover:text-indigo-800 text-sm font-medium">
                View All
              </button>
            </div>

            {isLoadingDiscounts ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="bg-white rounded-lg shadow p-4 animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                    <div className="h-6 bg-gray-200 rounded w-1/4"></div>
                  </div>
                ))}
              </div>
            ) : discounts.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {discounts.map((discount) => (
                  <div key={discount.id} className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{discount.title}</h3>
                      <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                        {discount.store}
                      </span>
                    </div>

                    {discount.description && (
                      <p className="text-gray-600 text-sm mb-3">{discount.description}</p>
                    )}

                    <div className="flex justify-between items-center">
                      <div className="flex space-x-2">
                        {discount.discount_price && (
                          <span className="text-lg font-bold text-green-600">
                            {formatPrice(discount.discount_price)}
                          </span>
                        )}
                        {discount.original_price && discount.discount_price && (
                          <span className="text-sm text-gray-500 line-through">
                            {formatPrice(discount.original_price)}
                          </span>
                        )}
                        {discount.discount_percentage && (
                          <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">
                            {discount.discount_percentage}% off
                          </span>
                        )}
                      </div>

                      {discount.url && (
                        <a
                          href={discount.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-800 text-sm"
                        >
                          View Deal
                        </a>
                      )}
                    </div>

                    {discount.valid_until && (
                      <p className="text-xs text-gray-500 mt-2">
                        Valid until {formatDate(discount.valid_until)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-600">No discounts available at the moment</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;