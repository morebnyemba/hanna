'use client';

import CheckInOutManager from '@/app/components/CheckInOutManager';

export default function TechnicianCheckInOutPage() {
  return (
    <CheckInOutManager 
      defaultLocation="technician"
      showOrderFulfillment={false}
      title="Technician - Check-In / Check-Out"
    />
  );
}
