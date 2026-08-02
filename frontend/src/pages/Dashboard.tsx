import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { DashboardStats, ScanSession } from '../types';
import { StatsCard } from '../components/StatsCard';
import { ConnectionDot } from '../components/ConnectionDot';
import { ScanProgress } from '../components/ScanProgress';
import { formatBytes, formatRelativeTime } from '../utils/format';
import { HardDrive, Trash2, Shield, Play, AlertCircle, Clock } from 'lucide-react';

export function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [latestScan, setLatestScan] = useState<ScanSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      const [statsData, scanData] = await Promise.all([
        api.getDashboardStats(),
        api.getLatestScan().catch(() => null) // Ignore error if no scan exists
      ]);
      setStats(statsData);
      setLatestScan(scanData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Erreur lors du chargement du tableau de bord');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const handleStartScan = async () => {
    try {
      const session = await api.startScan();
      setLatestScan(session);
    } catch (err: any) {
      alert(`Erreur lors du lancement du scan: ${err.message}`);
    }
  };

  const isScanning = latestScan?.status === 'pending' || latestScan?.status === 'running';

  if (loading) {
    return <div className="flex-1 flex items-center justify-center"><div className="animate-spin text-[var(--primary)]"><Clock size={32} /></div></div>;
  }

  if (error) {
    return (
      <div className="card border-[var(--danger)] text-center p-8">
        <AlertCircle size={48} className="text-[var(--danger)] mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">Erreur de connexion</h2>
        <p className="text-muted">{error}</p>
        <button onClick={fetchDashboardData} className="btn btn-outline mt-4">Réessayer</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl">Tableau de bord</h1>
          <p className="text-muted text-sm mt-1">Vue d'ensemble de votre répertoire de téléchargements</p>
        </div>
        <div className="flex gap-4 bg-[var(--bg-card)] p-2 rounded-lg border border-[var(--border)]">
          <ConnectionDot 
            label="Sonarr" 
            connected={stats?.connection_status?.sonarr_connected ?? false} 
            version={stats?.connection_status?.sonarr_version}
          />
          <ConnectionDot 
            label="Radarr" 
            connected={stats?.connection_status?.radarr_connected ?? false} 
            version={stats?.connection_status?.radarr_version}
          />
          <ConnectionDot 
            label="qBittorrent" 
            connected={stats?.connection_status?.qbittorrent_connected ?? false} 
          />
        </div>
      </header>

      {/* Main Actions */}
      <section>
        {isScanning ? (
          <ScanProgress scanId={latestScan!.id} onComplete={fetchDashboardData} />
        ) : (
          <div className="card text-center p-8 bg-gradient-to-b from-[var(--bg-card)] to-[var(--bg-base)] border border-[var(--border)] relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 text-xs text-muted">
              Dernier scan : {formatRelativeTime(stats?.last_scan_date || null)}
            </div>
            
            <HardDrive size={48} className="mx-auto text-[var(--primary)] mb-4 opacity-80" />
            <h2 className="text-xl font-bold mb-2">Prêt pour l'analyse</h2>
            <p className="text-muted max-w-md mx-auto mb-6 text-sm">
              Lancez une analyse pour identifier les fichiers orphelins pouvant être supprimés en toute sécurité.
            </p>
            <button onClick={handleStartScan} className="btn btn-primary px-8 py-3 text-lg rounded-xl shadow-[var(--shadow-md)]">
              <Play size={20} className="fill-current" />
              Lancer le scan
            </button>
            
            {latestScan && latestScan.status === 'completed' && (
              <div className="mt-6 pt-4 border-t border-[var(--border)] flex justify-center gap-6 text-sm">
                <span className="text-muted">Résultats du dernier scan:</span>
                <span className="text-warning font-medium">{latestScan.orphan_count} orphelins</span>
                <span className="text-success font-medium">{formatBytes(latestScan.reclaimable_size)} libérables</span>
                <button onClick={() => navigate('/results')} className="text-[var(--primary)] hover:underline">
                  Voir les résultats
                </button>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard 
          title="Taille Totale" 
          value={formatBytes(stats?.total_downloads_size || 0)} 
          subtitle="Tous fichiers vidéo scannés"
          icon={<HardDrive size={24} />}
          color="var(--text-primary)"
        />
        <StatsCard 
          title="Espace Libérable" 
          value={formatBytes(stats?.reclaimable_size || 0)} 
          subtitle="Gains réels estimés"
          icon={<Trash2 size={24} />}
          color="var(--warning)"
        />
        <StatsCard 
          title="Fichiers Orphelins" 
          value={stats?.orphan_count || 0} 
          subtitle="Non liés aux bibliothèques"
          icon={<AlertCircle size={24} />}
          color="var(--warning)"
        />
        <StatsCard 
          title="Fichiers Protégés" 
          value={stats?.protected_count || 0} 
          subtitle="Ignorés par sécurité"
          icon={<Shield size={24} />}
          color="var(--success)"
        />
      </div>
    </div>
  );
}
