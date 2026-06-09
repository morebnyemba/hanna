import Link from 'next/link';
import { FiSettings, FiLogIn, FiTool, FiShoppingBag, FiMapPin, FiArrowLeft } from 'react-icons/fi';

const portals = [
  { href: '/admin/login', icon: <FiSettings className="w-5 h-5" />, label: 'Admin Portal', description: 'System administration and management' },
  { href: '/client/login', icon: <FiLogIn className="w-5 h-5" />, label: 'Client Portal', description: 'Orders, warranties and installations' },
  { href: '/manufacturer/login', icon: <FiTool className="w-5 h-5" />, label: 'Manufacturer Portal', description: 'Product and warranty management' },
  { href: '/technician/login', icon: <FiTool className="w-5 h-5" />, label: 'Technician Portal', description: 'Job cards and installation tracking' },
  { href: '/retailer/login', icon: <FiShoppingBag className="w-5 h-5" />, label: 'Retailer Portal', description: 'Sales, orders and installations' },
  { href: '/retailer-branch/login', icon: <FiMapPin className="w-5 h-5" />, label: 'Branch Portal', description: 'Inventory and dispatch operations' },
];

export default function PortalsPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-xl">
        <Link
          href="/shop"
          className="inline-flex items-center gap-2 text-sm text-purple-600 hover:text-purple-800 font-semibold mb-8 transition"
        >
          <FiArrowLeft className="w-4 h-4" />
          Back to Shop
        </Link>

        <div className="mb-8 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-purple-600 to-purple-800 shadow mb-4">
            <span className="text-white font-bold text-lg">H</span>
          </div>
          <h1 className="text-2xl font-extrabold text-purple-900 mb-1">Business Portals</h1>
          <p className="text-gray-500 text-sm">Select your portal to log in</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {portals.map(({ href, icon, label, description }) => (
            <Link
              key={href}
              href={href}
              className="flex items-start gap-3 p-4 bg-white border border-purple-100 rounded-2xl hover:border-purple-400 hover:shadow-md transition group"
            >
              <div className="w-10 h-10 rounded-xl bg-purple-50 group-hover:bg-purple-100 flex items-center justify-center text-purple-600 flex-shrink-0 transition">
                {icon}
              </div>
              <div>
                <p className="font-bold text-purple-900 text-sm">{label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{description}</p>
              </div>
            </Link>
          ))}
        </div>

        <p className="text-center text-xs text-gray-400 mt-8">
          &copy; {new Date().getFullYear()} Pfungwa Technologies
        </p>
      </div>
    </div>
  );
}
