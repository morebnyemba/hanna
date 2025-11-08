'use client';

import { useState, useEffect } from 'react';
import { FiTool } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const ServiceRequestsPage = () => {
  const [installationRequests, setInstallationRequests] = useState([]);
  const [assessmentRequests, setAssessmentRequests] = useState([]);
  const [loanApplications, setLoanApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [installRes, assessRes, loanRes] = await Promise.all([
          apiClient.get('/crm-api/customer-data/installation-requests/'),
          apiClient.get('/crm-api/customer-data/site-assessments/'),
          apiClient.get('/crm-api/customer-data/loan-applications/'),
        ]);
        setInstallationRequests(installRes.data.results);
        setAssessmentRequests(assessRes.data.results);
        setLoanApplications(loanRes.data.results);
      } catch (error) {
        console.error("Failed to fetch service requests", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <p>Loading service requests...</p>;
  }

  return (
    <>
      <h1 className="text-3xl font-bold text-gray-900 mb-6 flex items-center">
        <FiTool className="mr-3" />
        Service Requests
      </h1>
      <Tabs defaultValue="installations">
        <TabsList>
          <TabsTrigger value="installations">Installation Requests</TabsTrigger>
          <TabsTrigger value="assessments">Site Assessments</TabsTrigger>
          <TabsTrigger value="loans">Loan Applications</TabsTrigger>
        </TabsList>
        <TabsContent value="installations">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {installationRequests.map((req: any) => (
                <TableRow key={req.id}>
                  <TableCell>{req.full_name}</TableCell>
                  <TableCell>{req.installation_type}</TableCell>
                  <TableCell>{req.status}</TableCell>
                  <TableCell>{new Date(req.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>
        <TabsContent value="assessments">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assessmentRequests.map((req: any) => (
                <TableRow key={req.id}>
                  <TableCell>{req.full_name}</TableCell>
                  <TableCell>{req.status}</TableCell>
                  <TableCell>{new Date(req.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>
        <TabsContent value="loans">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loanApplications.map((req: any) => (
                <TableRow key={req.id}>
                  <TableCell>{req.full_name}</TableCell>
                  <TableCell>{req.loan_type}</TableCell>
                  <TableCell>${req.requested_amount}</TableCell>
                  <TableCell>{req.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>
    </>
  );
};

export default ServiceRequestsPage;
