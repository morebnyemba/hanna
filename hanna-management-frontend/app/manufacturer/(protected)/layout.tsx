'use client';

import Sidebar from '@/app/components/manufacturer/Sidebar'; // We will create this component



export default function ManufacturerLayout({ children }: { children: React.ReactNode }) {

  return (

    <div className="flex h-screen bg-gray-100">

      <Sidebar />

      <div className="flex flex-col flex-1 w-full overflow-y-auto">

        <main className="flex-1 p-4 sm:p-6">

          {children}

        </main>

      </div>

    </div>

  );

}
