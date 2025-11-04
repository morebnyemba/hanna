
'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/apiClient';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface WarrantyClaim {
  claim_id: string;
  product_name: string;
  product_serial_number: string;
  customer_name: string;
  status: string;
  created_at: string;
}

const WarrantyClaimsPage = () => {
  const [claims, setClaims] = useState<WarrantyClaim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchClaims = async () => {
      try {
        const response = await apiClient.get('/warranty/claims/');
        setClaims(response.data);
      } catch (err) {
        setError('Failed to fetch warranty claims.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchClaims();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Warranty Claims</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Claim ID</TableHead>
              <TableHead>Product</TableHead>
              <TableHead>Serial Number</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {claims.map((claim) => (
              <TableRow key={claim.claim_id}>
                <TableCell>{claim.claim_id}</TableCell>
                <TableCell>{claim.product_name}</TableCell>
                <TableCell>{claim.product_serial_number}</TableCell>
                <TableCell>{claim.customer_name}</TableCell>
                <TableCell>
                  <Badge>{claim.status}</Badge>
                </TableCell>
                <TableCell>{new Date(claim.created_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default WarrantyClaimsPage;
