import { fetchApi } from './client';
import { 
  DashboardStats, 
  ScanSession, 
  ScanProgress, 
  FileListResponse, 
  ScannedFile, 
  DeletionPreview, 
  DeletionResult,
  DeletionLog,
  ConnectionStatus
} from '../types';

export const api = {
  // Stats & Health
  getDashboardStats: () => fetchApi<DashboardStats>('/stats/dashboard'),
  getConnectionStatus: () => fetchApi<ConnectionStatus>('/health/connections'),

  // Scans
  startScan: () => fetchApi<ScanSession>('/scans/', { method: 'POST' }),
  getScans: (page = 1, pageSize = 10) => fetchApi<ScanSession[]>(`/scans/?page=${page}&page_size=${pageSize}`),
  getLatestScan: () => fetchApi<ScanSession>('/scans/latest'),
  getScanProgress: (id: number) => fetchApi<ScanProgress>(`/scans/${id}/progress`),

  // Files
  getFiles: (params: Record<string, string | number>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query.append(key, String(value));
      }
    });
    return fetchApi<FileListResponse>(`/files/?${query.toString()}`);
  },
  getFileSummary: () => fetchApi<Record<string, { count: number; size: number }>>('/files/summary'),
  getFileDetail: (id: number) => fetchApi<ScannedFile>(`/files/${id}`),
  getAllDeletableIds: (search?: string) => {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return fetchApi<{ ids: number[]; count: number }>(`/files/all-deletable-ids${query}`);
  },

  // Deletions
  previewDeletion: (ids: number[]) => fetchApi<DeletionPreview>('/deletions/preview', {
    method: 'POST',
    body: JSON.stringify({ file_ids: ids })
  }),
  executeDeletion: (ids: number[]) => fetchApi<DeletionResult>('/deletions/execute', {
    method: 'POST',
    body: JSON.stringify({ file_ids: ids, confirm: true })
  }),
  getDeletionHistory: (limit = 50, offset = 0) => fetchApi<DeletionLog[]>(`/deletions/history?limit=${limit}&offset=${offset}`),
};
