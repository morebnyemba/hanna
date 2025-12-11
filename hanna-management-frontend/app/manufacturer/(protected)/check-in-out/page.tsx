'use client';

import CheckInOutManager from '@/app/components/CheckInOutManager';

export default function ManufacturerCheckInOutPage() {
  return (
    <CheckInOutManager 
      defaultLocation="manufacturer"
      showOrderFulfillment={false}
      title="Manufacturer - Check-In / Check-Out"
    />
  );
}
