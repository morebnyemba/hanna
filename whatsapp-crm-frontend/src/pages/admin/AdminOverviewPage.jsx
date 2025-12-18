// Admin Panel Overview Page
import React from 'react';
import { Link } from 'react-router-dom';
import { 
  FiUsers, FiBell, FiMail, FiCpu, FiTool, FiShield, 
  FiBarChart2, FiShoppingCart, FiPackage, FiSettings 
} from 'react-icons/fi';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

export default function AdminOverviewPage() {
  const adminSections = [
    {
      title: 'User Management',
      description: 'Manage system users and permissions',
      icon: FiUsers,
      path: '/admin/users',
      color: 'bg-blue-500',
    },
    {
      title: 'Notifications',
      description: 'View and manage notifications',
      icon: FiBell,
      path: '/admin/notifications',
      color: 'bg-purple-500',
    },
    {
      title: 'Notification Templates',
      description: 'Configure notification templates',
      icon: FiMail,
      path: '/admin/notification-templates',
      color: 'bg-pink-500',
    },
    {
      title: 'AI Providers',
      description: 'Manage AI integration settings',
      icon: FiCpu,
      path: '/admin/ai-providers',
      color: 'bg-indigo-500',
    },
    {
      title: 'Email Configuration',
      description: 'SMTP and email account settings',
      icon: FiMail,
      path: '/admin/email-config',
      color: 'bg-green-500',
    },
    {
      title: 'Retailers & Branches',
      description: 'Manage retailers and their branches',
      icon: FiPackage,
      path: '/admin/retailers',
      color: 'bg-yellow-500',
    },
    {
      title: 'Manufacturers',
      description: 'Manage manufacturer accounts',
      icon: FiTool,
      path: '/admin/manufacturers',
      color: 'bg-orange-500',
    },
    {
      title: 'Technicians',
      description: 'Manage technician accounts',
      icon: FiSettings,
      path: '/admin/technicians',
      color: 'bg-teal-500',
    },
    {
      title: 'Warranties',
      description: 'View and manage warranties',
      icon: FiShield,
      path: '/admin/warranties',
      color: 'bg-red-500',
    },
    {
      title: 'Warranty Claims',
      description: 'Process warranty claims',
      icon: FiShield,
      path: '/admin/warranty-claims',
      color: 'bg-red-600',
    },
    {
      title: 'Daily Statistics',
      description: 'View system statistics',
      icon: FiBarChart2,
      path: '/admin/daily-stats',
      color: 'bg-cyan-500',
    },
    {
      title: 'Carts & Orders',
      description: 'Manage shopping carts',
      icon: FiShoppingCart,
      path: '/admin/carts',
      color: 'bg-lime-500',
    },
  ];

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold dark:text-gray-100">Admin Panel</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Centralized management for all system components
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {adminSections.map((section) => {
          const Icon = section.icon;
          return (
            <Link key={section.path} to={section.path}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                <CardHeader>
                  <div className={`w-12 h-12 rounded-lg ${section.color} flex items-center justify-center mb-4`}>
                    <Icon className="text-white text-2xl" />
                  </div>
                  <CardTitle className="text-lg">{section.title}</CardTitle>
                  <CardDescription>{section.description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
