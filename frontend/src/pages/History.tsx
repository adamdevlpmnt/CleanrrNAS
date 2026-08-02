import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { ScanSession, DeletionLog } from '../types';
import { formatDate, formatBytes } from '../utils/format';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

export function History() {
  const [activeTab, setActiveTab] = useState<'scans' | 'deletions'>('scans');
  
  const [scans, setScans] = useState<ScanSession[]>([]);
  const [deletions, setDeletions] = useState<DeletionLog[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        if (activeTab === 'scans') {
          const res = await api.getScans(1, 50);
          setScans(res);
        } else {
          const res = await api.getDeletionHistory(50, 0);
          setDeletions(res);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [activeTab]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl">Historique</h1>
        <p className="text-muted text-sm mt-1">Consultez l'historique des analyses et des suppressions</p>
      </header>

      <div className="flex border-b border-[var(--border)] mb-4">
        <button 
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'scans' ? 'border-[var(--primary)] text-[var(--primary)]' : 'border-transparent text-muted hover:text-white'}`}
          onClick={() => setActiveTab('scans')}
        >
          Analyses (Scans)
        </button>
        <button 
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'deletions' ? 'border-[var(--primary)] text-[var(--primary)]' : 'border-transparent text-muted hover:text-white'}`}
          onClick={() => setActiveTab('deletions')}
        >
          Suppressions
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-muted flex justify-center"><Clock className="animate-spin" /></div>
        ) : activeTab === 'scans' ? (
          <table className="table">
            <thead className="bg-[var(--bg-hover)]">
              <tr>
                <th>Date</th>
                <th>Statut</th>
                <th>Fichiers analysés</th>
                <th>Orphelins trouvés</th>
                <th>Espace libérable</th>
              </tr>
            </thead>
            <tbody>
              {scans.length === 0 ? (
                <tr><td colSpan={5} className="text-center text-muted">Aucun scan trouvé</td></tr>
              ) : scans.map(s => (
                <tr key={s.id}>
                  <td>{formatDate(s.started_at)}</td>
                  <td>
                    <span className="flex items-center gap-1 text-sm">
                      {s.status === 'completed' ? <CheckCircle size={14} className="text-success" /> : 
                       s.status === 'failed' ? <XCircle size={14} className="text-danger" /> : 
                       <Clock size={14} className="text-warning" />}
                      {s.status === 'completed' ? 'Terminé' : s.status === 'failed' ? 'Échoué' : s.status === 'running' ? 'En cours' : 'En attente'}
                    </span>
                  </td>
                  <td>{s.total_files_scanned}</td>
                  <td>{s.orphan_count}</td>
                  <td>{formatBytes(s.reclaimable_size)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="table">
            <thead className="bg-[var(--bg-hover)]">
              <tr>
                <th>Date de suppression</th>
                <th>Nom du fichier</th>
                <th>Espace libéré</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {deletions.length === 0 ? (
                <tr><td colSpan={4} className="text-center text-muted">Aucune suppression trouvée</td></tr>
              ) : deletions.map(d => (
                <tr key={d.id}>
                  <td>{formatDate(d.deleted_at)}</td>
                  <td className="max-w-xs truncate" title={d.file_path}>{d.file_name}</td>
                  <td className="text-success">{formatBytes(d.real_space_freed ?? 0)}</td>
                  <td>
                    <span className="text-xs bg-[var(--bg-base)] px-2 py-1 rounded">
                      {d.status_at_deletion}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
