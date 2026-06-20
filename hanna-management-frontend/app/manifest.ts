import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Hanna Management System',
    short_name: 'Hanna',
    description:
      'Comprehensive management system for solar installations, warranties, products, and customer service in Zimbabwe',
    start_url: '/',
    scope: '/',
    display: 'standalone',
    orientation: 'portrait',
    background_color: '#ffffff',
    theme_color: '#4f46e5',
    lang: 'en-ZW',
    categories: ['business', 'shopping', 'productivity'],
    icons: [
      {
        src: '/icons/icon.svg',
        sizes: 'any',
        type: 'image/svg+xml',
        purpose: 'any',
      },
      {
        src: '/icons/icon-maskable.svg',
        sizes: 'any',
        type: 'image/svg+xml',
        purpose: 'maskable',
      },
    ],
    shortcuts: [
      {
        name: 'Shop',
        short_name: 'Shop',
        description: 'Browse and purchase solar products',
        url: '/shop',
      },
      {
        name: 'My Dashboard',
        short_name: 'Dashboard',
        description: 'Your personal dashboard',
        url: '/client/dashboard',
      },
    ],
  };
}
