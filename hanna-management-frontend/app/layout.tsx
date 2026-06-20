import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "./providers";
import ServiceWorkerRegistration from "./components/ServiceWorkerRegistration";

export const metadata: Metadata = {
  title: {
    default: "Hanna Management System",
    template: "%s | Hanna"
  },
  description: "Comprehensive management system for solar installations, warranties, products, and customer service in Zimbabwe",
  applicationName: "Hanna",
  keywords: ["solar", "warranty management", "installation tracking", "Zimbabwe", "CRM", "inventory management"],
  authors: [{ name: "Hanna Digital" }],
  creator: "Hanna Digital",
  publisher: "Hanna Digital",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Hanna",
  },
  icons: {
    icon: "/icons/icon.svg",
    apple: "/icons/icon.svg",
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    type: "website",
    locale: "en_ZW",
    url: "https://hanna.co.zw",
    siteName: "Hanna Management System",
    title: "Hanna Management System",
    description: "Comprehensive management system for solar installations, warranties, products, and customer service",
  },
};

export const viewport: Viewport = {
  themeColor: "#4f46e5",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased font-sans">
        <Providers>{children}</Providers>
        <ServiceWorkerRegistration />
      </body>
    </html>
  );
}
