import React from 'react';
import { ScannedFile } from '../types';
import { formatBytes, formatDuration, formatDate } from '../utils/format';
import { StatusBadge } from './StatusBadge';
import { X, HardDrive, Link as LinkIcon, Film, Activity } from 'lucide-react';

interface Props {
  file: ScannedFile;
  onClose: () => void;
}

export function FileDetailModal({ file, onClose }: Props) {
  const linkedPaths = file.linked_paths ? JSON.parse(file.linked_paths) : [];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="text-xl font-bold truncate pr-4" title={file.file_name}>{file.file_name}</h2>
          <button onClick={onClose} className="text-muted hover:text-white transition-colors">
            <X size={24} />
          </button>
        </div>
        
        <div className="modal-body space-y-6">
          {/* Status Section */}
          <section className="bg-[var(--bg-base)] p-4 rounded-lg border border-[var(--border)]">
            <div className="flex justify-between items-start mb-2">
              <span className="text-sm text-muted">Statut</span>
              <StatusBadge status={file.status} />
            </div>
            <p className="text-sm">{file.status_reason}</p>
          </section>

          {/* Details Grid */}
          <section className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <span className="text-xs text-muted flex items-center gap-1"><HardDrive size={14}/> Taille du fichier</span>
              <div className="font-medium">{formatBytes(file.file_size)}</div>
            </div>
            <div className="space-y-1">
              <span className="text-xs text-muted flex items-center gap-1"><Activity size={14}/> Gain d'espace réel</span>
              <div className={`font-medium ${file.real_space_gain > 0 ? 'text-success' : 'text-muted'}`}>
                {formatBytes(file.real_space_gain)}
              </div>
            </div>
            <div className="space-y-1 col-span-2">
              <span className="text-xs text-muted">Chemin complet</span>
              <div className="text-sm font-mono bg-[var(--bg-base)] p-2 rounded break-all">
                {file.file_path}
              </div>
            </div>
          </section>

          {/* Hardlinks */}
          {file.hardlink_count > 1 && (
            <section className="space-y-2">
              <h3 className="text-sm font-semibold flex items-center gap-2 text-warning">
                <LinkIcon size={16} /> Liens physiques ({file.hardlink_count})
              </h3>
              {linkedPaths.length > 0 ? (
                <ul className="text-xs bg-[var(--bg-base)] p-3 rounded-lg border border-[var(--border)] space-y-1 max-h-32 overflow-y-auto">
                  {linkedPaths.map((p: string, i: number) => (
                    <li key={i} className="break-all text-muted">{p}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-muted">Chemins liés non disponibles</p>
              )}
            </section>
          )}

          {/* Media/Torrent Info */}
          {(file.media_title || file.torrent_name) && (
            <section className="border-t border-[var(--border)] pt-4 space-y-4">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Film size={16} /> Métadonnées
              </h3>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                {file.media_title && (
                  <div>
                    <span className="text-xs text-muted block">Média (Sonarr/Radarr)</span>
                    {file.media_title} {file.quality_info && <span className="text-xs bg-[var(--bg-base)] px-1 rounded ml-1">{file.quality_info}</span>}
                  </div>
                )}
                {file.torrent_name && (
                  <div>
                    <span className="text-xs text-muted block">Torrent (qBittorrent)</span>
                    <span className="truncate block" title={file.torrent_name}>{file.torrent_name}</span>
                  </div>
                )}
                {file.seeding_time_seconds !== null && (
                  <div>
                    <span className="text-xs text-muted block">Temps de seed</span>
                    {formatDuration(file.seeding_time_seconds)}
                  </div>
                )}
                {file.completion_date && (
                  <div>
                    <span className="text-xs text-muted block">Date de fin</span>
                    {formatDate(file.completion_date)}
                  </div>
                )}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
