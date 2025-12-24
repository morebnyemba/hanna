import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Hanna Management System",
    template: "%s | Hanna"
  },
  description: "Comprehensive management system for solar installations, warranties, products, and customer service in Zimbabwe",
  keywords: ["solar", "warranty management", "installation tracking", "Zimbabwe", "CRM", "inventory management"],
  authors: [{ name: "Hanna Digital" }],
  creator: "Hanna Digital",
  publisher: "Hanna Digital",
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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
