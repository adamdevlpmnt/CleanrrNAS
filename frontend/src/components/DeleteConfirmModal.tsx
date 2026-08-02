import React, { useState } from 'react';
import { DeletionPreview } from '../types';
import { formatBytes } from '../utils/format';
import { AlertTriangle, Trash2, X } from 'lucide-react';

interface Props {
  preview: DeletionPreview;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting: boolean;
}

export function DeleteConfirmModal({ preview, onConfirm, onCancel, isDeleting }: Props) {
  const [confirmText, setConfirmText] = useState('');
  
  const canConfirm = confirmText === 'SUPPRIMER';
  const hasHardlinks = preview.real_gain < preview.total_size;

  return (
    <div className="modal-overlay">
      <div className="modal-content border-danger">
        <div className="modal-header text-danger">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <AlertTriangle />
            Confirmation de suppression
          </h2>
          <button onClick={onCancel} disabled={isDeleting} className="text-muted hover:text-white">
            <X size={24} />
          </button>
        </div>
        
        <div className="modal-body space-y-6">
          <p className="text-sm">
            Vous êtes sur le point de supprimer <strong>{preview.files.length}</strong> fichier(s).
            Cette action est irréversible. Les fichiers seront supprimés du disque, ainsi que les torrents associés dans qBittorrent.
          </p>
          
          <div className="grid grid-cols-2 gap-4 bg-[var(--bg-base)] p-4 rounded-lg">
            <div>
              <span className="text-xs text-muted block">Taille totale sélectionnée</span>
              <span className="font-bold">{formatBytes(preview.total_size)}</span>
            </div>
            <div>
              <span className="text-xs text-muted block">Espace réel libéré</span>
              <span className={`font-bold ${hasHardlinks ? 'text-warning' : 'text-success'}`}>
                {formatBytes(preview.real_gain)}
              </span>
            </div>
          </div>
          
          {hasHardlinks && (
            <div className="bg-[var(--warning-bg)] border border-[var(--warning)] p-3 rounded-lg text-sm text-warning flex items-start gap-2">
              <AlertTriangle size={18} className="shrink-0 mt-0.5" />
              <p>
                L'espace réel libéré est inférieur à la taille totale car certains fichiers ont des liens physiques.
                L'espace ne sera récupéré que lorsque <strong>tous</strong> les liens pointant vers ces données seront supprimés.
              </p>
            </div>
          )}
          
          {preview.warnings && preview.warnings.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-bold text-danger">Avertissements :</h3>
              <ul className="text-xs space-y-1 text-danger list-disc pl-4">
                {preview.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}
          
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Veuillez taper <strong className="text-danger select-none">SUPPRIMER</strong> pour confirmer :
            </label>
            <input 
              type="text" 
              className="input text-center text-xl font-bold tracking-widest uppercase"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value.toUpperCase())}
              placeholder="SUPPRIMER"
              disabled={isDeleting}
            />
          </div>
        </div>
        
        <div className="modal-footer bg-[var(--bg-base)]">
          <button className="btn btn-ghost" onClick={onCancel} disabled={isDeleting}>
            Annuler
          </button>
          <button 
            className="btn btn-danger" 
            onClick={onConfirm}
            disabled={!canConfirm || isDeleting}
          >
            {isDeleting ? 'Suppression...' : (
              <>
                <Trash2 size={18} />
                Supprimer définitivement
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
