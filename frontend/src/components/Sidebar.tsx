import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    TrendingUp,
    Briefcase,
    Newspaper,
    BarChart3,
    Activity,
    Star,
    Brain,
    Shield,
    ChevronLeft,
    ChevronRight,
    Zap,
    Landmark,
    Target,
    Filter,
    Bell,
    Grid3X3,
    GitCompareArrows,
    Calculator
} from 'lucide-react';

interface NavItem {
    path: string;
    label: string;
    icon: React.ReactNode;
    badge?: string;
    section?: string;
}

const navItems: NavItem[] = [
    // Trading
    { path: '/', label: 'Dashboard', icon: <LayoutDashboard size={20} />, section: 'Trading' },
    { path: '/analysis/INFY', label: 'Analysis', icon: <TrendingUp size={20} /> },
    { path: '/portfolio', label: 'Portfolio', icon: <Briefcase size={20} /> },
    { path: '/watchlist', label: 'Watchlist', icon: <Star size={20} /> },
    { path: '/recommendations', label: 'AI Signals', icon: <Brain size={20} />, badge: 'AI' },
    { path: '/alerts', label: 'Alerts', icon: <Bell size={20} />, badge: 'NEW' },
    // Markets
    { path: '/options', label: 'Options', icon: <Target size={20} />, badge: 'F&O', section: 'Markets' },
    { path: '/screener', label: 'Screener', icon: <Filter size={20} /> },
    { path: '/heatmap', label: 'Heatmap', icon: <Grid3X3 size={20} />, badge: 'NEW' },
    { path: '/mutual-funds', label: 'Mutual Funds', icon: <Landmark size={20} /> },
    { path: '/news', label: 'News', icon: <Newspaper size={20} /> },
    // Tools
    { path: '/compare', label: 'Compare', icon: <GitCompareArrows size={20} />, section: 'Tools' },
    { path: '/position-calc', label: 'Position Calc', icon: <Calculator size={20} /> },
    { path: '/backtest', label: 'Backtest', icon: <BarChart3 size={20} /> },
    // System
    { path: '/monitor', label: 'Monitor', icon: <Activity size={20} />, section: 'System' },
    { path: '/admin', label: 'Admin', icon: <Shield size={20} /> },
];

const Sidebar: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);
    const location = useLocation();

    const isActive = (path: string) => {
        if (path === '/') return location.pathname === '/';
        return location.pathname.startsWith(path.split('/').slice(0, 2).join('/'));
    };

    return (
        <aside
            style={{
                width: collapsed ? '72px' : '240px',
                minHeight: '100vh',
                background: 'rgba(10, 14, 26, 0.95)',
                borderRight: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                position: 'sticky',
                top: 0,
                zIndex: 50,
                overflow: 'hidden',
            }}
        >
            {/* Logo */}
            <div style={{
                padding: collapsed ? '20px 0' : '20px 20px',
                borderBottom: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                justifyContent: collapsed ? 'center' : 'flex-start',
            }}>
                <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '10px',
                    background: 'var(--gradient-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    boxShadow: '0 0 16px rgba(99, 102, 241, 0.3)'
                }}>
                    <Zap size={20} color="white" />
                </div>
                {!collapsed && (
                    <div style={{ whiteSpace: 'nowrap' }}>
                        <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                            MarketMind
                        </div>
                        <div style={{ fontSize: '0.65rem', color: 'var(--accent-indigo)', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                            AI Trading Platform
                        </div>
                    </div>
                )}
            </div>

            {/* Nav Items */}
            <nav style={{ flex: 1, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: '4px', overflowY: 'auto' }}>
                {navItems.map((item, idx) => {
                    const active = isActive(item.path);
                    return (
                        <React.Fragment key={item.path}>
                            {item.section && !collapsed && (
                                <div style={{
                                    fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-muted)',
                                    textTransform: 'uppercase', letterSpacing: '0.1em',
                                    padding: idx === 0 ? '0 14px 4px' : '12px 14px 4px',
                                    opacity: 0.6,
                                }}>{item.section}</div>
                            )}
                            {item.section && collapsed && idx > 0 && (
                                <div style={{ height: 1, background: 'var(--border-subtle)', margin: '6px 12px' }} />
                            )}
                            <Link
                                key={item.path}
                                to={item.path}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '12px',
                                    padding: collapsed ? '10px 0' : '10px 14px',
                                    borderRadius: '10px',
                                    color: active ? 'var(--text-primary)' : 'var(--text-muted)',
                                    background: active ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                                    border: active ? '1px solid rgba(99, 102, 241, 0.2)' : '1px solid transparent',
                                    textDecoration: 'none',
                                    fontSize: '0.875rem',
                                    fontWeight: active ? 600 : 400,
                                    transition: 'var(--transition)',
                                    justifyContent: collapsed ? 'center' : 'flex-start',
                                    position: 'relative',
                                    whiteSpace: 'nowrap',
                                }}
                                title={collapsed ? item.label : undefined}
                            >
                                <span style={{
                                    color: active ? 'var(--accent-indigo)' : 'inherit',
                                    display: 'flex',
                                    flexShrink: 0,
                                }}>
                                    {item.icon}
                                </span>
                                {!collapsed && (
                                    <>
                                        <span>{item.label}</span>
                                        {item.badge && (
                                            <span style={{
                                                marginLeft: 'auto',
                                                fontSize: '0.6rem',
                                                fontWeight: 700,
                                                padding: '2px 6px',
                                                borderRadius: '6px',
                                                background: 'var(--gradient-primary)',
                                                color: 'white',
                                                letterSpacing: '0.05em',
                                            }}>
                                                {item.badge}
                                            </span>
                                        )}
                                    </>
                                )}
                                {active && (
                                    <div style={{
                                        position: 'absolute',
                                        left: collapsed ? '50%' : '-8px',
                                        top: collapsed ? 'auto' : '50%',
                                        bottom: collapsed ? '-4px' : 'auto',
                                        transform: collapsed ? 'translateX(-50%)' : 'translateY(-50%)',
                                        width: collapsed ? '20px' : '3px',
                                        height: collapsed ? '3px' : '20px',
                                        borderRadius: '4px',
                                        background: 'var(--accent-indigo)',
                                        boxShadow: '0 0 8px var(--accent-indigo)',
                                    }} />
                                )}
                            </Link>
                        </React.Fragment>
                    );
                })}
            </nav>

            {/* Collapse Toggle */}
            <button
                onClick={() => setCollapsed(!collapsed)}
                style={{
                    padding: '14px',
                    border: 'none',
                    borderTop: '1px solid var(--border-subtle)',
                    background: 'transparent',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    fontSize: '0.75rem',
                    transition: 'var(--transition)',
                    fontFamily: 'inherit',
                }}
            >
                {collapsed ? <ChevronRight size={16} /> : (
                    <>
                        <ChevronLeft size={16} />
                        <span>Collapse</span>
                    </>
                )}
            </button>
        </aside>
    );
};

export default Sidebar;
