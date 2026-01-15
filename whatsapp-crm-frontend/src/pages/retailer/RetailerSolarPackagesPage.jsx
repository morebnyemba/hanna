// src/pages/retailer/RetailerSolarPackagesPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import retailerAPI from '../../services/retailer';
import { Package, DollarSign, Zap, ShoppingCart } from 'lucide-react';

const RetailerSolarPackagesPage = () => {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadPackages();
  }, []);

  const loadPackages = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await retailerAPI.getSolarPackages();
      setPackages(data.results || data || []);
    } catch (err) {
      console.error('Error loading solar packages:', err);
      setError(err.message || 'Failed to load solar packages');
      toast.error('Failed to load solar packages');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrder = (packageId) => {
    navigate(`/retailer/orders/new?package=${packageId}`);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading solar packages...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <h3 className="text-red-800 dark:text-red-200 font-semibold mb-2">Error Loading Packages</h3>
          <p className="text-red-600 dark:text-red-300">{error}</p>
          <button
            onClick={loadPackages}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Solar Packages
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Browse and sell our pre-configured solar system packages
        </p>
      </div>

      {/* Packages Grid */}
      {packages.length === 0 ? (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-8 text-center">
          <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No Solar Packages Available
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            There are currently no active solar packages to display.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {packages.map((pkg) => (
            <div
              key={pkg.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow"
            >
              {/* Package Header */}
              <div className="bg-gradient-to-r from-blue-600 to-blue-700 dark:from-blue-700 dark:to-blue-800 p-6">
                <h3 className="text-xl font-bold text-white mb-2">{pkg.name}</h3>
                <div className="flex items-center text-blue-100">
                  <Zap className="w-5 h-5 mr-2" />
                  <span className="text-lg font-semibold">{pkg.system_size} kW</span>
                </div>
              </div>

              {/* Package Body */}
              <div className="p-6">
                {/* Description */}
                {pkg.description && (
                  <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-3">
                    {pkg.description}
                  </p>
                )}

                {/* Products Included */}
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                    Included Products:
                  </h4>
                  <div className="space-y-1">
                    {pkg.package_products?.map((pp) => (
                      <div
                        key={pp.id}
                        className="text-sm text-gray-600 dark:text-gray-400 flex items-center"
                      >
                        <span className="w-8 text-right mr-2 font-medium">
                          {pp.quantity}x
                        </span>
                        <span>{pp.product?.name || 'Product'}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    Total: {pkg.total_products || 0} items
                  </p>
                </div>

                {/* Price */}
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Package Price:</span>
                    <div className="flex items-center text-2xl font-bold text-gray-900 dark:text-white">
                      <DollarSign className="w-5 h-5" />
                      <span>{parseFloat(pkg.price).toLocaleString()}</span>
                      <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-1">
                        {pkg.currency}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Action Button */}
                <button
                  onClick={() => handleCreateOrder(pkg.id)}
                  className="w-full bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center"
                >
                  <ShoppingCart className="w-5 h-5 mr-2" />
                  Create Order
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RetailerSolarPackagesPage;
