'use client';

import { useEffect, useState } from 'react';
import { FiSun, FiShoppingCart, FiPackage, FiDollarSign, FiInfo } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import { useRouter } from 'next/navigation';

interface Product {
  id: string;
  name: string;
  quantity: number;
}

interface SolarPackage {
  id: string;
  name: string;
  system_size: number;
  description: string;
  price: string;
  currency: string;
  is_active: boolean;
  included_products: Product[];
  compatibility_rules?: any;
}

export default function RetailerSolarPackagesPage() {
  const [packages, setPackages] = useState<SolarPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    const fetchPackages = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/users/retailer/solar-packages/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch solar packages. Status: ${response.status}`);
        }

        const result = await response.json();
        setPackages(result.results || result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchPackages();
    }
  }, [accessToken]);

  const handleCreateOrder = (packageId: string) => {
    router.push(`/retailer/orders/new?package=${packageId}`);
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow h-96"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiSun className="mr-3 h-8 w-8 text-yellow-500" />
          Solar Packages
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Browse and order pre-configured solar system packages for your customers.
        </p>
      </div>

      {packages.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiPackage className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No packages available</h3>
          <p className="mt-1 text-sm text-gray-500">
            There are currently no active solar packages. Please check back later.
          </p>
        </div>
      ) : (
        <>
          <div className="mb-6 bg-blue-50 border border-blue-200 p-4 rounded-lg flex items-start">
            <FiInfo className="h-5 w-5 text-blue-600 mr-3 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-blue-800">
                Pre-Approved Solar Packages
              </p>
              <p className="text-xs text-blue-700 mt-1">
                These packages are pre-configured with compatible components. Select a package to create
                an order for your customer.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {packages.map((pkg) => (
              <div
                key={pkg.id}
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow overflow-hidden flex flex-col"
              >
                {/* Package Header */}
                <div className="bg-gradient-to-r from-yellow-500 to-orange-500 p-6 text-white">
                  <div className="flex items-center justify-between">
                    <FiSun className="h-8 w-8" />
                    <span className="text-2xl font-bold">{pkg.system_size} kW</span>
                  </div>
                  <h3 className="text-xl font-bold mt-3">{pkg.name}</h3>
                </div>

                {/* Package Body */}
                <div className="p-6 flex-1 flex flex-col">
                  <p className="text-gray-600 text-sm mb-4">{pkg.description}</p>

                  {/* Price */}
                  <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Package Price</span>
                      <div className="flex items-center">
                        <FiDollarSign className="h-5 w-5 text-green-600" />
                        <span className="text-2xl font-bold text-gray-900 ml-1">
                          {parseFloat(pkg.price).toLocaleString()}
                        </span>
                        <span className="text-sm text-gray-600 ml-1">{pkg.currency}</span>
                      </div>
                    </div>
                  </div>

                  {/* Included Products */}
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                      <FiPackage className="mr-2" />
                      Included Components
                    </h4>
                    <div className="space-y-2">
                      {pkg.included_products.map((product, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between text-sm bg-gray-50 p-2 rounded"
                        >
                          <span className="text-gray-700">{product.name}</span>
                          <span className="text-gray-500">× {product.quantity}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Order Button */}
                  <button
                    onClick={() => handleCreateOrder(pkg.id)}
                    className="mt-auto w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg flex items-center justify-center transition-colors"
                  >
                    <FiShoppingCart className="mr-2" />
                    Create Order
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
