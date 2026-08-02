import React from 'react';

interface Props {
  title: string;
  value: React.ReactNode;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
}

export function StatsCard({ title, value, subtitle, icon, color = 'var(--primary)' }: Props) {
  return (
    <div className="card" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-sm text-muted font-medium mb-1">{title}</h3>
          <div className="text-2xl font-bold">{value}</div>
          {subtitle && <div className="text-xs text-secondary mt-1">{subtitle}</div>}
        </div>
        <div style={{ color }}>
          {icon}
        </div>
      </div>
    </div>
  );
}
