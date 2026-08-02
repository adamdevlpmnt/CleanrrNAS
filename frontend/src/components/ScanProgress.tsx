import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { ScanProgress as IScanProgress } from '../types';
import { Loader2 } from 'lucide-react';

interface Props {
  scanId: number;
  onComplete?: () => void;
}

export function ScanProgress({ scanId, onComplete }: Props) {
  const [progress, setProgress] = useState<IScanProgress | null>(null);
  
  useEffect(() => {
    let timeoutId: number;
    
    const poll = async () => {
      try {
        const data = await api.getScanProgress(scanId);
        setProgress(data);
        
        if (data.status === 'completed' || data.status === 'failed') {
          if (onComplete) onComplete();
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
  }, [scanId, onComplete]);
  
  if (!progress) return <div className="card flex items-center gap-4"><Loader2 className="animate-spin text-primary" /> <span>Initialisation du scan...</span></div>;
  
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
      <div className="mt-2 text-xs text-muted truncate" title={progress.current_file}>
        Fichier actuel: {progress.current_file || '...'}
      </div>
    </div>
  );
}
