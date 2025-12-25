"use client";

import { redirect } from 'next/navigation';

export default function SerializedItemEditAlias({ params }: { params: { id: string } }) {
  // Redirect alias from /admin/serialized-items/[id]/edit to the main edit page
  redirect(`/admin/serialized-items/${params.id}`);
  return null;
}
