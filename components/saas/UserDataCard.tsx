'use client';

import { Button } from '@/components/ui';

interface UserDataCardProps {
  userData: string;
  onEdit: () => void;
}

export function UserDataCard({ userData, onEdit }: UserDataCardProps) {
  return (
    <div className="bg-surface rounded-xl border border-default p-6 mb-6">
      <h2 className="text-xl font-semibold text-primary mb-4">Your Text Data</h2>
      <div
        className={`p-4 rounded-lg mb-4 min-h-[100px] ${
          userData ? 'bg-elevated text-primary' : 'bg-elevated text-muted italic'
        }`}
      >
        {userData || 'No data yet. Click "Edit" to add some content.'}
      </div>
      <Button onClick={onEdit}>Edit</Button>
    </div>
  );
}
