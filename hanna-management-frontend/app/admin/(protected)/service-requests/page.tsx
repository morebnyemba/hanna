'use client';

import { useState, useEffect } from 'react';
import { FiTool, FiTrash2, FiCheckCircle, FiXCircle } from 'react-icons/fi';
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
import { Button } from '@/components/ui/button';
import DeleteConfirmationModal from '@/app/components/shared/DeleteConfirmationModal';

const ServiceRequestsPage = () => {
  const [installationRequests, setInstallationRequests] = useState([]);
  const [assessmentRequests, setAssessmentRequests] = useState([]);
  const [loanApplications, setLoanApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<{ id: number; type: string; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [installRes, assessRes, loanRes] = await Promise.all([
        apiClient.get('/crm-api/admin-panel/installation-requests/'),
        apiClient.get('/crm-api/admin-panel/site-assessment-requests/'),
        apiClient.get('/crm-api/admin-panel/loan-applications/'),
      ]);
      setInstallationRequests(installRes.data.results || installRes.data);
      setAssessmentRequests(assessRes.data.results || assessRes.data);
      setLoanApplications(loanRes.data.results || loanRes.data);
    } catch (error) {
      console.error("Failed to fetch service requests", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDeleteClick = (id: number, type: string, name: string) => {
    setItemToDelete({ id, type, name });
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!itemToDelete) return;
    
    setIsDeleting(true);
    try {
      let endpoint = '';
      switch (itemToDelete.type) {
        case 'installation':
          endpoint = `/crm-api/admin-panel/installation-requests/${itemToDelete.id}/`;
          break;
        case 'assessment':
          endpoint = `/crm-api/admin-panel/site-assessment-requests/${itemToDelete.id}/`;
          break;
        case 'loan':
          endpoint = `/crm-api/admin-panel/loan-applications/${itemToDelete.id}/`;
          break;
      }
      
      await apiClient.delete(endpoint);
      
      // Remove from appropriate list
      switch (itemToDelete.type) {
        case 'installation':
          setInstallationRequests(prev => prev.filter((r: any) => r.id !== itemToDelete.id));
          break;
        case 'assessment':
          setAssessmentRequests(prev => prev.filter((r: any) => r.id !== itemToDelete.id));
          break;
        case 'loan':
          setLoanApplications(prev => prev.filter((r: any) => r.id !== itemToDelete.id));
          break;
      }
      
      setDeleteModalOpen(false);
      setItemToDelete(null);
    } catch (err: any) {
      alert('Failed to delete: ' + (err.response?.data?.message || err.message));
    } finally {
      setIsDeleting(false);
    }
  };

  const handleMarkCompleted = async (id: number) => {
    try {
      await apiClient.post(`/crm-api/admin-panel/installation-requests/${id}/mark_completed/`);
      fetchData();
    } catch (err: any) {
      alert('Failed to mark as completed: ' + (err.response?.data?.message || err.message));
    }
  };

  const handleMarkAssessed = async (id: number) => {
    try {
      await apiClient.post(`/crm-api/admin-panel/site-assessment-requests/${id}/mark_completed/`);
      fetchData();
    } catch (err: any) {
      alert('Failed to mark as assessed: ' + (err.response?.data?.message || err.message));
    }
  };

  const handleApproveLoan = async (id: number) => {
    try {
      await apiClient.post(`/crm-api/admin-panel/loan-applications/${id}/approve/`);
      fetchData();
    } catch (err: any) {
      alert('Failed to approve loan: ' + (err.response?.data?.message || err.message));
    }
  };

  const handleRejectLoan = async (id: number) => {
    try {
      await apiClient.post(`/crm-api/admin-panel/loan-applications/${id}/reject/`);
      fetchData();
    } catch (err: any) {
      alert('Failed to reject loan: ' + (err.response?.data?.message || err.message));
    }
  };

  if (loading) {
    return <p>Loading service requests...</p>;
  }

  return (
    <main className="flex-1 p-8 overflow-y-auto">
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
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {installationRequests.map((req: any) => (
                <TableRow key={req.id}>
                  <TableCell>{req.full_name}</TableCell>
                  <TableCell>{req.installation_type_display || req.installation_type}</TableCell>
                  <TableCell>{req.status_display || req.status}</TableCell>
                  <TableCell>{new Date(req.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      {req.status !== 'completed' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMarkCompleted(req.id)}
                          className="text-xs"
                        >
                          <FiCheckCircle className="w-3 h-3 mr-1" />
                          Complete
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteClick(req.id, 'installation', req.full_name)}
                        className="text-xs text-red-600 hover:text-red-700"
                      >
                        <FiTrash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </TableCell>
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
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assessmentRequests.map((req: any) => (
                <TableRow key={req.id}>
                  <TableCell>{req.full_name}</TableCell>
                  <TableCell>{req.assessment_type_display || req.assessment_type}</TableCell>
                  <TableCell>{req.status_display || req.status}</TableCell>
                  <TableCell>{new Date(req.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      {req.status !== 'assessed' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMarkAssessed(req.id)}
                          className="text-xs"
                        >
                          <FiCheckCircle className="w-3 h-3 mr-1" />
                          Mark Assessed
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteClick(req.id, 'assessment', req.full_name)}
                        className="text-xs text-red-600 hover:text-red-700"
                      >
                        <FiTrash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </TableCell>
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
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loanApplications.map((req: any) => (
                <TableRow key={req.id}>
                  <TableCell>{req.full_name}</TableCell>
                  <TableCell>{req.loan_type_display || req.loan_type}</TableCell>
                  <TableCell>${req.requested_amount}</TableCell>
                  <TableCell>{req.status_display || req.status}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      {req.status === 'pending' && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleApproveLoan(req.id)}
                            className="text-xs text-green-600 hover:text-green-700"
                          >
                            <FiCheckCircle className="w-3 h-3 mr-1" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleRejectLoan(req.id)}
                            className="text-xs text-orange-600 hover:text-orange-700"
                          >
                            <FiXCircle className="w-3 h-3 mr-1" />
                            Reject
                          </Button>
                        </>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteClick(req.id, 'loan', req.full_name)}
                        className="text-xs text-red-600 hover:text-red-700"
                      >
                        <FiTrash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setItemToDelete(null);
        }}
        onConfirm={handleDeleteConfirm}
        title="Delete Service Request"
        message={`Are you sure you want to delete the request for "${itemToDelete?.name}"? This action cannot be undone.`}
        isDeleting={isDeleting}
      />
    </main>
  );
};

export default ServiceRequestsPage;
