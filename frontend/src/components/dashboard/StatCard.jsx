import React from 'react';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import clsx from 'clsx';

const StatCard = ({ title, value, unit, trend, trendValue, icon: Icon, color = 'indigo' }) => {
    const isPositive = trend === 'up';
    const isNegative = trend === 'down';
    const isNeutral = trend === 'flat';

    return (
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-5 hover:border-slate-600 transition-colors group">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <p className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-1">{title}</p>
                    <div className="flex items-baseline gap-1">
                        <h3 className="text-2xl font-bold text-white tracking-tight">
                            {value}
                        </h3>
                        {unit && <span className="text-slate-500 text-sm font-medium">{unit}</span>}
                    </div>
                </div>
                <div className={clsx(
                    "p-2 rounded-lg transition-colors",
                    color === 'indigo' && "bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500/20",
                    color === 'emerald' && "bg-emerald-500/10 text-emerald-400 group-hover:bg-emerald-500/20",
                    color === 'rose' && "bg-rose-500/10 text-rose-400 group-hover:bg-rose-500/20",
                    color === 'amber' && "bg-amber-500/10 text-amber-400 group-hover:bg-amber-500/20",
                )}>
                    {Icon && <Icon size={20} />}
                </div>
            </div>

            {trendValue && (
                <div className="flex items-center gap-2 text-xs font-medium">
                    <span className={clsx(
                        "flex items-center gap-0.5 px-1.5 py-0.5 rounded-md",
                        isPositive && "text-emerald-400 bg-emerald-500/10",
                        isNegative && "text-rose-400 bg-rose-500/10",
                        isNeutral && "text-slate-400 bg-slate-500/10",
                    )}>
                        {isPositive && <ArrowUp size={12} />}
                        {isNegative && <ArrowDown size={12} />}
                        {isNeutral && <Minus size={12} />}
                        {trendValue}
                    </span>
                    <span className="text-slate-500">vs last period</span>
                </div>
            )}
        </div>
    );
};

export default StatCard;
