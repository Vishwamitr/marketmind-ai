import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface MetricsCardProps {
    label: string;
    value: string | number;
    trend?: 'up' | 'down' | 'neutral';
    subValue?: string;
    color?: 'blue' | 'green' | 'red' | 'purple' | 'amber' | 'cyan';
    icon?: React.ReactNode;
}

const colorMap = {
    blue: { gradient: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(99,102,241,0.1))', border: 'rgba(59,130,246,0.2)', glow: '0 0 20px rgba(59,130,246,0.1)' },
    green: { gradient: 'linear-gradient(135deg, rgba(16,185,129,0.15), rgba(6,182,212,0.1))', border: 'rgba(16,185,129,0.2)', glow: '0 0 20px rgba(16,185,129,0.1)' },
    red: { gradient: 'linear-gradient(135deg, rgba(239,68,68,0.15), rgba(245,158,11,0.1))', border: 'rgba(239,68,68,0.2)', glow: '0 0 20px rgba(239,68,68,0.1)' },
    purple: { gradient: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(99,102,241,0.1))', border: 'rgba(139,92,246,0.2)', glow: '0 0 20px rgba(139,92,246,0.1)' },
    amber: { gradient: 'linear-gradient(135deg, rgba(245,158,11,0.15), rgba(234,179,8,0.1))', border: 'rgba(245,158,11,0.2)', glow: '0 0 20px rgba(245,158,11,0.1)' },
    cyan: { gradient: 'linear-gradient(135deg, rgba(6,182,212,0.15), rgba(59,130,246,0.1))', border: 'rgba(6,182,212,0.2)', glow: '0 0 20px rgba(6,182,212,0.1)' },
};

const MetricsCard: React.FC<MetricsCardProps> = ({ label, value, trend, subValue, color = 'blue', icon }) => {
    const colors = colorMap[color];

    const getTrendIcon = () => {
        switch (trend) {
            case 'up': return <ArrowUpRight size={18} style={{ color: 'var(--accent-green)' }} />;
            case 'down': return <ArrowDownRight size={18} style={{ color: 'var(--accent-red)' }} />;
            case 'neutral': return <Minus size={18} style={{ color: 'var(--text-muted)' }} />;
            default: return null;
        }
    };

    return (
        <div
            className="animate-fade-in"
            style={{
                background: colors.gradient,
                border: `1px solid ${colors.border}`,
                borderRadius: 'var(--radius)',
                padding: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                transition: 'var(--transition)',
                cursor: 'default',
                boxShadow: colors.glow,
            }}
        >
            <div>
                <p style={{
                    color: 'var(--text-muted)',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    margin: '0 0 8px 0',
                }}>
                    {label}
                </p>
                <p style={{
                    color: 'var(--text-primary)',
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    margin: '0 0 4px 0',
                    lineHeight: 1.1,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                }}>
                    {value}
                    {getTrendIcon()}
                </p>
                {subValue && (
                    <p style={{
                        color: 'var(--text-secondary)',
                        fontSize: '0.75rem',
                        margin: 0,
                    }}>
                        {subValue}
                    </p>
                )}
            </div>
            {icon && (
                <div style={{
                    opacity: 0.4,
                    flexShrink: 0,
                }}>
                    {icon}
                </div>
            )}
        </div>
    );
};

export default MetricsCard;
