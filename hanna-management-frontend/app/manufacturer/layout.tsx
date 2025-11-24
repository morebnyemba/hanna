"use client";
import React from 'react';
import ManufacturerLayout from '@/app/components/ManufacturerLayout';

export default function ManufacturerPortalLayout({ children }: { children: React.ReactNode }) {
  return <ManufacturerLayout>{children}</ManufacturerLayout>;
}