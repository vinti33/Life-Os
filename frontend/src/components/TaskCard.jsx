import React from 'react';
import Button from './Button';
import { CheckCircle2, Circle, Clock, MoreVertical, Coffee, Briefcase, GraduationCap, DollarSign, Activity, Heart, Target } from 'lucide-react';

const CATEGORY_CONFIG = {
    health: { icon: Activity, color: 'emerald', label: 'Health' },
    finance: { icon: DollarSign, color: 'cyan', label: 'Finance' },
    learning: { icon: GraduationCap, color: 'fuchsia', label: 'Learning' },
    work: { icon: Briefcase, color: 'indigo', label: 'Work' },
    personal: { icon: Heart, color: 'orange', label: 'Personal' },
    planning: { icon: Target, color: 'blue', label: 'Planning' },
    other: { icon: Coffee, color: 'slate', label: 'Other' },
};

const COLOR_MAP = {
    emerald: { border: 'border-l-emerald-400', icon: 'text-emerald-400', bg: 'bg-emerald-500/10', badge: 'text-emerald-400' },
    cyan: { border: 'border-l-cyan-400', icon: 'text-cyan-400', bg: 'bg-cyan-500/10', badge: 'text-cyan-400' },
    fuchsia: { border: 'border-l-fuchsia-400', icon: 'text-fuchsia-400', bg: 'bg-fuchsia-500/10', badge: 'text-fuchsia-400' },
    indigo: { border: 'border-l-indigo-400', icon: 'text-indigo-400', bg: 'bg-indigo-500/10', badge: 'text-indigo-400' },
    orange: { border: 'border-l-orange-400', icon: 'text-orange-400', bg: 'bg-orange-500/10', badge: 'text-orange-400' },
    blue: { border: 'border-l-blue-400', icon: 'text-blue-400', bg: 'bg-blue-500/10', badge: 'text-blue-400' },
    slate: { border: 'border-l-slate-400', icon: 'text-slate-400', bg: 'bg-slate-500/10', badge: 'text-slate-400' },
};

export default function TaskCard({ task, onStatusUpdate }) {
    const catKey = (task.category || 'other').toLowerCase().split('/')[0].trim();
    const config = CATEGORY_CONFIG[catKey] || CATEGORY_CONFIG.other;
    const colors = COLOR_MAP[config.color] || COLOR_MAP.slate;
    const IconComponent = config.icon;
    // Local state for instant feedback
    const [localStatus, setLocalStatus] = React.useState(task.status);

    React.useEffect(() => {
        setLocalStatus(task.status);
    }, [task.status]);

    const isDone = localStatus === 'done';
    const isMissed = localStatus === 'missed';
    const [isAnimating, setIsAnimating] = React.useState(false);

    const handleToggle = () => {
        setIsAnimating(true);
        setTimeout(() => setIsAnimating(false), 400);

        const newStatus = isDone ? 'pending' : 'done';
        setLocalStatus(newStatus);
        onStatusUpdate(task.id || task._id, newStatus);
    };

    return (
        <div className={`
            glass-card p-5 flex items-center justify-between group
            border-l-[3px] ${colors.border}
            ${isDone ? 'opacity-60' : ''} 
            ${isMissed ? 'opacity-40' : ''}
            ${isAnimating ? 'animate-pop-click' : ''}
        `}>
            <div className={`flex items-center gap-5 transition-transform duration-300 ${isAnimating ? 'scale-95' : ''}`}>
                <button
                    onClick={handleToggle}
                    className={`transition-all duration-300 hover:scale-110 ${isDone ? 'text-emerald-500' : 'text-slate-600 hover:text-slate-300'} ${isAnimating ? 'text-emerald-400' : ''}`}
                >
                    {isDone
                        ? <CheckCircle2 size={24} className="animate-pop-in" />
                        : <Circle size={24} />
                    }
                </button>

                <div className="flex flex-col gap-1.5">
                    <div className="flex items-center gap-3">
                        <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full ${colors.bg}`}>
                            <IconComponent size={12} className={colors.icon} />
                            <span className={`text-[9px] uppercase font-black tracking-[0.15em] ${colors.badge}`}>
                                {config.label}
                            </span>
                        </div>
                        <div className="flex items-center gap-1 text-slate-500 text-[11px] font-mono">
                            <Clock size={11} />
                            {task.start_time} – {task.end_time}
                        </div>
                    </div>
                    <h3 className={`text-base transition-all duration-300 animated-strike ${isDone ? 'done' : ''} ${isDone
                        ? 'text-slate-500 italic'
                        : isMissed
                            ? 'text-red-400/60'
                            : 'text-slate-100 font-semibold'
                        }`}>
                        {task.title}
                    </h3>

                    {task.metrics && task.metrics.target && (
                        <div className="flex items-center gap-1.5 mt-0.5 w-fit rounded px-1.5 py-0.5 bg-slate-800/40 border border-slate-700/30">
                            <Target size={10} className="text-blue-400/80" />
                            <span className="text-[10px] text-slate-400 font-mono tracking-tight leading-none">
                                Target: <b className="text-slate-300 font-semibold text-[10px]">{task.metrics.target} {task.metrics.unit}</b>
                            </span>
                        </div>
                    )}
                </div>
            </div>

            <div className="flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-all duration-200">
                {task.status === 'pending' && (
                    <Button variant="ghost" onClick={() => onStatusUpdate(task.id || task._id, 'missed')} className="text-red-400/50 hover:text-red-400 text-xs !px-3 !py-1.5">
                        Skip
                    </Button>
                )}
                <button className="text-slate-700 hover:text-slate-400 transition-colors p-1">
                    <MoreVertical size={16} />
                </button>
            </div>
        </div>
    );
}
