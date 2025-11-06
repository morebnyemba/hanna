'use client';

import React from 'react';

const StatCard = ({ icon, title, value, color }: { icon: React.ReactNode, title: string, value: number, color: string }) => (
  <div className={`bg-white p-4 sm:p-6 rounded-lg shadow-md border-l-4 ${color}`}>
    <div className="flex items-center">
      <div className="mr-3 sm:mr-4">{icon}</div>
      <div>
        <p className="text-xs sm:text-sm font-medium text-gray-500 uppercase">{title}</p>
        <p className="text-xl sm:text-2xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  </div>
);

export default StatCard;
