import { FileStatus } from '../types';

export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Octets';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Octets', 'Ko', 'Mo', 'Go', 'To', 'Po', 'Eo', 'Zo', 'Yo'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Jamais';
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(dateStr));
}

export function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return 'Jamais';
  const date = new Date(dateStr);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) return 'À l\'instant';
  
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `Il y a ${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''}`;
  
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `Il y a ${diffInHours} heure${diffInHours > 1 ? 's' : ''}`;
  
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 30) return `Il y a ${diffInDays} jour${diffInDays > 1 ? 's' : ''}`;
  
  return formatDate(dateStr);
}

export function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return 'N/A';
  
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  const parts = [];
  if (days > 0) parts.push(`${days}j`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0 || parts.length === 0) parts.push(`${minutes}m`);
  
  return parts.join(' ');
}

export function getStatusLabel(status: FileStatus): string {
  const labels: Record<FileStatus, string> = {
    PROTECTED_LIBRARY: 'Protégé (Bibliothèque)',
    PROTECTED_HARDLINK: 'Protégé (Lien Physique)',
    PROTECTED_SEEDING: 'Protégé (En Partage)',
    PROTECTED_DOWNLOADING: 'Protégé (En Téléchargement)',
    ORPHAN_SAFE: 'Orphelin (Supprimable)',
    ORPHAN_PROTECTED: 'Orphelin protégé',
    ORPHAN_NO_GAIN: 'Orphelin (Sans Gain)',
    UNKNOWN: 'Inconnu'
  };
  return labels[status] || status;
}

export function getStatusColor(status: FileStatus): { bg: string, text: string } {
  if (status.startsWith('PROTECTED')) {
    return { bg: 'var(--success-bg)', text: 'var(--success)' };
  }
  if (status === 'ORPHAN_SAFE') {
    return { bg: 'var(--warning-bg)', text: 'var(--warning)' };
  }
  return { bg: 'rgba(100, 116, 139, 0.2)', text: 'var(--text-muted)' };
}
