'use client';

import { FiSun, FiWifi, FiPackage, FiShield, FiMessageCircle, FiChevronRight } from 'react-icons/fi';

interface HeroBannerProps {
  whatsappNumber: string;
  onShopNow: () => void;
}

export default function HeroBanner({ whatsappNumber, onShopNow }: HeroBannerProps) {
  const waLink = whatsappNumber
    ? `https://wa.me/${whatsappNumber}?text=${encodeURIComponent('Hi, I would like a free quote on a solar system or furniture.')}`
    : null;

  return (
    <section className="relative overflow-hidden bg-white rounded-2xl border border-purple-100 shadow-sm mb-8">
      {/* Background decoration */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full bg-orange-100 opacity-50" />
        <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-sky-100 opacity-60" />
        <div className="absolute top-1/2 right-1/4 w-32 h-32 rounded-full bg-purple-100 opacity-40" />
      </div>

      <div className="relative max-w-7xl mx-auto px-6 sm:px-10 py-10 sm:py-14 flex flex-col md:flex-row items-center gap-8">
        {/* Text */}
        <div className="flex-1 text-center md:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 border border-orange-200 text-orange-600 text-xs font-semibold mb-4">
            <FiSun className="w-3.5 h-3.5" />
            Zimbabwe's Premium Shop
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-purple-900 leading-tight mb-3">
            Solar, Furniture &amp; Tech —<br className="hidden sm:block" />
            <span className="text-orange-500">Delivered to Your Door</span>
          </h1>
          <p className="text-gray-600 text-base sm:text-lg max-w-lg mx-auto md:mx-0 mb-6">
            Solar systems, Starlink, custom furniture and more. Trusted by thousands across Zimbabwe.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center md:justify-start">
            <button
              onClick={onShopNow}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-bold rounded-xl shadow-md transition text-sm"
            >
              Shop Now
              <FiChevronRight className="w-4 h-4" />
            </button>
            {waLink ? (
              <a
                href={waLink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-300 font-semibold rounded-xl transition text-sm"
              >
                <FiMessageCircle className="w-4 h-4" />
                Free Quote on WhatsApp
              </a>
            ) : (
              <span className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-sky-50 text-sky-400 border border-sky-200 font-semibold rounded-xl text-sm cursor-default">
                <FiMessageCircle className="w-4 h-4" />
                WhatsApp Support
              </span>
            )}
          </div>
        </div>

        {/* Icon collage */}
        <div className="hidden md:grid grid-cols-2 gap-4 flex-shrink-0">
          {[
            { icon: <FiSun className="w-8 h-8 text-orange-500" />, label: 'Solar Systems', bg: 'bg-orange-50 border-orange-200' },
            { icon: <FiWifi className="w-8 h-8 text-sky-500" />, label: 'Starlink', bg: 'bg-sky-50 border-sky-200' },
            { icon: <FiPackage className="w-8 h-8 text-purple-500" />, label: 'Furniture', bg: 'bg-purple-50 border-purple-200' },
            { icon: <FiShield className="w-8 h-8 text-green-500" />, label: 'Warranty', bg: 'bg-green-50 border-green-200' },
          ].map(({ icon, label, bg }) => (
            <div key={label} className={`flex flex-col items-center gap-2 p-5 rounded-2xl border ${bg} w-28`}>
              {icon}
              <span className="text-xs font-semibold text-gray-700 text-center">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Trust strip */}
      <div className="relative bg-purple-50 border-t border-purple-100 px-6 py-3">
        <div className="max-w-7xl mx-auto flex flex-wrap justify-center md:justify-start gap-4 text-xs font-semibold text-purple-700">
          {['✓ PayNow Accepted', '✓ Free Quote', '✓ WhatsApp Support', '✓ Warranty Included', '✓ Nationwide Delivery'].map((b) => (
            <span key={b} className="bg-white px-3 py-1 rounded-full border border-purple-200">{b}</span>
          ))}
        </div>
      </div>
    </section>
  );
}
