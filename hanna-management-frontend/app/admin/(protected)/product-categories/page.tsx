import Link from 'next/link';

// Mock data for product categories
const categories = [
  {
    id: '1',
    name: 'Solar Panels',
    description: 'High-efficiency solar panels for residential and commercial use.',
  },
  {
    id: '2',
    name: 'Inverters',
    description: 'Inverters to convert DC to AC power.',
  },
  {
    id: '3',
    name: 'Batteries',
    description: 'Energy storage solutions.',
  },
];

export default function ProductCategoriesPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Product Categories</h1>
          <Link href="/product-categories/new">
            <a className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 w-full sm:w-auto justify-center">
              Add Category
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
                        Description
                      </th>
                      <th scope="col" className="relative px-6 py-3">
                        <span className="sr-only">Edit</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {categories.map((category) => (
                      <tr key={category.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{category.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{category.description}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link href={`/product-categories/${category.id}`}>
                            <a className="text-indigo-600 hover:text-indigo-900">Edit</a>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {/* Cards for small screens */}
                <div className="md:hidden">
                  {categories.map((category) => (
                    <div key={category.id} className="bg-white shadow rounded-lg p-4 mb-4 border border-gray-200">
                      <div className="flex justify-between items-center">
                        <div className="text-sm font-medium text-gray-900">{category.name}</div>
                        <Link href={`/product-categories/${category.id}`}>
                          <a className="text-indigo-600 hover:text-indigo-900 text-sm font-medium">Edit</a>
                        </Link>
                      </div>
                      <div className="text-sm text-gray-500 mt-1">{category.description}</div>
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
