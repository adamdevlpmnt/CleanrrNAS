import { useEffect, useState } from 'react';
import { api } from '../api';
import { ScanProgress as IScanProgress } from '../types';
import { Loader2, AlertCircle } from 'lucide-react';

interface Props {
  scanId: number;
  onComplete?: () => void;
  onFailed?: (errorMessage: string) => void;
}

export function ScanProgress({ scanId, onComplete, onFailed }: Props) {
  const [progress, setProgress] = useState<IScanProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    let timeoutId: number;
    
    const poll = async () => {
      try {
        const data = await api.getScanProgress(scanId);
        setProgress(data);
        
        if (data.status === 'completed') {
          if (onComplete) onComplete();
        } else if (data.status === 'failed') {
          const errMsg = data.current_file || 'Le scan a échoué (erreur inconnue)';
          setError(errMsg);
          if (onFailed) onFailed(errMsg);
        } else {
          timeoutId = window.setTimeout(poll, 2000);
        }
      } catch (e) {
        console.error("Erreur de suivi du scan:", e);
        timeoutId = window.setTimeout(poll, 5000);
      }
    };
    
    poll();
    
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [scanId, onComplete, onFailed]);
  
  if (!progress) return <div className="card flex items-center gap-4"><Loader2 className="animate-spin text-primary" /> <span>Initialisation du scan...</span></div>;
  
  if (error) {
    return (
      <div className="card border border-[var(--danger)]">
        <div className="flex items-center gap-3 mb-2">
          <AlertCircle size={24} className="text-[var(--danger)]" />
          <h3 className="text-lg font-medium text-[var(--danger)]">Scan échoué</h3>
        </div>
        <p className="text-sm text-muted mt-2 break-all">{error}</p>
        <p className="text-xs text-muted mt-3">Consultez les logs Docker pour plus de détails.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-medium flex items-center gap-2">
          {progress.status === 'running' ? <Loader2 className="animate-spin text-primary" size={20} /> : null}
          Analyse en cours...
        </h3>
        <span className="text-primary font-bold">{Math.round(progress.progress_percent)}%</span>
      </div>
      
      <div className="w-full bg-[var(--bg-base)] rounded-full h-2.5 mb-4 overflow-hidden" style={{ backgroundColor: 'var(--bg-base)' }}>
        <div 
          className="h-2.5 rounded-full transition-all duration-500 ease-out" 
          style={{ 
            width: `${progress.progress_percent}%`,
            background: 'linear-gradient(90deg, var(--primary), var(--secondary))'
          }}
        ></div>
      </div>
      
      <div className="flex justify-between text-sm text-secondary">
        <span>{progress.files_scanned} fichiers scannés</span>
      </div>
      <div className="mt-2 text-xs text-muted truncate" title={progress.current_file ?? undefined}>
        Fichier actuel: {progress.current_file || '...'}
      </div>
    </div>
  );
}
