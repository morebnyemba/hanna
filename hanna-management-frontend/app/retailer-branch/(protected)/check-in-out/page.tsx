'use client';

import CheckInOutManager from '@/app/components/CheckInOutManager';

export default function CheckInOutPage() {
  return (
    <CheckInOutManager 
      defaultLocation="retail"
      showOrderFulfillment={false}
      title="Retailer Branch - Check-In / Check-Out"
    />
  );
}
