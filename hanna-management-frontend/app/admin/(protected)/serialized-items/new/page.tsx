import Link from 'next/link';

export default function NewSerializedItemPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-3xl mx-auto bg-white p-4 sm:p-6 lg:p-8 rounded-lg shadow-md">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-8">Add New Serialized Item</h1>
        <form className="space-y-8 divide-y divide-gray-200">
          <div className="space-y-6 sm:space-y-5">
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900">Item Information</h3>
            </div>
            <div className="mt-6 sm:mt-5 space-y-6 sm:space-y-5">
              <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 sm:pt-5">
                <label htmlFor="serial_number" className="block text-sm font-medium text-gray-700 sm:mt-px sm:pt-2">
                  Serial Number
                </label>
                <div className="mt-1 sm:mt-0 sm:col-span-2">
                  <input
                    type="text"
                    name="serial_number"
                    id="serial_number"
                    className="max-w-lg block w-full shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:max-w-xs sm:text-sm border-gray-300 rounded-md"
                  />
                </div>
              </div>

              <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 sm:pt-5">
                <label htmlFor="product" className="block text-sm font-medium text-gray-700 sm:mt-px sm:pt-2">
                  Product
                </label>
                <div className="mt-1 sm:mt-0 sm:col-span-2">
                  <select
                    id="product"
                    name="product"
                    className="max-w-lg block focus:ring-indigo-500 focus:border-indigo-500 w-full shadow-sm sm:max-w-xs sm:text-sm border-gray-300 rounded-md"
                  >
                    <option>Standard Solar Panel</option>
                    <option>Premium Solar Panel</option>
                    <option>Inverter</option>
                    <option>Battery Storage</option>
                  </select>
                </div>
              </div>

              <div className="sm:grid sm:grid-cols-3 sm:gap-4 sm:items-start sm:border-t sm:border-gray-200 sm:pt-5">
                <label htmlFor="status" className="block text-sm font-medium text-gray-700 sm:mt-px sm:pt-2">
                  Status
                </label>
                <div className="mt-1 sm:mt-0 sm:col-span-2">
                  <select
                    id="status"
                    name="status"
                    className="max-w-lg block focus:ring-indigo-500 focus:border-indigo-500 w-full shadow-sm sm:max-w-xs sm:text-sm border-gray-300 rounded-md"
                  >
                    <option>In Stock</option>
                    <option>Sold</option>
                    <option>In Repair</option>
                    <option>Returned</option>
                    <option>Decommissioned</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-5">
            <div className="flex flex-col-reverse sm:flex-row justify-end gap-2">
              <Link href="/serialized-items">
                <a className="w-full sm:w-auto justify-center bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                  Cancel
                </a>
              </Link>
              <button
                type="submit"
                className="w-full sm:w-auto justify-center ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Save
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
