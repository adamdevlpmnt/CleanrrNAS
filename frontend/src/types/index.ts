export interface ScanSession {
  id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at: string | null;
  total_files_scanned: number;
  orphan_count: number;
  protected_count: number;
  total_size_scanned: number;
  reclaimable_size: number;
  error_message: string | null;
}

export interface ScanProgress {
  scan_id: number;
  status: string;
  progress_percent: number;
  files_scanned: number;
  current_file: string | null;
}

export type FileStatus = 'PROTECTED_LIBRARY' | 'PROTECTED_HARDLINK' | 'PROTECTED_SEEDING' | 'PROTECTED_DOWNLOADING' | 'ORPHAN_SAFE' | 'ORPHAN_NO_GAIN' | 'UNKNOWN';

export interface ScannedFile {
  id: number;
  scan_session_id: number;
  file_path: string;
  file_name: string;
  file_size: number;
  inode: number | null;
  device_id: number | null;
  hardlink_count: number;
  status: FileStatus;
  status_reason: string | null;
  real_space_gain: number;
  media_type: string | null;
  media_title: string | null;
  quality_info: string | null;
  torrent_hash: string | null;
  torrent_name: string | null;
  completion_date: string | null;
  seeding_time_seconds: number | null;
  linked_paths: string | null;
  created_at: string;
}

export interface FileListSummary {
  total_count: number;
  total_size: number;
  total_reclaimable: number;
}

export interface FileListResponse {
  items: ScannedFile[];
  total: number;
  page: number;
  page_size: number;
  summary: FileListSummary;
}

export interface DeletionPreview {
  files: ScannedFile[];
  total_size: number;
  real_gain: number;
  warnings: string[];
}

export interface DeletionResult {
  deleted_count: number;
  space_freed: number;
  errors: string[];
}

export interface DeletionLog {
  id: number;
  file_path: string;
  file_name: string;
  file_size: number | null;
  real_space_freed: number | null;
  status_at_deletion: string | null;
  reason: string | null;
  deleted_at: string;
  scan_session_id: number | null;
  torrent_hash: string | null;
  torrent_removed: boolean;
}

export interface ConnectionStatus {
  sonarr_connected: boolean;
  radarr_connected: boolean;
  qbittorrent_connected: boolean;
  sonarr_version: string | null;
  radarr_version: string | null;
}

export interface DashboardStats {
  total_downloads_size: number;
  reclaimable_size: number;
  protected_count: number;
  orphan_count: number;
  last_scan_date: string | null;
  connection_status: ConnectionStatus;
}
