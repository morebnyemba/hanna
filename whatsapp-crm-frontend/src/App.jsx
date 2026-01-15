import AnalyticsPage from './pages/AnalyticsPage';
// Filename: src/App.jsx
import React from 'react';
import { RouterProvider, createBrowserRouter, Navigate, Link } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext'; // Your AuthProvider
import ProtectedRoute from './components/ProtectedRoute'; // Your ProtectedRoute
import AdminRoute from './components/AdminRoute'; // Admin route protection

import DashboardLayout from './components/DashboardLayout';
import Dashboard from './pages/Dashboard';
import ApiSettings from './pages/ApiSettings';
import FlowsPage from './pages/FlowsPage';
import FlowEditorPage from './pages/FlowEditorPage'; // <--- IMPORT FlowEditorPage
import MediaLibraryPage from './pages/MediaLibraryPage';
import ContactsPage from './pages/ContactsPage';
import SavedData from './pages/SavedData';
import Conversation from './pages/Conversation';
import LoginPage from './pages/LoginPage';


import InstallationRequestsPage from './pages/InstallationRequestsPage';
import OrdersPage from './pages/OrdersPage';
import SiteAssessmentsPage from './pages/SiteAssessmentsPage';
import SermonsPage from './pages/SermonsPage';
import SermonFormPage from './pages/SermonFormPage';
import EventsPage from './pages/EventsPage';
import EventFormPage from './pages/EventFormPage';
import MinistriesPage from './pages/MinistriesPage';
import MinistryFormPage from './pages/MinistryFormPage';
import BarcodeScannerPage from './pages/BarcodeScannerPage';

// Admin Pages
import AdminOverviewPage from './pages/admin/AdminOverviewPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminNotificationsPage from './pages/admin/AdminNotificationsPage';
import AdminNotificationTemplatesPage from './pages/admin/AdminNotificationTemplatesPage';
import AdminAIProvidersPage from './pages/admin/AdminAIProvidersPage';
import AdminSMTPConfigsPage from './pages/admin/AdminSMTPConfigsPage';
import AdminRetailersPage from './pages/admin/AdminRetailersPage';
import AdminManufacturersPage from './pages/admin/AdminManufacturersPage';
import AdminTechniciansPage from './pages/admin/AdminTechniciansPage';
import AdminWarrantiesPage from './pages/admin/AdminWarrantiesPage';
import AdminWarrantyClaimsPage from './pages/admin/AdminWarrantyClaimsPage';
import AdminDailyStatsPage from './pages/admin/AdminDailyStatsPage';
import AdminCartsPage from './pages/admin/AdminCartsPage';

// Retailer Pages
import RetailerSolarPackagesPage from './pages/retailer/RetailerSolarPackagesPage';
import RetailerCreateOrderPage from './pages/retailer/RetailerCreateOrderPage';
import RetailerOrdersPage from './pages/retailer/RetailerOrdersPage';
import RetailerInstallationsPage from './pages/retailer/RetailerInstallationsPage';
import RetailerInstallationDetailPage from './pages/retailer/RetailerInstallationDetailPage';
import RetailerWarrantiesPage from './pages/retailer/RetailerWarrantiesPage';
import RetailerWarrantyDetailPage from './pages/retailer/RetailerWarrantyDetailPage';

const NotFoundPage = () => (
  <div className="p-10 text-center">
    <h1 className="text-3xl font-bold text-red-600 dark:text-red-400">404 - Page Not Found</h1>
    <p className="mt-4 text-gray-700 dark:text-gray-300">The page you are looking for does not exist.</p>
    <Link
      to="/dashboard"
      className="mt-6 inline-block px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
    >
      Go to Dashboard
    </Link>
  </div>
);

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'api-settings', element: <ApiSettings /> },
      
      // Flow Management
      { path: 'flows', element: <FlowsPage /> }, // Page to list all flows
      { path: 'flows/new', element: <FlowEditorPage /> }, // <--- ADDED: Route to create a new flow
      { path: 'flows/edit/:flowId', element: <FlowEditorPage /> }, // <--- ADDED: Route to edit an existing flow
      
  // Other sections
  { path: 'media-library', element: <MediaLibraryPage /> },
  { path: 'contacts', element: <ContactsPage /> },
  { path: 'analytics', element: <AnalyticsPage />},
  { path: 'barcode-scanner', element: <BarcodeScannerPage /> },
  { path: 'installation-requests', element: <InstallationRequestsPage /> },
  { path: 'orders', element: <OrdersPage /> },
  { path: 'site-assessments', element: <SiteAssessmentsPage /> },

  // Sermon Management
  { path: 'sermons', element: <SermonsPage /> },
  { path: 'sermons/new', element: <SermonFormPage /> },
  { path: 'sermons/edit/:sermonId', element: <SermonFormPage /> },

  // Event Management
  { path: 'events', element: <EventsPage /> },
  { path: 'events/new', element: <EventFormPage /> },
  { path: 'events/edit/:eventId', element: <EventFormPage /> },

  // Ministry Management
  { path: 'ministries', element: <MinistriesPage /> },
  { path: 'ministries/new', element: <MinistryFormPage /> },
  { path: 'ministries/edit/:ministryId', element: <MinistryFormPage /> },

  // Retailer Portal
  { path: 'retailer/solar-packages', element: <RetailerSolarPackagesPage /> },
  { path: 'retailer/orders/new', element: <RetailerCreateOrderPage /> },
  { path: 'retailer/orders', element: <RetailerOrdersPage /> },
  { path: 'retailer/installations', element: <RetailerInstallationsPage /> },
  { path: 'retailer/installations/:id', element: <RetailerInstallationDetailPage /> },
  { path: 'retailer/warranties', element: <RetailerWarrantiesPage /> },
  { path: 'retailer/warranties/:id', element: <RetailerWarrantyDetailPage /> },

  // Admin Panel
  { path: 'admin', element: <AdminRoute><AdminOverviewPage /></AdminRoute> },
  { path: 'admin/users', element: <AdminRoute><AdminUsersPage /></AdminRoute> },
  { path: 'admin/notifications', element: <AdminRoute><AdminNotificationsPage /></AdminRoute> },
  { path: 'admin/notification-templates', element: <AdminRoute><AdminNotificationTemplatesPage /></AdminRoute> },
  { path: 'admin/ai-providers', element: <AdminRoute><AdminAIProvidersPage /></AdminRoute> },
  { path: 'admin/smtp-configs', element: <AdminRoute><AdminSMTPConfigsPage /></AdminRoute> },
  { path: 'admin/retailers', element: <AdminRoute><AdminRetailersPage /></AdminRoute> },
  { path: 'admin/manufacturers', element: <AdminRoute><AdminManufacturersPage /></AdminRoute> },
  { path: 'admin/technicians', element: <AdminRoute><AdminTechniciansPage /></AdminRoute> },
  { path: 'admin/warranties', element: <AdminRoute><AdminWarrantiesPage /></AdminRoute> },
  { path: 'admin/warranty-claims', element: <AdminRoute><AdminWarrantyClaimsPage /></AdminRoute> },
  { path: 'admin/daily-stats', element: <AdminRoute><AdminDailyStatsPage /></AdminRoute> },
  { path: 'admin/carts', element: <AdminRoute><AdminCartsPage /></AdminRoute> },

  { path: 'saved-data', element: <SavedData /> },
  { path: 'conversation', element: <Conversation /> },
  { path: '*', element: <NotFoundPage /> } // Catch-all for paths under DashboardLayout
    ]
  },
  { path: '*', element: <Navigate to="/" replace /> } // General catch-all for any other path
]);

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}