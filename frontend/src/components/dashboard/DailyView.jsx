import React, { useMemo, useState, useEffect } from 'react';
import metricsService from '../../services/metricsService';
import { Clock, CheckCircle, Zap, Activity, Calendar } from 'lucide-react';
import StatCard from './StatCard';
import PerformanceChart from './PerformanceChart';
import clsx from 'clsx';

const DailyView = ({ plan }) => {
    // 1. Calculate Metrics
    const metrics = useMemo(() => {
        const totalTasks = plan.tasks.length;
        const highPriority = plan.tasks.filter(t => t.priority <= 2).length;
        // Mock focus hours calculation based on tasks marked as "Deep Work" or distinct category
        const focusHours = plan.tasks.reduce((acc, t) => {
            if (t.category === 'work' || t.category === 'learning') return acc + (t.estimated_duration || 60) / 60;
            return acc;
        }, 0).toFixed(1);

        return { totalTasks, highPriority, focusHours };
    }, [plan]);

    // 2. Generate Energy Data for Chart
    const energyData = useMemo(() => {
        return plan.tasks
            .filter(t => t.start_time) // Ensure start_time exists
            .sort((a, b) => a.start_time.localeCompare(b.start_time))
            .map(t => ({
                date: t.start_time, // X-axis
                energy: t.energy_required === 'high' ? 100 : t.energy_required === 'medium' ? 60 : 30,
                title: t.title
            }));
    }, [plan]);

    const [serverMetrics, setServerMetrics] = useState(null);

    useEffect(() => {
        const loadMetrics = async () => {
            // Only fetch if plan is potentially active (has ID)
            if (plan?.plan_id) {
                try {
                    const data = await metricsService.getDaily();
                    setServerMetrics(data);
                } catch (e) {
                    console.error("Failed to load daily metrics", e);
                }
            }
        };
        loadMetrics();
    }, [plan]);

    // 3. Render Task Timeline
    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Top Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Daily Score" value={serverMetrics?.productivity_score || metrics.totalTasks > 0 ? (metrics.totalTasks - metrics.highPriority) * 2 : 0} unit="/100" trend="up" trendValue="12%" icon={Activity} color="indigo" />
                <StatCard title="Focus Planned" value={metrics.focusHours} unit="hrs" trend="flat" trendValue="0%" icon={Zap} color="amber" />
                <StatCard title="Tasks Completed" value={serverMetrics ? `${serverMetrics.completed}/${serverMetrics.total}` : metrics.totalTasks} unit="items" icon={CheckCircle} color="emerald" />
                <StatCard title="High Priority" value={metrics.highPriority} unit="critical" icon={Clock} color="rose" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Schedule (2/3 width) */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
                        <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
                            <Calendar className="text-indigo-400" size={20} /> Today's Protocol
                        </h3>

                        <div className="space-y-3">
                            {plan.tasks.map((task, idx) => (
                                <div key={idx} className="flex items-start gap-4 p-3 rounded-lg hover:bg-slate-700/30 transition-colors border border-transparent hover:border-slate-700 group">
                                    {/* Time Column */}
                                    <div className="flex flex-col items-end min-w-[60px] text-right">
                                        <span className="text-slate-300 font-mono text-sm font-medium">{task.start_time}</span>
                                        <span className="text-slate-600 text-xs">{task.end_time}</span>
                                    </div>

                                    {/* Timeline Line */}
                                    <div className="relative flex flex-col items-center self-stretch">
                                        <div className={clsx(
                                            "w-3 h-3 rounded-full border-2 z-10 bg-slate-900",
                                            task.priority <= 2 ? "border-rose-500" : "border-slate-500"
                                        )} />
                                        {idx !== plan.tasks.length - 1 && <div className="w-0.5 grow bg-slate-800 absolute top-3" />}
                                    </div>

                                    {/* Task Card */}
                                    <div className="flex-1">
                                        <div className="flex justify-between items-start">
                                            <h4 className={clsx(
                                                "font-medium text-slate-200 group-hover:text-white transition-colors",
                                                task.priority <= 2 && "text-white"
                                            )}>{task.title}</h4>
                                            <span className={clsx(
                                                "text-[10px] uppercase font-bold px-2 py-0.5 rounded-full tracking-wider",
                                                task.category === 'work' && "bg-blue-500/10 text-blue-400",
                                                task.category === 'health' && "bg-emerald-500/10 text-emerald-400",
                                                task.category === 'learning' && "bg-amber-500/10 text-amber-400",
                                                (task.category === 'personal' || task.category === 'other') && "bg-slate-500/10 text-slate-400",
                                                task.category === 'finance' && "bg-indigo-500/10 text-indigo-400",
                                            )}>{task.category}</span>
                                        </div>

                                        {/* Meta Row */}
                                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                                            {task.estimated_duration && <span>⏱ {task.estimated_duration}m</span>}
                                            {task.energy_required && (
                                                <span className={clsx(
                                                    "flex items-center gap-1",
                                                    task.energy_required === 'high' && "text-rose-400",
                                                    task.energy_required === 'medium' && "text-amber-400",
                                                    task.energy_required === 'low' && "text-emerald-400",
                                                )}>
                                                    <Zap size={10} /> {task.energy_required.toUpperCase()} ENERGY
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right: Charts & Stats (1/3 width) */}
                <div className="space-y-6">
                    <PerformanceChart data={energyData} dataKey="energy" color="#f59e0b" height={250} />

                    {/* Time Portfolio */}
                    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-5">
                        <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-4">Time Capital</h3>
                        <div className="space-y-3">
                            {plan.capital_allocation?.filter(c => c.resource_type === 'time').map((cap, idx) => (
                                <div key={idx} className="space-y-1">
                                    <div className="flex justify-between text-xs">
                                        <span className="text-slate-300 capitalize">{cap.category}</span>
                                        <span className="text-slate-500">{cap.amount}h ({cap.percentage}%)</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-slate-700/50 rounded-full overflow-hidden">
                                        <div className={clsx(
                                            "h-full rounded-full",
                                            cap.category === 'work' && "bg-blue-500",
                                            cap.category === 'health' && "bg-emerald-500",
                                            cap.category === 'learning' && "bg-amber-500",
                                            !['work', 'health', 'learning'].includes(cap.category) && "bg-slate-500"
                                        )} style={{ width: `${cap.percentage}%` }} />
                                    </div>
                                </div>
                            ))}
                            {(!plan.capital_allocation || plan.capital_allocation.length === 0) && (
                                <p className="text-xs text-slate-500 italic">No time allocation data available.</p>
                            )}
                        </div>
                    </div>

                    {/* Reflection / Notes Box */}
                    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-5">
                        <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-2">Daily Focus</h3>
                        <p className="text-slate-200 italic">"{plan.plan_summary}"</p>
                    </div>

                    {/* Clarification Box */}
                    {plan.clarification_questions?.length > 0 && (
                        <div className="bg-indigo-900/20 border border-indigo-500/30 rounded-xl p-5">
                            <h3 className="text-indigo-400 text-sm font-bold uppercase tracking-wider mb-2">Pending Questions</h3>
                            <ul className="list-disc list-inside text-sm text-indigo-200/80 space-y-1">
                                {plan.clarification_questions.map((q, i) => <li key={i}>{q}</li>)}
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DailyView;
