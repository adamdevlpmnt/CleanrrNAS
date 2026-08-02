interface Props {
  connected: boolean;
  label: string;
  version?: string | null;
}

export function ConnectionDot({ connected, label, version }: Props) {
  return (
    <div className="flex items-center gap-2" title={version ? `Version: ${version}` : undefined}>
      <div 
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: connected ? 'var(--success)' : 'var(--danger)',
          boxShadow: `0 0 8px ${connected ? 'var(--success)' : 'var(--danger)'}`
        }}
      />
      <span className="text-sm text-secondary">{label}</span>
    </div>
  );
}
