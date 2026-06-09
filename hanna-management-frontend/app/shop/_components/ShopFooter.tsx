'use client';

import Link from 'next/link';
import { FiMessageCircle } from 'react-icons/fi';

interface ShopFooterProps {
  whatsappNumber: string;
}

export default function ShopFooter({ whatsappNumber }: ShopFooterProps) {
  const waLink = whatsappNumber ? `https://wa.me/${whatsappNumber}` : null;

  return (
    <footer className="bg-purple-50 border-t border-purple-100 mt-16">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Brand */}
          <div className="text-center md:text-left">
            <div className="flex items-center gap-2 justify-center md:justify-start mb-1">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center">
                <span className="text-white text-xs font-bold">H</span>
              </div>
              <span className="font-extrabold text-purple-900 text-sm">Hanna Shop</span>
            </div>
            <p className="text-xs text-gray-500">A Pfungwa Technologies Platform</p>
          </div>

          {/* Contact */}
          <div className="flex items-center gap-4 text-sm">
            {waLink && (
              <a href={waLink} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-sky-600 hover:text-sky-700 font-semibold transition">
                <FiMessageCircle className="w-4 h-4" />
                WhatsApp Support
              </a>
            )}
            <Link href="/portals" className="text-purple-500 hover:text-purple-700 font-medium transition text-xs">
              Business Portals →
            </Link>
          </div>

          {/* Copyright */}
          <p className="text-xs text-gray-400">
            &copy; {new Date().getFullYear()} Pfungwa Technologies. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
