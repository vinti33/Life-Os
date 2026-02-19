import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import progressService from '../../services/progressService';
import { ChevronLeft, ChevronRight, Calendar, Activity } from 'lucide-react';
import clsx from 'clsx';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const YearView = () => {
    const router = useRouter();
    const currentYear = new Date().getFullYear();
    const [year, setYear] = useState(currentYear);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await progressService.getYearProgress(year);
                setData(result);
            } catch (error) {
                console.error("Failed to load year progress", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [year]);

    const handleMonthClick = (month) => {
        router.push(`/progress/${year}/${month}`);
    };

    // Helper to render heatmap grid (GitHub Style)
    const renderHeatmap = () => {
        if (!data?.heatmap) return null;

        // 1. Generate full year matrix
        const startDate = new Date(year, 0, 1);
        const endDate = new Date(year, 11, 31);

        // Map date -> data
        const dateMap = {};
        data.heatmap.forEach(d => dateMap[d.date] = d);

        // Generate weeks
        const weeks = [];
        let currentWeek = [];
        let currentDate = new Date(startDate);

        // Pad beginning of first week if not Sunday/Monday (aligned to Monday for GitHub style)
        // GitHub uses Sunday(0) to Saturday(6) usually, or Mon(1)-Sun(0)
        // User image rows: Mon, Wed, Fri labels implies Mon-Sun or Sun-Sat layout.
        // Let's standard on Sunday (0) at top or Monday (1) 
        // Image shows Mon, Wed, Fri as rows. This usually means Weeks are Columns.
        // Rows: 0=Sun, 1=Mon... 
        // If labels are Mon, Wed, Fri, then Row 1 is Mon. 
        // Let's assume standard: 7 Rows (Sun-Sat), ~53 Columns.

        // Normalize to start on a Sunday for simplified grid
        const dayOfWeek = currentDate.getDay(); // 0=Sun
        // If we want Mon-Sun, we shift. Let's stick to standard Sun-Sat for easy JS.

        // Backtrack to previous Sunday to align grid
        currentDate.setDate(currentDate.getDate() - dayOfWeek);

        while (currentDate <= endDate || currentWeek.length > 0) {
            // Safety break
            if (currentDate.getFullYear() > year && currentWeek.length === 0) break;

            const dStr = currentDate.toISOString().split('T')[0];
            const isCurrentYear = currentDate.getFullYear() === year;

            currentWeek.push({
                date: dStr,
                data: isCurrentYear ? dateMap[dStr] : null,
                inYear: isCurrentYear,
                month: currentDate.getMonth(),
                day: currentDate.getDate()
            });

            if (currentWeek.length === 7) {
                weeks.push(currentWeek);
                currentWeek = [];
            }

            currentDate.setDate(currentDate.getDate() + 1);
        }

        // Render Grid
        // Flex row of columns
        return (
            <div className="overflow-x-auto pb-4 custom-scrollbar">
                <div className="min-w-[800px] flex flex-col gap-2">
                    {/* Month Labels */}
                    <div className="flex text-xs text-slate-400 pl-8">
                        {months.map((m, i) => (
                            // Only show label if the month starts roughly here? 
                            // Simplified: Just space them out or find the index where month changes
                            <div key={m} className="flex-1">{m}</div>
                        ))}
                        {/* Implementing precise month labels is tricky with flex headers. 
                             Better approach: Render labels based on week index. */}
                    </div>

                    <div className="flex gap-1 relative">
                        {/* Y-Axis Labels */}
                        <div className="flex flex-col justify-between text-[10px] text-slate-500 pr-2 py-1 h-[112px] sticky left-0 bg-[#0f172a] z-10">
                            <span>Mon</span>
                            <span>Wed</span>
                            <span>Fri</span>
                        </div>

                        {/* Weeks */}
                        {weeks.map((week, wIdx) => {
                            // Check if first week of a month to add label above?
                            // We'll do labels separately later if needed, or simple top row.
                            return (
                                <div key={wIdx} className="flex flex-col gap-1">
                                    {week.map((day, dIdx) => (
                                        <div
                                            key={day.date}
                                            onClick={() => day.inYear && day.data && router.push(`/progress/${year}/${String(day.month + 1).padStart(2, '0')}/${String(day.day).padStart(2, '0')}`)}
                                            className={clsx(
                                                "w-3 h-3 rounded-sm transition-colors",
                                                !day.inYear ? "opacity-0" : "cursor-pointer hover:ring-1 hover:ring-white",
                                                !day.data || day.data.percentage === 0 ? "bg-slate-800" :
                                                    day.data.percentage < 40 ? "bg-emerald-900" :
                                                        day.data.percentage < 70 ? "bg-emerald-700" :
                                                            day.data.percentage < 90 ? "bg-emerald-500" : "bg-emerald-300"
                                            )}
                                            title={`${day.date}: ${day.data?.percentage || 0}%`}
                                        />
                                    ))}
                                </div>
                            )
                        })}
                    </div>

                    {/* Month Label Overlay Logic (Refined) */}
                    <div className="absolute top-0 left-8 flex w-full pointer-events-none">
                        {/* We iterate weeks and place labels when month changes */}
                        {weeks.map((week, wIdx) => {
                            const firstDay = week[0];
                            const isNewMonth = wIdx === 0 || weeks[wIdx - 1][0].month !== firstDay.month;
                            if (isNewMonth && firstDay.inYear && firstDay.day < 14) { // Only label if early in month
                                return (
                                    <span
                                        key={wIdx}
                                        className="absolute text-xs text-slate-400 font-medium -top-6"
                                        style={{ left: `${wIdx * 16}px` }} // 12px width + 4px gap = 16px
                                    // Make interactive to go to month view
                                    >
                                        <button
                                            className="hover:text-white pointer-events-auto"
                                            onClick={() => router.push(`/progress/${year}/${String(firstDay.month + 1).padStart(2, '0')}`)}
                                        >
                                            {months[firstDay.month]}
                                        </button>
                                    </span>
                                )
                            }
                            return null;
                        })}
                    </div>
                </div>
            </div>
        );
    };

    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    return (
        <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8 animate-fadeIn">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
                        <Activity className="text-indigo-500" size={32} />
                        Progress & Analytics
                    </h1>
                    <p className="text-slate-400 mt-1">
                        Visualize your consistency and performance over time.
                    </p>
                </div>

                <div className="flex items-center gap-4 bg-slate-800/50 p-1.5 rounded-lg border border-slate-700/50">
                    <button onClick={() => setYear(y => y - 1)} className="p-2 hover:bg-slate-700 rounded-md text-slate-300 transition-colors">
                        <ChevronLeft size={20} />
                    </button>
                    <span className="text-xl font-mono font-bold text-white min-w-[80px] text-center">
                        {year}
                    </span>
                    <button onClick={() => setYear(y => y + 1)} className="p-2 hover:bg-slate-700 rounded-md text-slate-300 transition-colors">
                        <ChevronRight size={20} />
                    </button>
                    <button onClick={() => setYear(currentYear)} className="px-3 py-1.5 ml-2 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded-md font-medium transition-colors">
                        Today
                    </button>
                </div>
            </header>

            {/* Annual Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2 bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                    <h3 className="text-lg font-bold text-white mb-6">Annual Consistency</h3>
                    <div className="h-[200px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={data?.monthly_averages}>
                                <XAxis
                                    dataKey="month"
                                    tickFormatter={(m) => new Date(0, m - 1).toLocaleString('default', { month: 'short' })}
                                    stroke="#475569"
                                    fontSize={12}
                                />
                                <YAxis stroke="#475569" fontSize={12} unit="%" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                    cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                                />
                                <Bar dataKey="percentage" radius={[4, 4, 0, 0]}>
                                    {data?.monthly_averages.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.percentage >= 80 ? '#10b981' : entry.percentage >= 50 ? '#6366f1' : '#f59e0b'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 flex flex-col justify-center items-center">
                    <div className="w-40 h-40 rounded-full border-8 border-slate-800 flex flex-col items-center justify-center relative mb-4">
                        <div className="absolute inset-0 rounded-full border-8 border-indigo-500 opacity-20"></div>
                        <div
                            className="absolute inset-0 rounded-full border-8 border-t-indigo-500 border-r-indigo-500 border-b-transparent border-l-transparent rotate-45"
                            style={{
                                transform: `rotate(${(data?.average || 0) * 3.6}deg)`,
                                transition: 'transform 1s ease-out'
                            }}
                        ></div>
                        <span className="text-4xl font-bold text-white">{data?.average || 0}%</span>
                        <span className="text-xs text-slate-400 uppercase tracking-wider font-medium mt-1">Avg Score</span>
                    </div>
                    <p className="text-slate-400 text-center text-sm">
                        Overall completion rate for {year}. <br />
                        <span className="text-indigo-400">Keep slightly pushing your limits.</span>
                    </p>
                </div>
            </div>

            {/* Detailed Heatmap Grid */}
            <div>
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <Calendar size={20} className="text-slate-400" />
                    Daily Breakdown
                </h3>
                {loading ? (
                    <div className="h-64 flex items-center justify-center text-slate-500">Loading heatmap...</div>
                ) : renderHeatmap()}
            </div>
        </div>
    );
};

export default YearView;
