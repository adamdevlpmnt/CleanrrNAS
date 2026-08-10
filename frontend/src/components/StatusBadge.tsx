import { FileStatus } from '../types';
import { getStatusLabel, getStatusColor } from '../utils/format';
import { Shield, Trash2, AlertCircle, HelpCircle } from 'lucide-react';

interface Props {
  status: FileStatus;
  size?: 'sm' | 'md';
}

export function StatusBadge({ status, size = 'md' }: Props) {
  let colors = getStatusColor(status);
  let label = getStatusLabel(status);
  
  if (status === 'ORPHAN_PROTECTED') {
    colors = { bg: 'rgba(245, 158, 11, 0.2)', text: '#f59e0b' }; // amber
    label = 'Orphelin protégé';
  }
  
  const Icon = status.startsWith('PROTECTED') ? Shield :
               status === 'ORPHAN_PROTECTED' ? Shield :
               status === 'ORPHAN_SAFE' ? Trash2 :
               status === 'ORPHAN_NO_GAIN' ? AlertCircle : HelpCircle;
               
  return (
    <span 
      className="badge" 
      style={{ 
        backgroundColor: colors.bg, 
        color: colors.text,
        fontSize: size === 'sm' ? '0.7rem' : '0.75rem',
        padding: size === 'sm' ? '0.15rem 0.4rem' : '0.25rem 0.5rem'
      }}
      title={label}
    >
      <Icon size={size === 'sm' ? 12 : 14} />
      {label}
    </span>
  );
}
