import React from 'react';
import { Calendar, CalendarDays, CalendarRange, DollarSign } from 'lucide-react';

const TABS = [
    { id: 'daily', label: 'Daily', icon: Calendar },
    { id: 'weekly', label: 'Weekly', icon: CalendarDays },
    { id: 'monthly', label: 'Monthly', icon: CalendarRange },
    { id: 'finance', label: 'Finance', icon: DollarSign },
];

function PlanTabs({ activeTab, onTabChange }) {
    return (
        <div style={{
            display: 'flex', gap: '8px', padding: '6px',
            background: 'rgba(0,0,0,0.2)', borderRadius: '16px',
            marginBottom: '24px', border: '1px solid rgba(255,255,255,0.05)'
        }}>
            {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                    <button
                        key={tab.id}
                        onClick={() => onTabChange(tab.id)}
                        style={{
                            flex: 1,
                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                            padding: '10px', borderRadius: '12px',
                            background: isActive ? 'rgba(99,102,241,0.15)' : 'transparent',
                            border: isActive ? '1px solid rgba(99,102,241,0.3)' : '1px solid transparent',
                            color: isActive ? '#a5b4fc' : '#94a3b8',
                            fontSize: '13px', fontWeight: 600,
                            cursor: 'pointer', transition: 'all 0.2s',
                        }}
                        onMouseEnter={(e) => !isActive && (e.currentTarget.style.background = 'rgba(255,255,255,0.03)')}
                        onMouseLeave={(e) => !isActive && (e.currentTarget.style.background = 'transparent')}
                    >
                        <Icon size={16} />
                        {tab.label}
                    </button>
                );
            })}
        </div>
    );
}

export default PlanTabs;
