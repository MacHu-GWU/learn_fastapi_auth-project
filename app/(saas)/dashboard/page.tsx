'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/hooks/useToast';
import { isLoggedIn } from '@/lib/auth';
import { apiRequest } from '@/lib/api';
import { getErrorMessage, API_ENDPOINTS, ROUTES } from '@/constants';
import { UserDataCard, EditDataModal } from '@/components/saas';
import type { UserData } from '@/types';

export default function DashboardPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [userData, setUserData] = useState('');

  const [editModalOpen, setEditModalOpen] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.push(`${ROUTES.SIGNIN}?error=login_required`);
      return;
    }

    loadUserData().then(() => {
      setLoading(false);
    });
  }, [router]);

  const loadUserData = async () => {
    try {
      const response = await apiRequest(API_ENDPOINTS.USER.DATA);
      if (response.ok) {
        const data: UserData = await response.json();
        setUserData(data.text_value || '');
      } else {
        const error = await response.json();
        showToast(getErrorMessage(error.detail, 'Failed to load data.'), 'error');
      }
    } catch (error) {
      console.error('Error loading user data:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-secondary">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-primary mb-2">Your Personal Data</h1>
        <p className="text-secondary">This is your private space. Only you can see and edit this content.</p>
      </div>

      {/* User Data Card */}
      <UserDataCard userData={userData} onEdit={() => setEditModalOpen(true)} />

      {/* Edit Data Modal */}
      <EditDataModal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        initialData={userData}
        onSave={setUserData}
      />
    </div>
  );
}
