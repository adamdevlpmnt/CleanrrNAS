import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { ConnectionStatus } from '../types';
import { ConnectionDot } from '../components/ConnectionDot';
import { Info, RefreshCw, Server, Settings as SettingsIcon } from 'lucide-react';

export function Settings() {
  const [connections, setConnections] = useState<ConnectionStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchConnections = async () => {
    setLoading(true);
    try {
      const data = await api.getConnectionStatus();
      setConnections(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConnections();
  }, []);

  return (
    <div className="space-y-6 max-w-4xl">
      <header>
        <h1 className="text-2xl">Paramètres</h1>
        <p className="text-muted text-sm mt-1">Configuration et état des connexions</p>
      </header>

      <div className="bg-[var(--bg-card)] border border-[var(--primary)] rounded-lg p-4 flex gap-4 text-sm text-[var(--text-primary)]">
        <Info className="text-[var(--primary)] shrink-0" />
        <div>
          <p className="font-medium mb-1">Configuration en lecture seule</p>
          <p className="text-muted">
            La configuration de MediaCleaner se fait via les variables d'environnement (généralement dans votre fichier <code className="bg-[var(--bg-base)] px-1 rounded">docker-compose.yml</code> ou <code className="bg-[var(--bg-base)] px-1 rounded">.env</code>). 
            Modifiez ces fichiers et redémarrez le conteneur pour appliquer les changements.
          </p>
        </div>
      </div>

      <div className="flex justify-between items-end mt-8 mb-4">
        <h2 className="text-lg font-bold flex items-center gap-2"><Server size={20} /> État des services</h2>
        <button 
          className="btn btn-outline btn-sm" 
          onClick={fetchConnections}
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Tester les connexions
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Sonarr */}
        <div className="card">
          <div className="flex justify-between items-start mb-4">
            <h3 className="font-bold text-[var(--primary)]">Sonarr</h3>
            <ConnectionDot 
              label={connections?.sonarr_connected ? 'Connecté' : 'Déconnecté'} 
              connected={connections?.sonarr_connected ?? false} 
            />
          </div>
          <div className="space-y-2 text-sm">
            {connections?.sonarr_version && (
              <div>
                <span className="text-muted block text-xs">Version</span>
                {connections.sonarr_version}
              </div>
            )}
            {!connections?.sonarr_connected && (
              <div className="text-[var(--danger)] text-xs">Non connecté — vérifiez l'URL et la clé API dans le docker-compose.yml</div>
            )}
          </div>
        </div>

        {/* Radarr */}
        <div className="card">
          <div className="flex justify-between items-start mb-4">
            <h3 className="font-bold text-[var(--primary)]">Radarr</h3>
            <ConnectionDot 
              label={connections?.radarr_connected ? 'Connecté' : 'Déconnecté'} 
              connected={connections?.radarr_connected ?? false} 
            />
          </div>
          <div className="space-y-2 text-sm">
            {connections?.radarr_version && (
              <div>
                <span className="text-muted block text-xs">Version</span>
                {connections.radarr_version}
              </div>
            )}
            {!connections?.radarr_connected && (
              <div className="text-[var(--danger)] text-xs">Non connecté — vérifiez l'URL et la clé API dans le docker-compose.yml</div>
            )}
          </div>
        </div>

        {/* qBittorrent */}
        <div className="card">
          <div className="flex justify-between items-start mb-4">
            <h3 className="font-bold text-[var(--primary)]">qBittorrent</h3>
            <ConnectionDot 
              label={connections?.qbittorrent_connected ? 'Connecté' : 'Déconnecté'} 
              connected={connections?.qbittorrent_connected ?? false} 
            />
          </div>
          <div className="space-y-2 text-sm">
            {!connections?.qbittorrent_connected && (
              <div className="text-[var(--danger)] text-xs">Non connecté — vérifiez l'URL et les identifiants dans le docker-compose.yml</div>
            )}
          </div>
        </div>
      </div>

      {/* Configuration Info */}
      <div className="mt-8">
        <h2 className="text-lg font-bold flex items-center gap-2 mb-4"><SettingsIcon size={20} /> Configuration actuelle</h2>
        <div className="card">
          <table className="table w-full text-sm">
            <tbody>
              <tr>
                <td className="text-muted py-2 pr-4">Chemin des téléchargements</td>
                <td className="py-2"><code className="bg-[var(--bg-base)] px-2 py-1 rounded">/data</code></td>
              </tr>
              <tr>
                <td className="text-muted py-2 pr-4">Bibliothèque Sonarr</td>
                <td className="py-2"><code className="bg-[var(--bg-base)] px-2 py-1 rounded">/data/Series_4K</code></td>
              </tr>
              <tr>
                <td className="text-muted py-2 pr-4">Bibliothèque Radarr</td>
                <td className="py-2"><code className="bg-[var(--bg-base)] px-2 py-1 rounded">/data/Film</code></td>
              </tr>
              <tr>
                <td className="text-muted py-2 pr-4">Protection Hit & Run</td>
                <td className="py-2">7 jours</td>
              </tr>
              <tr>
                <td className="text-muted py-2 pr-4">Extensions vidéo</td>
                <td className="py-2"><code className="bg-[var(--bg-base)] px-2 py-1 rounded">.mkv, .mp4, .avi, .ts, .wmv, .m4v, .mov, .flv, .webm</code></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
