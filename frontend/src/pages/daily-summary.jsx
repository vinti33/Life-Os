import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useStats } from '../store/statsStore';
import Button from '../components/Button';
import MainLayout from '../components/MainLayout';
import { ArrowLeft, TrendingUp } from 'lucide-react';

export default function DailySummary() {
    const { dailyStats, history } = useStats();
    const router = useRouter();
    const [animatedProgress, setAnimatedProgress] = useState(0);

    useEffect(() => {
        const target = dailyStats?.success_percentage || 0;
        const timer = setTimeout(() => setAnimatedProgress(target), 300);
        return () => clearTimeout(timer);
    }, [dailyStats]);

    const successPct = dailyStats?.success_percentage || 0;
    const strokeDashoffset = 502 - (502 * animatedProgress) / 100;

    const getProgressColor = (pct) => {
        if (pct >= 80) return 'text-emerald-500';
        if (pct >= 50) return 'text-amber-500';
        return 'text-red-500';
    };

    return (
        <MainLayout>
            <div className="max-w-4xl mx-auto pb-12 animate-fade-in">
                {/* Header */}
                <header className="mb-10 text-center">
                    <button onClick={() => router.back()} className="flex items-center gap-1.5 text-slate-500 hover:text-white mb-6 text-sm transition-colors mx-auto md:mx-0">
                        <ArrowLeft size={16} /> Back
                    </button>
                    <h1 className="text-3xl md:text-4xl font-black mb-2">
                        Day in <span className="text-gradient">Review</span>
                    </h1>
                    <p className="text-slate-500 text-sm">Here's how your day went. Keep building momentum.</p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
                    {/* Progress Ring */}
                    <div className="glass-card p-8 flex flex-col items-center justify-center animate-fade-in delay-100">
                        <div className="relative w-44 h-44 mb-6">
                            <svg className="w-full h-full transform -rotate-90">
                                <circle cx="88" cy="88" r="80" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-white/5" />
                                <circle
                                    cx="88" cy="88" r="80"
                                    stroke="currentColor" strokeWidth="8" fill="transparent"
                                    className={`${getProgressColor(successPct)} transition-all duration-[2s] ease-out`}
                                    strokeDasharray={502}
                                    strokeDashoffset={strokeDashoffset}
                                    strokeLinecap="round"
                                />
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-4xl font-black text-white">{successPct}%</span>
                                <span className="text-[10px] uppercase text-slate-500 font-bold tracking-wider">Success</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-8 w-full border-t border-white/5 pt-5">
                            <div className="text-center flex-1">
                                <p className="text-2xl font-bold text-emerald-400">{dailyStats?.completed_tasks || 0}</p>
                                <p className="text-[10px] uppercase text-slate-500 font-bold tracking-wider">Done</p>
                            </div>
                            <div className="w-px h-8 bg-white/5" />
                            <div className="text-center flex-1">
                                <p className="text-2xl font-bold text-red-400">{dailyStats?.missed_tasks || 0}</p>
                                <p className="text-[10px] uppercase text-slate-500 font-bold tracking-wider">Missed</p>
                            </div>
                        </div>
                    </div>

                    {/* History Chart */}
                    <div className="glass-card p-8 animate-fade-in delay-200">
                        <div className="flex items-center gap-2 mb-6">
                            <TrendingUp size={16} className="text-indigo-400" />
                            <h3 className="text-lg font-bold text-white">Weekly Trend</h3>
                        </div>
                        <div className="space-y-3">
                            {history.slice(0, 7).map((entry, i) => (
                                <div key={i} className="flex items-center gap-3 animate-fade-in" style={{ animationDelay: `${i * 80}ms` }}>
                                    <span className="text-[11px] font-mono text-slate-500 w-20 shrink-0">
                                        {new Date(entry.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                                    </span>
                                    <div className="flex-1 bg-white/5 h-2 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full transition-all duration-700 ${entry.success_percentage >= 80 ? 'bg-gradient-to-r from-emerald-500 to-cyan-500' :
                                                    entry.success_percentage >= 50 ? 'bg-gradient-to-r from-amber-500 to-orange-500' :
                                                        'bg-gradient-to-r from-red-500 to-pink-500'
                                                }`}
                                            style={{ width: `${entry.success_percentage}%` }}
                                        />
                                    </div>
                                    <span className="text-xs font-bold text-slate-400 w-10 text-right">{Math.round(entry.success_percentage)}%</span>
                                </div>
                            ))}
                            {history.length === 0 && (
                                <p className="text-slate-600 text-sm text-center py-6">No history yet. Complete some tasks to see trends.</p>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex justify-center">
                    <Button variant="secondary" onClick={() => router.push('/dashboard')} className="px-10 py-3">
                        Back to Dashboard
                    </Button>
                </div>
            </div>
        </MainLayout>
    );
}
