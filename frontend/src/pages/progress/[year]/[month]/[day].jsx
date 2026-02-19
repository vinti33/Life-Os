import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import progressService from '../../../../services/progressService';
import { ArrowLeft, CheckCircle, Circle, Clock, Tag, Lightbulb } from 'lucide-react';
import clsx from 'clsx';
import Link from 'next/link';

const DayDetailView = () => {
    const router = useRouter();
    const { year, month, day } = router.query;
    const [data, setData] = useState(null);
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(true);

    const dateStr = (year && month && day) ? `${year}-${month}-${day}` : null;

    useEffect(() => {
        if (!dateStr) return;

        const fetchData = async () => {
            setLoading(true);
            try {
                // Fetch day detail and global suggestions in parallel
                // Note: Suggestions are global, but we show them here as requested
                const [dayResult, suggResult] = await Promise.all([
                    progressService.getDayDetail(dateStr),
                    progressService.getSuggestions()
                ]);
                setData(dayResult);
                setSuggestions(suggResult);
            } catch (error) {
                console.error("Failed to load data", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [dateStr]);

    if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-500">Loading details...</div>;

    if (!data?.found) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center space-y-4">
                <h1 className="text-2xl font-bold text-white">No Plan Found</h1>
                <p className="text-slate-400">There was no active plan for {dateStr}.</p>
                <Link href={`/progress/${year}/${month}`} className="text-indigo-400 hover:text-indigo-300">
                    Back to Calendar
                </Link>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto p-4 md:p-8 space-y-8 animate-fadeIn">
            <header className="flex items-center gap-4">
                <Link href={`/progress/${year}/${month}`} className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
                    <ArrowLeft size={24} />
                </Link>
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">
                        {new Date(year, month - 1, day).toLocaleDateString('default', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                    </h1>
                    <p className="text-slate-400 text-sm italic">"{data.summary}"</p>
                </div>
            </header>

            {/* Score Card */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-8 flex items-center justify-between">
                <div>
                    <h2 className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-1">Daily Score</h2>
                    <div className="text-5xl font-mono font-bold text-white">
                        {data.percentage}<span className="text-2xl text-slate-500">%</span>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-sm text-slate-400 mb-1">Items Completed</div>
                    <div className="text-2xl font-bold text-white">
                        {data.completed} <span className="text-slate-500">/ {data.total}</span>
                    </div>
                </div>
            </div>

            {/* Suggestions Box */}
            {suggestions.length > 0 && (
                <div className="bg-indigo-900/20 border border-indigo-500/30 rounded-xl p-5 mb-6">
                    <h3 className="text-indigo-400 text-sm font-bold uppercase tracking-wider mb-3 flex items-center gap-2">
                        <Lightbulb size={16} /> AI Observations
                    </h3>
                    <div className="space-y-3">
                        {suggestions.map((s, idx) => (
                            <div key={idx} className="flex gap-3 items-start text-sm text-indigo-200/80">
                                <span className="mt-1 w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0" />
                                <p>{s.message}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Task List */}
            <div className="space-y-4">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <CheckCircle className="text-emerald-500" size={20} />
                    Execution Log
                </h3>

                {data.tasks.map((task, idx) => (
                    <div key={task.id} className={clsx(
                        "flex items-start gap-4 p-4 rounded-xl border transition-all",
                        task.status === 'done'
                            ? "bg-slate-800/30 border-slate-700/50 opacity-75"
                            : "bg-slate-800 border-slate-700"
                    )}>
                        <div className="mt-1">
                            {task.status === 'done' ? (
                                <CheckCircle className="text-emerald-500" size={20} />
                            ) : (
                                <Circle className="text-slate-500" size={20} />
                            )}
                        </div>
                        <div className="flex-1">
                            <h4 className={clsx(
                                "font-medium text-lg",
                                task.status === 'done' ? "text-slate-400 line-through" : "text-white"
                            )}>
                                {task.title}
                            </h4>
                            <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                                <span className="flex items-center gap-1">
                                    <Tag size={12} /> {task.category}
                                </span>
                                {task.priority <= 2 && (
                                    <span className="flex items-center gap-1 text-rose-400 font-bold">
                                        <Clock size={12} /> High Priority
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}

                {data.tasks.length === 0 && (
                    <div className="text-center p-8 text-slate-500">No tasks recorded for this day.</div>
                )}
            </div>
        </div>
    );
};

export default DayDetailView;
