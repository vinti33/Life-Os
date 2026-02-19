import React, { useState, useEffect } from 'react';
import metricsService from '../../services/metricsService';
import { Target, TrendingUp, CheckSquare, Sun } from 'lucide-react';
import StatCard from './StatCard';
import clsx from 'clsx';

const WeeklyView = ({ plan }) => {
    const outcomes = plan.outcomes || [];
    const habits = plan.habits || [];
    const goals = plan.goals || [];

    const [serverMetrics, setServerMetrics] = useState(null);

    useEffect(() => {
        const loadMetrics = async () => {
            if (plan?.plan_id) {
                try {
                    const data = await metricsService.getWeekly();
                    setServerMetrics(data);
                } catch (e) {
                    console.error("Failed to load weekly metrics", e);
                }
            }
        };
        loadMetrics();
    }, [plan]);

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Top Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard title="Weekly Goal Progress" value={serverMetrics?.goal_progress || 0} unit="%" trend={serverMetrics?.goal_progress > 50 ? "up" : "neutral"} trendValue={serverMetrics?.goal_progress > 0 ? `${serverMetrics.completed_goals}/${serverMetrics.total_goals}` : "0/0"} icon={TrendingUp} color="indigo" />
                <StatCard title="Key Outcomes" value={`${outcomes.length}`} unit="goals" trend="neutral" icon={Target} color="rose" />
                <StatCard title="Habit Streak" value="--" unit="days" trend="up" icon={Sun} color="amber" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Strategic Outcomes & Linked Goals */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
                        <h3 className="text-white font-bold text-lg mb-6 flex items-center gap-2">
                            <Target className="text-rose-400" size={20} /> Strategic Logic
                        </h3>

                        <div className="space-y-8">
                            {outcomes.map((outcome, idx) => {
                                // Find linked goals
                                const outcomeGoals = goals.filter(g => g.linked_outcome_id === outcome.id);
                                const progress = outcome.target_value > 0 ? (outcome.current_value / outcome.target_value) * 100 : 0;

                                return (
                                    <div key={idx} className="relative pl-6 border-l-2 border-slate-700">
                                        {/* Outcome Header */}
                                        <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-slate-900 border-2 border-rose-500" />
                                        <div className="mb-4">
                                            <div className="flex justify-between items-start">
                                                <h4 className="text-xl font-bold text-white">{outcome.title}</h4>
                                                <span className="text-rose-400 font-mono text-sm">{outcome.current_value} / {outcome.target_value} {outcome.metric}</span>
                                            </div>
                                            {/* Progress Bar */}
                                            <div className="w-full bg-slate-700/30 rounded-full h-1.5 mt-2">
                                                <div className="bg-rose-500 h-1.5 rounded-full" style={{ width: `${Math.min(progress, 100)}%` }} />
                                            </div>
                                        </div>

                                        {/* Linked Tactical Goals */}
                                        <div className="space-y-3">
                                            {outcomeGoals.map((goal, gIdx) => (
                                                <div key={gIdx} className="p-3 rounded-lg bg-slate-700/20 border border-slate-700/30 flex justify-between items-center group hover:bg-slate-700/30 transition-colors">
                                                    <div className="flex items-center gap-3">
                                                        <div className={clsx(
                                                            "w-1.5 h-1.5 rounded-full",
                                                            goal.priority <= 2 ? "bg-rose-400" : "bg-emerald-400"
                                                        )} />
                                                        <div>
                                                            <p className="text-slate-200 font-medium text-sm group-hover:text-white">{goal.title}</p>
                                                            <p className="text-xs text-slate-500">by {goal.deadline_day}</p>
                                                        </div>
                                                    </div>
                                                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">{goal.category}</span>
                                                </div>
                                            ))}
                                            {outcomeGoals.length === 0 && (
                                                <div className="flex items-center gap-2 text-slate-500 text-sm italic p-2">
                                                    <CheckSquare size={14} /> No linked tactical goals
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}

                            {/* Unlinked Goals Section */}
                            {goals.filter(g => !g.linked_outcome_id && !outcomes.some(o => o.id === g.linked_outcome_id)).length > 0 && (
                                <div className="mt-8 pt-8 border-t border-slate-700/50">
                                    <h4 className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-4">Additional Tactics</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {goals.filter(g => !g.linked_outcome_id).map((goal, idx) => (
                                            <div key={idx} className="p-3 rounded-lg bg-slate-700/10 border border-slate-700/30 flex justify-between items-center">
                                                <div>
                                                    <p className="text-slate-300 font-medium text-sm">{goal.title}</p>
                                                    <p className="text-xs text-slate-500">by {goal.deadline_day}</p>
                                                </div>
                                                <span className={clsx(
                                                    "text-[10px] px-1.5 py-0.5 rounded font-bold uppercase",
                                                    goal.priority <= 2 ? "bg-rose-500/10 text-rose-400" : "bg-emerald-500/10 text-emerald-400"
                                                )}>P{goal.priority}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Habit Grid */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
                    <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
                        <Sun className="text-amber-400" size={20} /> Habit Protocol
                    </h3>
                    <div className="space-y-4">
                        {habits.map((habit, idx) => (
                            <div key={idx} className="space-y-2">
                                <div className="flex justify-between items-center text-sm">
                                    <span className="text-slate-200">{habit.habit}</span>
                                    <span className="text-slate-500 text-xs">{habit.frequency}</span>
                                </div>
                                {/* Pseudo-Grid for Mon-Sun */}
                                <div className="grid grid-cols-7 gap-1">
                                    {[...Array(7)].map((_, d) => (
                                        <div key={d} className={clsx(
                                            "h-6 rounded-sm transition-colors",
                                            habit.target_days?.includes(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d])
                                                ? "bg-amber-500/20 border border-amber-500/30"
                                                : "bg-slate-700/30"
                                        )} title={["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d]} />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default WeeklyView;
