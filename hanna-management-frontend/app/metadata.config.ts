// Metadata configuration for all routes
export const siteConfig = {
  name: 'Hanna Management System',
  description: 'Comprehensive management system for solar installations, warranties, products, and customer service',
  url: 'https://hanna.co.zw',
  ogImage: 'https://hanna.co.zw/og-image.jpg',
  links: {
    twitter: 'https://twitter.com/hannadigital',
  },
};

export const routeMetadata = {
  // Admin Routes
  admin: {
    dashboard: {
      title: 'Dashboard',
      description: 'Admin dashboard with system overview and key metrics',
    },
    analytics: {
      title: 'Analytics',
      description: 'System-wide analytics and reporting',
    },
    users: {
      title: 'User Management',
      description: 'Manage users, roles, and permissions',
    },
    settings: {
      title: 'System Settings',
      description: 'Configure system settings and preferences',
    },
    customers: {
      title: 'Customer Management',
      description: 'View and manage customer information',
    },
    conversations: {
      title: 'Conversations',
      description: 'Manage customer conversations and communications',
    },
    'flow-builder': {
      title: 'Flow Builder',
      description: 'Create and manage automated workflows',
    },
    flows: {
      title: 'Flows',
      description: 'View and manage automation flows',
    },
    templates: {
      title: 'Templates',
      description: 'Manage message and response templates',
    },
    'job-cards': {
      title: 'Job Cards',
      description: 'Manage service and installation job cards',
    },
    notifications: {
      title: 'Notifications',
      description: 'System notifications and alerts',
    },
    payments: {
      title: 'Payments',
      description: 'View and manage payment transactions',
    },
    products: {
      title: 'Products',
      description: 'Manage product catalog and inventory',
    },
    warranties: {
      title: 'Warranties',
      description: 'Manage product warranties and claims',
    },
  },
  
  // Client Routes
  client: {
    dashboard: {
      title: 'My Dashboard',
      description: 'Your personal dashboard and account overview',
    },
    orders: {
      title: 'My Orders',
      description: 'View and track your orders',
    },
    shop: {
      title: 'Shop',
      description: 'Browse and purchase solar products',
    },
    monitoring: {
      title: 'System Monitoring',
      description: 'Monitor your solar system performance',
    },
    settings: {
      title: 'Account Settings',
      description: 'Manage your account settings and preferences',
    },
  },
  
  // Manufacturer Routes
  manufacturer: {
    dashboard: {
      title: 'Manufacturer Dashboard',
      description: 'Overview of products, warranties, and claims',
    },
    products: {
      title: 'Products',
      description: 'Manage your product catalog',
    },
    warranties: {
      title: 'Warranties',
      description: 'Manage product warranties',
    },
    'warranty-claims': {
      title: 'Warranty Claims',
      description: 'Process and manage warranty claims',
    },
    'product-tracking': {
      title: 'Product Tracking',
      description: 'Track product movements and installations',
    },
    analytics: {
      title: 'Analytics',
      description: 'Product and warranty analytics',
    },
  },
  
  // Technician Routes
  technician: {
    dashboard: {
      title: 'Technician Dashboard',
      description: 'Your installations and tasks overview',
    },
    'installation-history': {
      title: 'Installation History',
      description: 'View your installation history',
    },
    'check-in-out': {
      title: 'Check-In/Out',
      description: 'Check-in and out of installations',
    },
    analytics: {
      title: 'Performance Analytics',
      description: 'View your performance metrics',
    },
  },
  
  // Retailer Routes
  retailer: {
    dashboard: {
      title: 'Retailer Dashboard',
      description: 'Manage branches and inventory',
    },
    branches: {
      title: 'Branches',
      description: 'Manage retail branches',
    },
  },
  
  // Retailer Branch Routes
  'retailer-branch': {
    dashboard: {
      title: 'Branch Dashboard',
      description: 'Branch operations and inventory',
    },
    inventory: {
      title: 'Inventory',
      description: 'Manage branch inventory',
    },
    'order-dispatch': {
      title: 'Order Dispatch',
      description: 'Process and dispatch orders',
    },
    history: {
      title: 'History',
      description: 'View transaction history',
    },
    'check-in-out': {
      title: 'Check-In/Out',
      description: 'Staff check-in and check-out',
    },
  },
  
  // Shop
  shop: {
    title: 'Solar Products Shop',
    description: 'Browse and purchase quality solar products, inverters, batteries, and accessories',
  },
};
