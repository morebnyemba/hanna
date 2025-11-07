
import Link from 'next/link';
import { FiBox, FiUsers, FiLogIn, FiShield, FiTool, FiSettings } from 'react-icons/fi';

const FeatureCard = ({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) => (
  <div className="bg-white/70 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/50 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
    <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center mx-auto mb-4">
      {icon}
    </div>
    <h3 className="font-semibold text-gray-900">{title}</h3>
    <p className="mt-2 text-sm text-gray-600">{description}</p>
  </div>
);

const PortalLink = ({ href, icon, label }: { href: string; icon: React.ReactNode; label:string }) => (
    <Link 
        href={href} 
        className="px-8 py-4 font-semibold text-white bg-gradient-to-r from-gray-800 to-gray-900 rounded-xl hover:from-gray-700 hover:to-gray-800 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-0.5 flex items-center justify-center"
    >
        {icon}
        {label}
    </Link>
)

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-32 w-80 h-80 bg-blue-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-32 w-80 h-80 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse animation-delay-4000"></div>
      </div>

      {/* Main content */}
      <div className="relative flex min-h-screen flex-col items-center justify-center text-center p-8">
        <div className="max-w-4xl">
          {/* Logo/Brand */}
          <div className="mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 shadow-lg mb-6">
              <span className="text-2xl font-bold text-white">H</span>
            </div>
            <h1 className="text-6xl md:text-7xl font-bold text-gray-900 mt-4 bg-gradient-to-r from-gray-900 to-indigo-900 bg-clip-text text-transparent">
              Hanna
            </h1>
            <p className="mt-2 text-lg font-medium text-gray-500">A Pfungwa Technologies Platform</p>
            <div className="w-24 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 mx-auto mt-4 rounded-full"></div>
          </div>

          {/* Tagline */}
          <p className="mt-6 text-xl md:text-2xl text-gray-700 max-w-3xl mx-auto leading-relaxed">
            The exclusive CRM platform for Pfungwa Technologies partners and affiliates,
            designed to streamline operations and enhance customer engagement.
          </p>

          {/* Feature highlights */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <FeatureCard icon={<FiUsers className="w-6 h-6 text-indigo-600" />} title="Customer Management" description="Streamline all customer interactions in one place" />
            <FeatureCard icon={<FiShield className="w-6 h-6 text-indigo-600" />} title="Warranty Management" description="Efficiently track and manage product warranties" />
            <FeatureCard icon={<FiBox className="w-6 h-6 text-indigo-600" />} title="Powerful Analytics" description="Gain insights with advanced data analytics" />
          </div>

          {/* CTA Buttons */}
          <div className="mt-12 flex flex-col sm:flex-row justify-center gap-4">
            <PortalLink href="/admin/login" icon={<FiSettings className="w-5 h-5 mr-2" />} label="Admin Login" />
            <PortalLink href="/client/login" icon={<FiLogIn className="w-5 h-5 mr-2" />} label="Client Login" />
          </div>

          {/* Additional portals section */}
          <div className="mt-16 bg-white/50 backdrop-blur-sm rounded-2xl p-8 shadow-lg border border-white/50 max-w-2xl mx-auto">
            <p className="text-gray-700 font-medium mb-4">Access your dedicated partner portal below.</p>
            <div className="flex flex-col sm:flex-row justify-center items-center gap-4">
                <PortalLink href="/manufacturer/login" icon={<FiTool className="w-4 h-4 mr-2" />} label="Manufacturer Portal" />
                <span className="hidden sm:block text-gray-400">&bull;</span>
                <PortalLink href="/technician/login" icon={<FiTool className="w-4 h-4 mr-2" />} label="Technician Portal" />
            </div>
          </div>

          {/* Footer note */}
          <div className="mt-12 text-sm text-gray-500">
            <p>&copy; {new Date().getFullYear()} Pfungwa Technologies. All rights reserved.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
