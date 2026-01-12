'use client';

import { useState, useEffect } from 'react';
import { Button, Modal } from '@/components/ui';
import { useToast } from '@/hooks/useToast';
import { apiRequest } from '@/lib/api';
import { getErrorMessage, API_ENDPOINTS } from '@/constants';
import type { UserData } from '@/types';

interface EditDataModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialData: string;
  onSave: (newData: string) => void;
}

export function EditDataModal({ isOpen, onClose, initialData, onSave }: EditDataModalProps) {
  const { showToast } = useToast();
  const [editText, setEditText] = useState(initialData);
  const [saving, setSaving] = useState(false);

  // Reset editText when modal opens with new initialData
  useEffect(() => {
    if (isOpen) {
      setEditText(initialData);
    }
  }, [isOpen, initialData]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await apiRequest(API_ENDPOINTS.USER.DATA, {
        method: 'PUT',
        body: JSON.stringify({ text_value: editText }),
      });

      if (response.ok) {
        const data: UserData = await response.json();
        onSave(data.text_value || '');
        onClose();
        showToast('Data saved successfully!', 'success');
      } else {
        const error = await response.json();
        showToast(getErrorMessage(error.detail, 'Failed to save data.'), 'error');
      }
    } catch (error) {
      console.error('Error saving user data:', error);
      showToast(getErrorMessage('NETWORK_ERROR'), 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Your Data">
      <textarea
        value={editText}
        onChange={(e) => setEditText(e.target.value)}
        placeholder="Enter your text here..."
        className="w-full h-40 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
      />
      <div className="flex justify-end gap-3 mt-4">
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={handleSave} loading={saving} loadingText="Saving...">
          Save
        </Button>
      </div>
    </Modal>
  );
}
