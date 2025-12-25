'use client';

import { useState, useEffect, useMemo } from 'react';
import { FiTool, FiTrash2, FiCheckCircle, FiXCircle, FiSearch, FiFilter, FiFileText, FiChevronLeft, FiChevronRight, FiEye } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
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
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import DeleteConfirmationModal from '@/app/components/shared/DeleteConfirmationModal';
import { Component, ReactNode } from 'react';

// Error Boundary
interface LocalErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class LocalErrorBoundary extends Component<{ children: ReactNode }, LocalErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): LocalErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    console.error('LocalErrorBoundary caught:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 border border-red-300 bg-red-50 rounded-lg">
          <h2 className="text-red-800 font-semibold">Something went wrong</h2>
          <p className="text-red-700 text-sm mt-1">{this.state.error?.message}</p>
        </div>
      );
    }

    return this.props.children;
  }
}

// Helper function to format dates safely
const safeFormatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A';
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return 'Invalid Date';
  }
};

// Status badge component
const StatusBadge = ({ status, type }: { status: string; type: 'installation' | 'assessment' | 'loan' }) => {
  const statusMap: Record<string, Record<string, string>> = {
    installation: {
      pending: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
    },
    assessment: {
      pending: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
      assessed: 'bg-blue-100 text-blue-800',
    },
    loan: {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
    },
  };

  const style = statusMap[type]?.[status] || 'bg-gray-100 text-gray-800';
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${style}`}>
      {status?.charAt(0).toUpperCase() + status?.slice(1) || 'Unknown'}
    </span>
  );
};

const ServiceRequestsPage = () => {
  const [installationRequests, setInstallationRequests] = useState([]);
  const [assessmentRequests, setAssessmentRequests] = useState([]);
  const [loanApplications, setLoanApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<{ id: number; type: string; name: string } | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<any>(null);
  const [selectedDetailType, setSelectedDetailType] = useState<'installation' | 'assessment' | 'loan' | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Search and filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [installationStatusFilter, setInstallationStatusFilter] = useState('all');
  const [assessmentStatusFilter, setAssessmentStatusFilter] = useState('all');
  const [loanStatusFilter, setLoanStatusFilter] = useState('all');
  
  // Pagination states
  const [installationPage, setInstallationPage] = useState(1);
  const [assessmentPage, setAssessmentPage] = useState(1);
  const [loanPage, setLoanPage] = useState(1);
  const itemsPerPage = 10;

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [installRes, assessRes, loanRes] = await Promise.all([
        apiClient.get('/crm-api/admin-panel/installation-requests/'),
        apiClient.get('/crm-api/admin-panel/site-assessment-requests/'),
        apiClient.get('/crm-api/admin-panel/loan-applications/'),
      ]);
      setInstallationRequests(installRes.data.results || installRes.data || []);
      setAssessmentRequests(assessRes.data.results || assessRes.data || []);
      setLoanApplications(loanRes.data.results || loanRes.data || []);
    } catch (err: any) {
      setError('Failed to fetch service requests. Please try again.');
      console.error("Failed to fetch service requests", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filtered installation requests
  const filteredInstallations = useMemo(() => {
    return installationRequests.filter((req: any) => {
      const matchesSearch =
        req.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.phone?.includes(searchTerm) ||
        req.national_id?.includes(searchTerm);
      const matchesStatus =
        installationStatusFilter === 'all' || req.status === installationStatusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [installationRequests, searchTerm, installationStatusFilter]);

  // Filtered assessment requests
  const filteredAssessments = useMemo(() => {
    return assessmentRequests.filter((req: any) => {
      const matchesSearch =
        req.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.phone?.includes(searchTerm) ||
        req.national_id?.includes(searchTerm);
      const matchesStatus =
        assessmentStatusFilter === 'all' || req.status === assessmentStatusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [assessmentRequests, searchTerm, assessmentStatusFilter]);

  // Filtered loan applications
  const filteredLoans = useMemo(() => {
    return loanApplications.filter((req: any) => {
      const matchesSearch =
        req.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.phone?.includes(searchTerm) ||
        req.national_id?.includes(searchTerm);
      const matchesStatus =
        loanStatusFilter === 'all' || req.status === loanStatusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [loanApplications, searchTerm, loanStatusFilter]);

  // Paginated data
  const paginatedInstallations = filteredInstallations.slice(
    (installationPage - 1) * itemsPerPage,
    installationPage * itemsPerPage
  );
  const paginatedAssessments = filteredAssessments.slice(
    (assessmentPage - 1) * itemsPerPage,
    assessmentPage * itemsPerPage
  );
  const paginatedLoans = filteredLoans.slice(
    (loanPage - 1) * itemsPerPage,
    loanPage * itemsPerPage
  );

  const installationPages = Math.ceil(filteredInstallations.length / itemsPerPage);
  const assessmentPages = Math.ceil(filteredAssessments.length / itemsPerPage);
  const loanPages = Math.ceil(filteredLoans.length / itemsPerPage);

  const handleDeleteClick = (id: number, type: string, name: string) => {
    setItemToDelete({ id, type, name });
    setDeleteModalOpen(true);
  };

  const handleShowDetail = (item: any, type: 'installation' | 'assessment' | 'loan') => {
    setSelectedDetail(item);
    setSelectedDetailType(type);
    setDetailModalOpen(true);
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
      setError('Failed to delete: ' + (err.response?.data?.message || err.message));
    } finally {
      setIsDeleting(false);
    }
  };

  const handleMarkCompleted = async (id: number) => {
    try {
      await apiClient.post(`/crm-api/admin-panel/installation-requests/${id}/mark_completed/`);
      setDetailModalOpen(false);
      setSelectedDetail(null);
      fetchData();
    } catch (err: any) {
      setError('Failed to mark as completed: ' + (err.response?.data?.message || err.message));
    }
  };

  const handleMarkAssessed = async (id: number) => {
    try {
      await apiClient.post(`/crm-api/admin-panel/site-assessment-requests/${id}/mark_completed/`);
      setDetailModalOpen(false);
      setSelectedDetail(null);
      fetchData();
    } catch (err: any) {
      setError('Failed to mark as assessed: ' + (err.response?.data?.message || err.message));
    }
  };

  const handleApproveLoan = async (id: number) => {
    try {
      await apiClient.post(`/crm-api/admin-panel/loan-applications/${id}/approve/`);
      setDetailModalOpen(false);
      setSelectedDetail(null);
      fetchData();
    } catch (err: any) {
      setError('Failed to approve loan: ' + (err.response?.data?.message || err.message));
    }
  };

  const handleRejectLoan = async (id: number) => {
    try {
      await apiClient.post(`/crm-api/admin-panel/loan-applications/${id}/reject/`);
      setDetailModalOpen(false);
      setSelectedDetail(null);
      fetchData();
    } catch (err: any) {
      setError('Failed to reject loan: ' + (err.response?.data?.message || err.message));
    }
  };

  // PDF Export function
  const exportToPDF = (data: any[], title: string, columns: any[]) => {
    const doc = new jsPDF();
    doc.setFontSize(16);
    doc.text(title, 14, 22);
    
    const tableData = data.map(item =>
      columns.map(col => {
        const value = col.accessor(item);
        if (col.id === 'status') {
          return value?.charAt(0).toUpperCase() + value?.slice(1) || 'N/A';
        }
        return value || 'N/A';
      })
    );

    autoTable(doc, {
      head: [columns.map(col => col.label)],
      body: tableData,
      startY: 30,
      theme: 'striped',
      columnStyles: {
        0: { cellWidth: 30 },
        1: { cellWidth: 25 },
        2: { cellWidth: 25 },
        3: { cellWidth: 40 },
      },
    });

    doc.save(`${title.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`);
  };

  const handleExportInstallations = () => {
    exportToPDF(filteredInstallations, 'Installation Requests', [
      { id: 'name', label: 'Customer', accessor: (row: any) => row.full_name },
      { id: 'type', label: 'Type', accessor: (row: any) => row.installation_type_display || row.installation_type },
      { id: 'status', label: 'Status', accessor: (row: any) => row.status },
      { id: 'date', label: 'Date', accessor: (row: any) => safeFormatDate(row.created_at) },
    ]);
  };

  const handleExportAssessments = () => {
    exportToPDF(filteredAssessments, 'Site Assessment Requests', [
      { id: 'name', label: 'Customer', accessor: (row: any) => row.full_name },
      { id: 'type', label: 'Type', accessor: (row: any) => row.assessment_type_display || row.assessment_type },
      { id: 'status', label: 'Status', accessor: (row: any) => row.status },
      { id: 'date', label: 'Date', accessor: (row: any) => safeFormatDate(row.created_at) },
    ]);
  };

  const handleExportLoans = () => {
    exportToPDF(filteredLoans, 'Loan Applications', [
      { id: 'name', label: 'Customer', accessor: (row: any) => row.full_name },
      { id: 'type', label: 'Type', accessor: (row: any) => row.loan_type_display || row.loan_type },
      { id: 'amount', label: 'Amount', accessor: (row: any) => `$${row.requested_amount}` },
      { id: 'status', label: 'Status', accessor: (row: any) => row.status },
    ]);
  };

  if (loading) {
    return (
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-600">Loading service requests...</p>
        </div>
      </main>
    );
  }

  return (
    <LocalErrorBoundary>
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
            <FiTool className="mr-3" />
            Service Requests
          </h1>
          {error && (
            <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error}
            </div>
          )}
        </div>

        {/* Search and Filter Controls */}
        <div className="mb-6 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex flex-col gap-4 md:flex-row md:items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <FiSearch className="inline mr-2" />
                Search (Name, Phone, ID)
              </label>
              <input
                type="text"
                placeholder="Search service requests..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setInstallationPage(1);
                  setAssessmentPage(1);
                  setLoanPage(1);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Tabs Section */}
        <Tabs defaultValue="installations" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="installations">
              Installation Requests ({filteredInstallations.length})
            </TabsTrigger>
            <TabsTrigger value="assessments">
              Site Assessments ({filteredAssessments.length})
            </TabsTrigger>
            <TabsTrigger value="loans">
              Loan Applications ({filteredLoans.length})
            </TabsTrigger>
          </TabsList>

          {/* Installation Requests Tab */}
          <TabsContent value="installations" className="space-y-4">
            <div className="flex gap-2 mb-4">
              <select
                value={installationStatusFilter}
                onChange={(e) => {
                  setInstallationStatusFilter(e.target.value);
                  setInstallationPage(1);
                }}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <Button
                onClick={handleExportInstallations}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <FiFileText className="w-4 h-4" />
                Export PDF
              </Button>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
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
                  {paginatedInstallations.length > 0 ? (
                    paginatedInstallations.map((req: any) => (
                      <TableRow key={req.id}>
                        <TableCell className="font-medium">{req.full_name || 'N/A'}</TableCell>
                        <TableCell>{req.installation_type_display || req.installation_type || 'N/A'}</TableCell>
                        <TableCell>
                          <StatusBadge status={req.status} type="installation" />
                        </TableCell>
                        <TableCell>{safeFormatDate(req.created_at)}</TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleShowDetail(req, 'installation')}
                              className="text-xs"
                            >
                              <FiEye className="w-3 h-3" />
                            </Button>
                            {req.status !== 'completed' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleMarkCompleted(req.id)}
                                className="text-xs text-green-600 hover:text-green-700"
                              >
                                <FiCheckCircle className="w-3 h-3" />
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
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-gray-500 py-8">
                        No installation requests found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            {installationPages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Page {installationPage} of {installationPages}
                </p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setInstallationPage(prev => Math.max(1, prev - 1))}
                    disabled={installationPage === 1}
                  >
                    <FiChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setInstallationPage(prev => Math.min(installationPages, prev + 1))}
                    disabled={installationPage === installationPages}
                  >
                    <FiChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          {/* Assessment Requests Tab */}
          <TabsContent value="assessments" className="space-y-4">
            <div className="flex gap-2 mb-4">
              <select
                value={assessmentStatusFilter}
                onChange={(e) => {
                  setAssessmentStatusFilter(e.target.value);
                  setAssessmentPage(1);
                }}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <Button
                onClick={handleExportAssessments}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <FiFileText className="w-4 h-4" />
                Export PDF
              </Button>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
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
                  {paginatedAssessments.length > 0 ? (
                    paginatedAssessments.map((req: any) => (
                      <TableRow key={req.id}>
                        <TableCell className="font-medium">{req.full_name || 'N/A'}</TableCell>
                        <TableCell>{req.assessment_type_display || req.assessment_type || 'N/A'}</TableCell>
                        <TableCell>
                          <StatusBadge status={req.status} type="assessment" />
                        </TableCell>
                        <TableCell>{safeFormatDate(req.created_at)}</TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleShowDetail(req, 'assessment')}
                              className="text-xs"
                            >
                              <FiEye className="w-3 h-3" />
                            </Button>
                            {req.status !== 'completed' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleMarkAssessed(req.id)}
                                className="text-xs text-green-600 hover:text-green-700"
                              >
                                <FiCheckCircle className="w-3 h-3" />
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
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-gray-500 py-8">
                        No site assessment requests found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            {assessmentPages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Page {assessmentPage} of {assessmentPages}
                </p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setAssessmentPage(prev => Math.max(1, prev - 1))}
                    disabled={assessmentPage === 1}
                  >
                    <FiChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setAssessmentPage(prev => Math.min(assessmentPages, prev + 1))}
                    disabled={assessmentPage === assessmentPages}
                  >
                    <FiChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          {/* Loan Applications Tab */}
          <TabsContent value="loans" className="space-y-4">
            <div className="flex gap-2 mb-4">
              <select
                value={loanStatusFilter}
                onChange={(e) => {
                  setLoanStatusFilter(e.target.value);
                  setLoanPage(1);
                }}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
              <Button
                onClick={handleExportLoans}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <FiFileText className="w-4 h-4" />
                Export PDF
              </Button>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
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
                  {paginatedLoans.length > 0 ? (
                    paginatedLoans.map((req: any) => (
                      <TableRow key={req.id}>
                        <TableCell className="font-medium">{req.full_name || 'N/A'}</TableCell>
                        <TableCell>{req.loan_type_display || req.loan_type || 'N/A'}</TableCell>
                        <TableCell className="font-semibold">${req.requested_amount || 0}</TableCell>
                        <TableCell>
                          <StatusBadge status={req.status} type="loan" />
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleShowDetail(req, 'loan')}
                              className="text-xs"
                            >
                              <FiEye className="w-3 h-3" />
                            </Button>
                            {req.status === 'pending' && (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleApproveLoan(req.id)}
                                  className="text-xs text-green-600 hover:text-green-700"
                                >
                                  <FiCheckCircle className="w-3 h-3" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleRejectLoan(req.id)}
                                  className="text-xs text-red-600 hover:text-red-700"
                                >
                                  <FiXCircle className="w-3 h-3" />
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
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-gray-500 py-8">
                        No loan applications found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            {loanPages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Page {loanPage} of {loanPages}
                </p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setLoanPage(prev => Math.max(1, prev - 1))}
                    disabled={loanPage === 1}
                  >
                    <FiChevronLeft className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setLoanPage(prev => Math.min(loanPages, prev + 1))}
                    disabled={loanPage === loanPages}
                  >
                    <FiChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Detail Modal */}
        <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>
                {selectedDetailType === 'installation' && 'Installation Request Details'}
                {selectedDetailType === 'assessment' && 'Site Assessment Details'}
                {selectedDetailType === 'loan' && 'Loan Application Details'}
              </DialogTitle>
            </DialogHeader>
            {selectedDetail && (
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-gray-700">Customer Name</p>
                  <p className="text-gray-900">{selectedDetail.full_name || 'N/A'}</p>
                </div>
                {selectedDetail.phone && (
                  <div>
                    <p className="text-sm font-medium text-gray-700">Phone</p>
                    <p className="text-gray-900">{selectedDetail.phone}</p>
                  </div>
                )}
                {selectedDetail.national_id && (
                  <div>
                    <p className="text-sm font-medium text-gray-700">National ID</p>
                    <p className="text-gray-900">{selectedDetail.national_id}</p>
                  </div>
                )}
                {selectedDetailType === 'installation' && (
                  <div>
                    <p className="text-sm font-medium text-gray-700">Installation Type</p>
                    <p className="text-gray-900">{selectedDetail.installation_type_display || selectedDetail.installation_type}</p>
                  </div>
                )}
                {selectedDetailType === 'assessment' && (
                  <div>
                    <p className="text-sm font-medium text-gray-700">Assessment Type</p>
                    <p className="text-gray-900">{selectedDetail.assessment_type_display || selectedDetail.assessment_type}</p>
                  </div>
                )}
                {selectedDetailType === 'loan' && (
                  <>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Loan Type</p>
                      <p className="text-gray-900">{selectedDetail.loan_type_display || selectedDetail.loan_type}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">Requested Amount</p>
                      <p className="text-gray-900 font-semibold">${selectedDetail.requested_amount || 0}</p>
                    </div>
                  </>
                )}
                <div>
                  <p className="text-sm font-medium text-gray-700">Status</p>
                  <StatusBadge
                    status={selectedDetail.status}
                    type={selectedDetailType || 'installation'}
                  />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">Date</p>
                  <p className="text-gray-900">{safeFormatDate(selectedDetail.created_at)}</p>
                </div>
                {selectedDetail.notes && (
                  <div>
                    <p className="text-sm font-medium text-gray-700">Notes</p>
                    <p className="text-gray-900 whitespace-pre-wrap">{selectedDetail.notes}</p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2 pt-4">
                  {selectedDetailType === 'installation' && selectedDetail.status !== 'completed' && (
                    <Button
                      onClick={() => handleMarkCompleted(selectedDetail.id)}
                      className="flex-1 text-xs"
                    >
                      <FiCheckCircle className="w-3 h-3 mr-1" />
                      Mark Completed
                    </Button>
                  )}
                  {selectedDetailType === 'assessment' && selectedDetail.status !== 'completed' && (
                    <Button
                      onClick={() => handleMarkAssessed(selectedDetail.id)}
                      className="flex-1 text-xs"
                    >
                      <FiCheckCircle className="w-3 h-3 mr-1" />
                      Mark Assessed
                    </Button>
                  )}
                  {selectedDetailType === 'loan' && selectedDetail.status === 'pending' && (
                    <>
                      <Button
                        onClick={() => handleApproveLoan(selectedDetail.id)}
                        className="flex-1 text-xs bg-green-600 hover:bg-green-700"
                      >
                        Approve
                      </Button>
                      <Button
                        onClick={() => handleRejectLoan(selectedDetail.id)}
                        className="flex-1 text-xs bg-red-600 hover:bg-red-700"
                      >
                        Reject
                      </Button>
                    </>
                  )}
                  <Button
                    onClick={() => setDetailModalOpen(false)}
                    variant="outline"
                    className="flex-1 text-xs"
                  >
                    Close
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

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
    </LocalErrorBoundary>
  );
};

export default ServiceRequestsPage;
