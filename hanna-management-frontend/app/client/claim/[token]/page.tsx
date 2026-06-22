'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/app/store/authStore';

interface ISRDetails {
  token: string;
  isr_id: string;
  address: string;
  system_size: string;
  system_type: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
}

interface RegistrationFormData {
  token: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
}

export default function ClaimInstallationPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;

  const [step, setStep] = useState<'validate' | 'register' | 'success' | 'error'>('validate');
  const [isrDetails, setIsrDetails] = useState<ISRDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<RegistrationFormData>({
    token: token || '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
  });
  const [registering, setRegistering] = useState(false);

  // Validate token on page load
  useEffect(() => {
    validateToken();
  }, [token]);

  const validateToken = async () => {
    if (!token) {
      setError('Invalid claim link');
      setStep('error');
      setLoading(false);
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/customer-data/claim/validate/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.token?.[0] || 'Invalid or expired claim link');
      }

      const data = await response.json();
      setIsrDetails(data);
      setFormData((prev) => ({
        ...prev,
        email: data.customer_email || '',
        first_name: data.customer_name.split(' ')[0] || '',
        last_name: data.customer_name.split(' ').slice(1).join(' ') || '',
      }));
      setStep('register');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to validate claim link');
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegistering(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/customer-data/claim/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        const errorMessage = Object.entries(data)
          .map(([key, value]) => {
            if (Array.isArray(value)) {
              return `${key}: ${value.join(', ')}`;
            }
            return `${key}: ${value}`;
          })
          .join('\n');
        throw new Error(errorMessage);
      }

      const data = await response.json();

      useAuthStore.getState().login(
        { access: data.access, refresh: data.refresh },
        { username: data.user.username, email: data.user.email, role: 'client' }
      );

      setStep('success');

      // Redirect to dashboard after 3 seconds
      setTimeout(() => {
        router.push('/client/dashboard');
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to claim installation');
    } finally {
      setRegistering(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Validating your claim link...</p>
        </div>
      </div>
    );
  }

  if (step === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
          <div className="text-center mb-6">
            <div className="text-red-600 text-5xl mb-4">✕</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Claim Link Invalid</h1>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-600 mb-4">Please ask your service provider for a new claim link.</p>
            <Link
              href="/"
              className="inline-block bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'success') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <div className="text-green-600 text-5xl mb-4">✓</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Account Created!</h1>
          <p className="text-gray-600 mb-6">
            Welcome! Your account has been successfully created. You'll be redirected to your dashboard shortly.
          </p>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800 text-sm">
              If you're not redirected automatically, click the button below.
            </p>
          </div>
          <button
            onClick={() => router.push('/client/dashboard')}
            className="mt-6 w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4 py-12">
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full">
        <div className="grid md:grid-cols-2 gap-0">
          {/* Installation Details */}
          <div className="bg-indigo-600 text-white p-8 rounded-l-lg">
            <h2 className="text-2xl font-bold mb-6">Your Installation</h2>
            {isrDetails && (
              <div className="space-y-6">
                <div>
                  <p className="text-indigo-200 text-sm mb-2">LOCATION</p>
                  <p className="text-lg font-semibold">{isrDetails.address}</p>
                </div>
                <div>
                  <p className="text-indigo-200 text-sm mb-2">SYSTEM TYPE</p>
                  <p className="text-lg font-semibold capitalize">{isrDetails.system_type}</p>
                </div>
                <div>
                  <p className="text-indigo-200 text-sm mb-2">SYSTEM SIZE</p>
                  <p className="text-lg font-semibold">{isrDetails.system_size}</p>
                </div>
                <div className="pt-4 border-t border-indigo-400">
                  <p className="text-indigo-200 text-sm mb-2">ASSIGNED TO</p>
                  <p className="text-lg font-semibold">{isrDetails.customer_name}</p>
                </div>
              </div>
            )}
          </div>

          {/* Registration Form */}
          <div className="p-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Create Your Account</h1>
            <p className="text-gray-600 mb-6">
              Complete your profile to start managing your installation online.
            </p>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <p className="text-red-800 text-sm whitespace-pre-wrap">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    First Name *
                  </label>
                  <input
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    disabled={registering}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Last Name
                  </label>
                  <input
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    disabled={registering}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  disabled={registering}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password *
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  minLength={8}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="At least 8 characters"
                  disabled={registering}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Use a mix of uppercase, lowercase, numbers, and symbols
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm Password *
                </label>
                <input
                  type="password"
                  name="password_confirm"
                  value={formData.password_confirm}
                  onChange={handleInputChange}
                  required
                  minLength={8}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  disabled={registering}
                />
              </div>

              <button
                type="submit"
                disabled={registering}
                className={`w-full py-2 px-4 rounded-lg font-semibold text-white transition ${
                  registering
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-700'
                }`}
              >
                {registering ? 'Creating Account...' : 'Claim Installation & Create Account'}
              </button>

              <p className="text-xs text-center text-gray-500 mt-4">
                By creating an account, you agree to our Terms of Service and Privacy Policy
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
