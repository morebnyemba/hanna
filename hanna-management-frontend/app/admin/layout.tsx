"use client";
import React from 'react';
import AdminLayout from '@/app/components/AdminLayout';

export default function AdminPortalLayout({ children }: { children: React.ReactNode }) {
  return <AdminLayout>{children}</AdminLayout>;
}