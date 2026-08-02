import { ScannedFile } from '../types';
import { StatusBadge } from './StatusBadge';
import { formatBytes } from '../utils/format';
import { Eye, HardDrive } from 'lucide-react';

interface Props {
  files: ScannedFile[];
  selectedIds: Set<number>;
  onSelect: (id: number, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
  onViewDetail: (file: ScannedFile) => void;
  sortBy?: string;
  sortDir?: 'asc' | 'desc';
  onSort?: (col: string) => void;
}

export function FileTable({ 
  files, selectedIds, onSelect, onSelectAll, onViewDetail, sortBy, sortDir, onSort 
}: Props) {
  
  if (files.length === 0) {
    return (
      <div className="card text-center py-12 text-muted">
        <HardDrive size={48} className="mx-auto mb-4 opacity-50" />
        <p>Aucun fichier trouvé</p>
      </div>
    );
  }

  const allSelected = files.length > 0 && files.every(f => selectedIds.has(f.id));
  const someSelected = files.some(f => selectedIds.has(f.id));

  const SortIcon = ({ col }: { col: string }) => {
    if (sortBy !== col) return null;
    return <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  };

  const handleHeaderClick = (col: string) => {
    if (onSort) onSort(col);
  };

  return (
    <div className="card table-container p-0 overflow-hidden">
      <table className="table">
        <thead className="bg-[var(--bg-hover)]">
          <tr>
            <th className="w-10 text-center">
              <input 
                type="checkbox" 
                checked={allSelected}
                ref={input => {
                  if (input) input.indeterminate = someSelected && !allSelected;
                }}
                onChange={(e) => onSelectAll(e.target.checked)}
                className="cursor-pointer"
              />
            </th>
            <th className="cursor-pointer hover:text-white" onClick={() => handleHeaderClick('file_name')}>
              Nom <SortIcon col="file_name" />
            </th>
            <th className="cursor-pointer hover:text-white" onClick={() => handleHeaderClick('file_size')}>
              Taille <SortIcon col="file_size" />
            </th>
            <th className="cursor-pointer hover:text-white" onClick={() => handleHeaderClick('status')}>
              Statut <SortIcon col="status" />
            </th>
            <th>Gain Réel</th>
            <th className="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {files.map(file => {
            const canDelete = file.status === 'ORPHAN_SAFE';
            
            return (
              <tr key={file.id} className={selectedIds.has(file.id) ? 'bg-[rgba(99,102,241,0.1)]' : ''}>
                <td className="text-center">
                  <input 
                    type="checkbox"
                    checked={selectedIds.has(file.id)}
                    onChange={(e) => onSelect(file.id, e.target.checked)}
                    disabled={!canDelete}
                    className={!canDelete ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}
                  />
                </td>
                <td className="max-w-xs truncate" title={file.file_name}>
                  {file.file_name}
                  {file.hardlink_count > 1 && (
                    <span className="ml-2 text-xs text-muted" title={`${file.hardlink_count} liens physiques`}>
                      ({file.hardlink_count} links)
                    </span>
                  )}
                </td>
                <td className="whitespace-nowrap">{formatBytes(file.file_size)}</td>
                <td><StatusBadge status={file.status} size="sm" /></td>
                <td className={`whitespace-nowrap ${file.real_space_gain > 0 ? 'text-success' : 'text-muted'}`}>
                  {formatBytes(file.real_space_gain)}
                </td>
                <td className="text-right">
                  <button 
                    onClick={() => onViewDetail(file)}
                    className="p-1 text-muted hover:text-primary transition-colors"
                    title="Voir les détails"
                  >
                    <Eye size={18} />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
