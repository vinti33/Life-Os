import React, { useMemo, useState, useEffect } from 'react';
import metricsService from '../../services/metricsService';
import { Flag, TrendingUp, Calendar, PieChart } from 'lucide-react';
import StatCard from './StatCard';
import clsx from 'clsx';
import PerformanceChart from './PerformanceChart';

const MonthlyView = ({ plan }) => {
    const milestones = plan.milestones || [];
    const kpis = plan.kpis || [];
    const strategicGoals = plan.strategic_goals || [];

    const [serverMetrics, setServerMetrics] = useState(null);

    useEffect(() => {
        const loadMetrics = async () => {
            if (plan?.plan_id) {
                try {
                    const data = await metricsService.getMonthly();
                    setServerMetrics(data);
                } catch (e) {
                    console.error("Failed to load monthly metrics", e);
                }
            }
        };
        loadMetrics();
    }, [plan]);

    // Mock trend data for KPIs since we don't have history yet
    const kpiTrends = useMemo(() => {
        return [
            { date: 'Week 1', value: 20 },
            { date: 'Week 2', value: 45 },
            { date: 'Week 3', value: 60 },
            { date: 'Week 4', value: 85 },
        ];
    }, []);

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* High Level Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard title="Strategic Progress" value={`${serverMetrics?.milestone_progress || 0}%`} unit="completed" trend="up" trendValue="12%" icon={Flag} color="indigo" />
                <StatCard title="KPI Health" value={`${kpis.length}`} unit="metrics" trend="neutral" icon={PieChart} color="emerald" />
                <StatCard title="Days Remaining" value="12" unit="days" icon={Calendar} color="slate" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main: Milestones & Goals */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
                        <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
                            <Flag className="text-indigo-400" size={20} /> Strategic Logic
                        </h3>
                        <div className="space-y-2 mb-6">
                            {strategicGoals.map((goal, idx) => (
                                <div key={idx} className="flex items-center gap-3 text-slate-300">
                                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                                    {goal}
                                </div>
                            ))}
                        </div>

                        <h4 className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-3">Milestone Timeline</h4>
                        <div className="space-y-4">
                            {milestones.map((ms, idx) => (
                                <div key={idx} className="relative pl-6 border-l border-slate-700 pb-4 last:pb-0">
                                    <div className={clsx(
                                        "absolute -left-[5px] top-1 w-2.5 h-2.5 rounded-full border-2",
                                        ms.status === 'completed' ? "bg-emerald-500 border-emerald-500" : "bg-slate-900 border-slate-500"
                                    )} />
                                    <div className="flex justify-between items-start mb-1">
                                        <h5 className="text-white font-medium">{ms.title}</h5>
                                        <span className="text-xs text-slate-500">{ms.deadline_date}</span>
                                    </div>
                                    <div className="w-full bg-slate-700/30 rounded-full h-1.5 mt-2">
                                        <div
                                            className="bg-emerald-500 h-1.5 rounded-full"
                                            style={{ width: `${ms.progress || 0}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Side: KPI Cards */}
                <div className="space-y-4">
                    {kpis.map((kpi, idx) => (
                        <div key={idx} className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-5">
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <p className="text-slate-400 text-xs font-bold uppercase">{kpi.name}</p>
                                    <h3 className="text-2xl font-bold text-white">{kpi.actual_value || 0} <span className="text-sm text-slate-500 font-normal">{kpi.unit}</span></h3>
                                </div>
                                <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
                                    <TrendingUp size={16} />
                                </div>
                            </div>
                            <div className="w-full bg-slate-700/30 rounded-full h-1.5 mb-2">
                                <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: '60%' }} />
                            </div>
                            <p className="text-xs text-slate-500 text-right">Target: {kpi.target_value} {kpi.unit}</p>
                        </div>
                    ))}

                    {/* Mock Chart for first KPI if exists */}
                    {kpis.length > 0 && (
                        <PerformanceChart data={kpiTrends} dataKey="value" color="#10b981" height={150} />
                    )}
                </div>
            </div>
        </div>
    );
};

export default MonthlyView;
