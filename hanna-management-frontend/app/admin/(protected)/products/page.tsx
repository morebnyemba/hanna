import Link from 'next/link';

// Mock data for products
const products = [
  {
    id: '1',
    name: 'Standard Solar Panel',
    sku: 'SOL-ST-250W',
    product_type: 'Hardware',
    category: 'Solar Panels',
    price: '250.00',
    is_active: true,
  },
  {
    id: '2',
    name: 'Premium Solar Panel',
    sku: 'SOL-PR-350W',
    product_type: 'Hardware',
    category: 'Solar Panels',
    price: '350.00',
    is_active: true,
  },
  {
    id: '3',
    name: 'Inverter',
    sku: 'INV-5KW',
    product_type: 'Hardware',
    category: 'Inverters',
    price: '800.00',
    is_active: true,
  },
  {
    id: '4',
    name: 'Battery Storage',
    sku: 'BAT-10KWH',
    product_type: 'Hardware',
    category: 'Batteries',
    price: '5000.00',
    is_active: false,
  },
];

export default function ProductsPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Products</h1>
          <Link href="/products/new">
            <a className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 w-full sm:w-auto justify-center">
              Add Product
            </a>
          </Link>
        </div>
        <div className="flex flex-col">
          <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
            <div className="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
              <div className="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
                {/* Table for medium screens and up */}
                <table className="min-w-full divide-y divide-gray-200 hidden md:table">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        SKU
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Category
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Price
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th scope="col" className="relative px-6 py-3">
                        <span className="sr-only">Edit</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {products.map((product) => (
                      <tr key={product.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{product.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{product.sku}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{product.product_type}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{product.category}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${product.price}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${product.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {product.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link href={`/products/${product.id}`}>
                            <a className="text-indigo-600 hover:text-indigo-900">Edit</a>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {/* Cards for small screens */}
                <div className="md:hidden">
                  {products.map((product) => (
                    <div key={product.id} className="bg-white shadow rounded-lg p-4 mb-4 border border-gray-200">
                      <div className="flex justify-between items-center">
                        <div className="text-sm font-medium text-gray-900">{product.name}</div>
                        <Link href={`/products/${product.id}`}>
                          <a className="text-indigo-600 hover:text-indigo-900 text-sm font-medium">Edit</a>
                        </Link>
                      </div>
                      <div className="text-sm text-gray-500 mt-1">{product.sku}</div>
                      <div className="text-sm text-gray-500 mt-1">{product.category}</div>
                      <div className="mt-2 flex justify-between items-center">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${product.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {product.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <div className="text-sm text-gray-500">${product.price}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
