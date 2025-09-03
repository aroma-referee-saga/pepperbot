import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../services/api';

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

const DiscountsPage: React.FC = () => {
  const navigate = useNavigate();
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [filteredDiscounts, setFilteredDiscounts] = useState<Discount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStore, setSelectedStore] = useState('');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'price-low' | 'price-high' | 'discount'>('newest');

  useEffect(() => {
    fetchDiscounts();
  }, []);

  useEffect(() => {
    filterAndSortDiscounts();
  }, [discounts, searchTerm, selectedStore, sortBy]);

  const fetchDiscounts = async () => {
    try {
      const response = await apiClient.getDiscounts({ limit: 100 });
      setDiscounts(response.data);
    } catch (err: any) {
      setError('Failed to load discounts');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const filterAndSortDiscounts = () => {
    let filtered = discounts.filter((discount) => {
      const matchesSearch = discount.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           discount.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           discount.store.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStore = !selectedStore || discount.store === selectedStore;

      return matchesSearch && matchesStore;
    });

    // Sort discounts
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'oldest':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'price-low':
          return (a.discount_price || 0) - (b.discount_price || 0);
        case 'price-high':
          return (b.discount_price || 0) - (a.discount_price || 0);
        case 'discount':
          return (b.discount_percentage || 0) - (a.discount_percentage || 0);
        default:
          return 0;
      }
    });

    setFilteredDiscounts(filtered);
  };

  const getUniqueStores = () => {
    const stores = discounts.map(discount => discount.store);
    return Array.from(new Set(stores)).sort();
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

  const getSavings = (discount: Discount) => {
    if (discount.original_price && discount.discount_price) {
      return discount.original_price - discount.discount_price;
    }
    return 0;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-600 hover:text-gray-900 mr-4"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-xl font-semibold text-gray-900">Discounts</h1>
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

          {/* Filters and Search */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
                  Search
                </label>
                <input
                  type="text"
                  id="search"
                  placeholder="Search discounts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              {/* Store Filter */}
              <div>
                <label htmlFor="store" className="block text-sm font-medium text-gray-700 mb-1">
                  Store
                </label>
                <select
                  id="store"
                  value={selectedStore}
                  onChange={(e) => setSelectedStore(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">All Stores</option>
                  {getUniqueStores().map((store) => (
                    <option key={store} value={store}>
                      {store}
                    </option>
                  ))}
                </select>
              </div>

              {/* Sort */}
              <div>
                <label htmlFor="sort" className="block text-sm font-medium text-gray-700 mb-1">
                  Sort by
                </label>
                <select
                  id="sort"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="newest">Newest</option>
                  <option value="oldest">Oldest</option>
                  <option value="price-low">Price: Low to High</option>
                  <option value="price-high">Price: High to Low</option>
                  <option value="discount">Highest Discount</option>
                </select>
              </div>
            </div>
          </div>

          {/* Results Summary */}
          <div className="mb-4">
            <p className="text-gray-600">
              Showing {filteredDiscounts.length} of {discounts.length} discounts
            </p>
          </div>

          {/* Discounts Grid */}
          {filteredDiscounts.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No discounts found</h3>
              <p className="text-gray-600">Try adjusting your search or filter criteria.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredDiscounts.map((discount) => (
                <div key={discount.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                  {/* Discount Image */}
                  {discount.image_url && (
                    <div className="h-48 bg-gray-200">
                      <img
                        src={discount.image_url}
                        alt={discount.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    </div>
                  )}

                  <div className="p-6">
                    {/* Store Badge */}
                    <div className="flex justify-between items-start mb-3">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {discount.store}
                      </span>
                      {discount.discount_percentage && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          {discount.discount_percentage}% OFF
                        </span>
                      )}
                    </div>

                    {/* Title and Description */}
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{discount.title}</h3>
                    {discount.description && (
                      <p className="text-gray-600 text-sm mb-4 line-clamp-2">{discount.description}</p>
                    )}

                    {/* Pricing */}
                    <div className="mb-4">
                      {discount.discount_price && (
                        <div className="flex items-baseline space-x-2">
                          <span className="text-2xl font-bold text-green-600">
                            {formatPrice(discount.discount_price)}
                          </span>
                          {discount.original_price && (
                            <>
                              <span className="text-lg text-gray-500 line-through">
                                {formatPrice(discount.original_price)}
                              </span>
                              <span className="text-sm text-green-600 font-medium">
                                Save {formatPrice(getSavings(discount))}
                              </span>
                            </>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Valid Until */}
                    {discount.valid_until && (
                      <div className="text-sm text-gray-600 mb-4">
                        Valid until {formatDate(discount.valid_until)}
                      </div>
                    )}

                    {/* Action Button */}
                    {discount.url ? (
                      <a
                        href={discount.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md text-center block transition-colors"
                      >
                        View Deal
                      </a>
                    ) : (
                      <button className="w-full bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md transition-colors">
                        View Details
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default DiscountsPage;