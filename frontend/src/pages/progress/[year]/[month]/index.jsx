import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import progressService from '../../../../services/progressService';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, ArrowLeft } from 'lucide-react';
import clsx from 'clsx';
import Link from 'next/link';

const MonthView = () => {
    const router = useRouter();
    const { year, month } = router.query;
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!year || !month) return;

        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await progressService.getMonthProgress(year, month);
                setData(result);
            } catch (error) {
                console.error("Failed to load month progress", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [year, month]);

    if (loading) return <div className="p-8 text-center text-slate-500">Loading calendar...</div>;

    // Calendar Grid Logic
    // We need to know which day of the week the 1st starts on to add padding
    const dateObj = new Date(year, month - 1, 1);
    const startDay = dateObj.getDay(); // 0 = Sunday
    const daysInMonth = new Date(year, month, 0).getDate();

    // Create array of days
    const days = data?.days || [];
    const dayMap = {};
    days.forEach(d => dayMap[d.date] = d);

    const renderCalendar = () => {
        // Aligned with the "Dots" design from user image
        // Grid of 7 columns (days of week)

        const blanks = Array.from({ length: startDay }, (_, i) => <div key={`blank-${i}`}></div>);

        const dayCells = Array.from({ length: daysInMonth }, (_, i) => {
            const dayNum = i + 1;
            const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`;
            const dayData = dayMap[dateStr];

            return (
                <Link
                    key={dayNum}
                    href={`/progress/${year}/${month}/${String(dayNum).padStart(2, '0')}`}
                    className="flex flex-col items-center justify-center p-2 group"
                >
                    <div className={clsx(
                        "w-12 h-12 md:w-16 md:h-16 rounded-full flex items-center justify-center text-sm font-bold transition-all relative",
                        dayData && dayData.percentage > 0
                            ? (dayData.percentage >= 80 ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/30 ring-2 ring-indigo-400" :
                                dayData.percentage >= 50 ? "bg-indigo-900/80 text-indigo-300 ring-1 ring-indigo-700" :
                                    "bg-indigo-900/40 text-indigo-500/70")
                            : "bg-slate-800/50 text-slate-600 hover:bg-slate-800"
                    )}>
                        {dayNum}

                        {/* Percentage Badge */}
                        {dayData && dayData.percentage > 0 && (
                            <span className={clsx(
                                "absolute -top-1 -right-1 w-5 h-5 flex items-center justify-center rounded-full text-[10px] bg-slate-900 border border-slate-700",
                                dayData.percentage >= 80 ? "text-emerald-400" : "text-slate-400"
                            )}>
                                {dayData.percentage}
                            </span>
                        )}
                    </div>
                </Link>
            );
        });

        return [...blanks, ...dayCells];
    };

    return (
        <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6 animate-fadeIn">
            <header className="flex items-center gap-4">
                <Link href="/progress" className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
                    <ArrowLeft size={24} />
                </Link>
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
                        {new Date(year, month - 1).toLocaleString('default', { month: 'long' })} {year}
                    </h1>
                    <p className="text-slate-400 text-sm">Monthly Average: <span className="text-white font-bold">{data?.average}%</span></p>
                </div>
            </header>

            <div className="grid grid-cols-7 gap-4">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                    <div key={day} className="text-center text-slate-500 font-medium uppercase text-xs py-2 tracking-wider">
                        {day}
                    </div>
                ))}
                {renderCalendar()}
            </div>
        </div>
    );
};

export default MonthView;
