'use client';

import { Button } from '@/components/ui';

interface UserDataCardProps {
  userData: string;
  onEdit: () => void;
}

export function UserDataCard({ userData, onEdit }: UserDataCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Text Data</h2>
      <div
        className={`p-4 rounded-lg mb-4 min-h-[100px] ${
          userData ? 'bg-gray-50 text-gray-800' : 'bg-gray-100 text-gray-500 italic'
        }`}
      >
        {userData || 'No data yet. Click "Edit" to add some content.'}
      </div>
      <Button onClick={onEdit}>Edit</Button>
    </div>
  );
}
