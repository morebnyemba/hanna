'use client';

import CheckInOutManager from '@/app/components/CheckInOutManager';

export default function AdminCheckInOutPage() {
  return (
    <CheckInOutManager 
      defaultLocation="warehouse"
      showOrderFulfillment={true}
      title="Admin - Item Check-In / Check-Out"
    />
  );
}
