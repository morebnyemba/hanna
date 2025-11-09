'use client';

import { useState, useEffect } from 'react';
import { FiUsers, FiPlus } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  groups: string[];
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInviteDialogOpen, setInviteDialogOpen] = useState(false);

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get('/crm-api/users/');
        setUsers(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch users.');
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  const handleInviteUser = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const data = Object.fromEntries(formData.entries());

    try {
      await apiClient.post('/crm-api/users/invite/', data);
      setInviteDialogOpen(false);
      // Refresh users list
      const response = await apiClient.get('/crm-api/users/');
      setUsers(response.data);
    } catch (err: any) {
      alert('Failed to invite user: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <FiUsers className="mr-3" />
          User Management
        </h1>
        <Dialog open={isInviteDialogOpen} onOpenChange={setInviteDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <FiPlus className="mr-2" />
              Invite User
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Invite New User</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleInviteUser} className="space-y-4">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input id="email" name="email" type="email" required />
              </div>
              <div>
                <Label htmlFor="first_name">First Name</Label>
                <Input id="first_name" name="first_name" required />
              </div>
              <div>
                <Label htmlFor="last_name">Last Name</Label>
                <Input id="last_name" name="last_name" required />
              </div>
              <div>
                <Label htmlFor="role">Role</Label>
                <select id="role" name="role" className="w-full p-2 border rounded">
                  <option>Admin</option>
                  <option>Manufacturer</option>
                  <option>Technician</option>
                </select>
              </div>
              <Button type="submit">Send Invitation</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {loading && <p>Loading users...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}

      {!loading && !error && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.first_name} {user.last_name}</TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>{Array.isArray(user.groups) ? user.groups.join(', ') : ''}</TableCell>
                <TableCell>
                  <Button variant="outline" size="sm">Edit</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </>
  );
}
