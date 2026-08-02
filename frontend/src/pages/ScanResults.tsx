import { useState, useEffect } from 'react';
import { api } from '../api';
import { FileListResponse, ScannedFile, DeletionPreview } from '../types';
import { FileTable } from '../components/FileTable';
import { FileDetailModal } from '../components/FileDetailModal';
import { DeleteConfirmModal } from '../components/DeleteConfirmModal';
import { formatBytes } from '../utils/format';
import { Search, Filter, Trash2, CheckSquare, XSquare, Loader2 } from 'lucide-react';

export function ScanResults() {
  const [data, setData] = useState<FileListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Filters & Pagination
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('file_size');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  
  // Selection
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [selectingAll, setSelectingAll] = useState(false);
  
  // Modals
  const [detailFile, setDetailFile] = useState<ScannedFile | null>(null);
  const [deletionPreview, setDeletionPreview] = useState<DeletionPreview | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const res = await api.getFiles({
        page,
        page_size: 50,
        status: statusFilter,
        search,
        sort_by: sortBy,
        sort_dir: sortDir
      });
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [page, statusFilter, search, sortBy, sortDir]);

  // Handle selection
  const handleSelect = (id: number, selected: boolean) => {
    const next = new Set(selectedIds);
    if (selected) next.add(id);
    else next.delete(id);
    setSelectedIds(next);
  };

  const handleSelectAll = (selected: boolean) => {
    if (!data) return;
    if (selected) {
      const deletableIds = data.items
        .filter(f => f.status === 'ORPHAN_SAFE')
        .map(f => f.id);
      setSelectedIds(new Set([...selectedIds, ...deletableIds]));
    } else {
      const next = new Set(selectedIds);
      data.items.forEach(f => next.delete(f.id));
      setSelectedIds(next);
    }
  };

  // Select ALL orphans across ALL pages
  const handleSelectAllOrphans = async () => {
    setSelectingAll(true);
    try {
      const result = await api.getAllDeletableIds(search || undefined);
      setSelectedIds(new Set(result.ids));
    } catch (e: any) {
      alert(`Erreur: ${e.message}`);
    } finally {
      setSelectingAll(false);
    }
  };

  const handleDeselectAll = () => {
    setSelectedIds(new Set());
  };

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortDir('desc');
    }
  };

  const handlePrepareDelete = async () => {
    if (selectedIds.size === 0) return;
    try {
      const preview = await api.previewDeletion(Array.from(selectedIds));
      setDeletionPreview(preview);
    } catch (e: any) {
      alert(`Erreur: ${e.message}`);
    }
  };

  const handleExecuteDelete = async () => {
    if (selectedIds.size === 0) return;
    setIsDeleting(true);
    try {
      const res = await api.executeDeletion(Array.from(selectedIds));
      alert(`Supprimé avec succès : ${res.deleted_count} fichiers (${formatBytes(res.space_freed)})`);
      setDeletionPreview(null);
      setSelectedIds(new Set());
      fetchFiles(); // reload
    } catch (e: any) {
      alert(`Erreur lors de la suppression: ${e.message}`);
    } finally {
      setIsDeleting(false);
    }
  };

  // Count orphan_safe on current page for info
  const orphanSafeCount = data?.summary?.total_reclaimable ? data.summary.total_count : 0;

  return (
    <div className="space-y-6 pb-20">
      <header>
        <h1 className="text-2xl">Résultats d'analyse</h1>
        <p className="text-muted text-sm mt-1">Examinez les fichiers et libérez de l'espace</p>
      </header>

      {/* Summary Bar */}
      {data && data.summary && data.summary.total_reclaimable > 0 && (
        <div className="flex gap-4 p-4 bg-[var(--warning-bg)] border border-[var(--warning)] rounded-lg items-center">
          <div className="flex-1">
            <h3 className="text-[var(--warning)] font-bold text-lg">
              {data.summary.total_count} fichiers trouvés
            </h3>
            <p className="text-sm text-warning opacity-80">
              {formatBytes(data.summary.total_reclaimable)} d'espace peut être libéré en toute sécurité.
            </p>
          </div>
          <button 
            className="btn btn-primary"
            onClick={() => {
              setStatusFilter('ORPHAN_SAFE');
              setPage(1);
            }}
            disabled={statusFilter === 'ORPHAN_SAFE'}
          >
            Voir uniquement les orphelins
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input 
            type="text" 
            placeholder="Rechercher par nom..." 
            className="input pl-10"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="relative">
          <Filter size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <select 
            className="select pl-10"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Tous les statuts</option>
            <option value="ORPHAN_SAFE">Orphelins (Supprimables)</option>
            <option value="ORPHAN_NO_GAIN">Orphelins (Sans gain)</option>
            <option value="PROTECTED">Tous les protégés</option>
          </select>
        </div>
      </div>

      {/* Bulk Selection Actions */}
      <div className="flex gap-3 items-center flex-wrap">
        <button 
          className="btn btn-outline flex items-center gap-2"
          onClick={handleSelectAllOrphans}
          disabled={selectingAll}
        >
          {selectingAll ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <CheckSquare size={16} />
          )}
          {selectingAll ? 'Chargement...' : 'Tout sélectionner (orphelins supprimables)'}
        </button>
        {selectedIds.size > 0 && (
          <button 
            className="btn btn-outline flex items-center gap-2"
            onClick={handleDeselectAll}
          >
            <XSquare size={16} />
            Tout désélectionner ({selectedIds.size})
          </button>
        )}
        {selectedIds.size > 0 && (
          <span className="text-sm text-muted ml-auto">
            {selectedIds.size} fichier(s) sélectionné(s) sur toutes les pages
          </span>
        )}
      </div>

      {/* Table */}
      <div className="relative min-h-[400px]">
        {loading && (
          <div className="absolute inset-0 bg-[var(--bg-base)]/50 backdrop-blur-sm z-10 flex items-center justify-center">
            <div className="animate-spin text-primary"><Search size={32} /></div>
          </div>
        )}
        
        {data && (
          <FileTable 
            files={data.items}
            selectedIds={selectedIds}
            onSelect={handleSelect}
            onSelectAll={handleSelectAll}
            onViewDetail={setDetailFile}
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={handleSort}
          />
        )}
      </div>

      {/* Pagination */}
      {data && data.total > data.page_size && (
        <div className="flex justify-center gap-2 mt-4">
          <button 
            className="btn btn-outline" 
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
          >
            Précédent
          </button>
          <span className="flex items-center px-4 text-sm">
            Page {page} sur {Math.ceil(data.total / data.page_size)}
          </span>
          <button 
            className="btn btn-outline" 
            disabled={page >= Math.ceil(data.total / data.page_size)}
            onClick={() => setPage(p => p + 1)}
          >
            Suivant
          </button>
        </div>
      )}

      {/* Floating Action Bar */}
      {selectedIds.size > 0 && (
        <div className="fixed bottom-0 left-0 right-0 md:left-[var(--sidebar-width)] bg-[var(--bg-card)] border-t border-[var(--border)] p-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)] z-20 flex justify-between items-center animate-slide-up">
          <div>
            <span className="font-bold text-lg">{selectedIds.size}</span> fichiers sélectionnés
          </div>
          <button className="btn btn-danger" onClick={handlePrepareDelete}>
            <Trash2 size={18} />
            Supprimer la sélection
          </button>
        </div>
      )}

      {/* Modals */}
      {detailFile && (
        <FileDetailModal file={detailFile} onClose={() => setDetailFile(null)} />
      )}
      
      {deletionPreview && (
        <DeleteConfirmModal 
          preview={deletionPreview}
          onConfirm={handleExecuteDelete}
          onCancel={() => setDeletionPreview(null)}
          isDeleting={isDeleting}
        />
      )}
    </div>
  );
}
