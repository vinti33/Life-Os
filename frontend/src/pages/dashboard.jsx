import { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/router';
import { useUser } from '../store/userStore';
import { usePlan } from '../store/planStore';
import { useStats } from '../store/statsStore';
import MainLayout from '../components/MainLayout';
import { planService } from '../services/planService';
import { taskService } from '../services/taskService';
import {
    Sparkles, CalendarDays, Loader2, CheckCircle2, XCircle, Activity,
    Layers, PieChart, TrendingUp
} from 'lucide-react';
import DailyView from '../components/dashboard/DailyView';
import WeeklyView from '../components/dashboard/WeeklyView';
import MonthlyView from '../components/dashboard/MonthlyView';
import FinanceView from '../components/dashboard/FinanceView';
import StatCard from '../components/dashboard/StatCard';
import metricsService from '../services/metricsService';
import routineService from '../services/routineService';
import { Save } from 'lucide-react';

const FONT = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif";

function getGreeting() {
    const hour = new Date().getHours();
    if (hour < 6) return { text: 'Late night protocol', emoji: '🌙' };
    if (hour < 12) return { text: 'Good morning', emoji: '☀️' };
    if (hour < 17) return { text: 'Good afternoon', emoji: '🌤️' };
    if (hour < 21) return { text: 'Good evening', emoji: '🌆' };
    return { text: 'Good night', emoji: '🌙' };
}

export default function Dashboard() {
    const { user, profile } = useUser();
    const { currentPlan, tasks, fetchActivePlan, generatePlan, setTasks, error: planError, setError: setPlanError } = usePlan();
    const [isGenerating, setIsGenerating] = useState(false);
    const [activeTab, setActiveTab] = useState('daily');
    const router = useRouter();
    const greeting = getGreeting();

    const [lpi, setLpi] = useState(0);

    useEffect(() => {
        fetchActivePlan(activeTab);
        const fetchLpi = async () => {
            try {
                const data = await metricsService.getLifeOSIndex();
                setLpi(data.lifeos_index);
            } catch (e) {
                console.error("Failed to fetch LPI:", e);
            }
        };
        fetchLpi();
    }, [activeTab]);

    const handleGenerate = async () => {
        setIsGenerating(true);
        setPlanError(null);
        try {
            await generatePlan("Plan my " + activeTab, activeTab);
        } catch (e) {
            console.error("Generation failed:", e);
            // Error is handled by planStore and available via planError
        } finally {
            setIsGenerating(false);
        }
    };
    const handleApprove = async () => { await planService.approve(currentPlan.plan_id); fetchActivePlan(activeTab); };
    const handleReject = async () => { await planService.reject(currentPlan.plan_id); fetchActivePlan(activeTab); };

    const handleSaveRoutine = async () => {
        if (!currentPlan) return;
        const name = window.prompt("Enter Routine Name (e.g. 'Weekday Baseline'):", "My Routine");
        if (!name) return;

        const daysInput = window.prompt("Enter Days of Week (0=Mon, 6=Sun), comma separated:", "0,1,2,3,4");
        if (!daysInput) return;

        const days = daysInput.split(',').map(d => parseInt(d.trim())).filter(n => !isNaN(n));

        try {
            await routineService.createFromPlan(currentPlan.plan_id || currentPlan._id || currentPlan.id, name, days);
            alert("Routine saved successfully! It will be used for auto-planning on these days.");
        } catch (e) {
            console.error(e);
            alert("Failed to save routine.");
        }
    };


    // Construct the data object for the view
    const viewData = useMemo(() => {
        if (activeTab === 'daily') {
            return {
                ...currentPlan,
                tasks: tasks, // Always use fresh tasks from planStore
                plan_summary: currentPlan?.summary || currentPlan?.plan_summary || "No active plan"
            };
        }
        return currentPlan || {};
    }, [currentPlan, tasks, activeTab]);

    const isDraft = currentPlan?.status === 'draft';

    return (
        <MainLayout>
            <div style={{ maxWidth: '1200px', margin: '0 auto', animation: 'fadeInUp 0.5s ease-out' }}>
                {/* Header Section */}
                <div className="flex justify-between items-end mb-8 flex-wrap gap-4">
                    <div>
                        <p className="text-slate-400 text-sm font-medium flex items-center gap-2 mb-2">
                            <CalendarDays size={14} />
                            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                        </p>
                        <h1 className="text-3xl lg:text-4xl font-black text-slate-50 tracking-tight leading-tight">
                            {greeting.emoji} {greeting.text}, <span className="text-indigo-400">{user?.name || 'Protocol'}</span>
                        </h1>
                    </div>

                    <div className="flex gap-3">
                        {/* LPI Score Widget (Mocked for now) */}
                        <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 px-4 py-2 rounded-xl flex items-center gap-3">
                            <div className="p-2 bg-indigo-500/10 rounded-lg">
                                <Activity className="text-indigo-400" size={18} />
                            </div>
                            <div>
                                <p className="text-[10px] uppercase font-bold text-slate-500">LifeOS Index</p>
                                <p className="text-xl font-black text-white">{lpi}<span className="text-sm font-normal text-slate-500">/100</span></p>
                            </div>
                        </div>

                        <button
                            onClick={handleGenerate}
                            disabled={isGenerating}
                            className={`
                                flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all
                                ${isGenerating ? 'bg-slate-700 text-slate-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 hover:-translate-y-0.5'}
                            `}
                        >
                            {isGenerating ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
                            {isGenerating ? 'Architecting...' : 'Auto-Architect'}
                        </button>

                        {/* Save Routine Button */}
                        {viewData && activeTab === 'daily' && !isDraft && (
                            <button
                                onClick={handleSaveRoutine}
                                className="flex items-center gap-2 px-4 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors border border-slate-700 font-medium text-sm"
                                title="Save current plan as a Routine Template"
                            >
                                <Save size={18} />
                            </button>
                        )}
                    </div>
                </div>

                {/* Error Banner */}
                {planError && (
                    <div className="mb-6 p-4 rounded-xl bg-red-900/10 border border-red-500/20 flex justify-between items-center animate-in slide-in-from-top-2">
                        <div className="flex items-center gap-3 text-red-400">
                            <XCircle size={18} />
                            <div>
                                <h3 className="font-bold">Protocol Alert</h3>
                                <p className="text-xs">{planError}</p>
                            </div>
                        </div>
                        <button onClick={() => setPlanError(null)} className="text-red-400/50 hover:text-red-400 transition-colors">
                            <Loader2 size={14} className="rotate-45" />
                        </button>
                    </div>
                )}

                {/* Tab Navigation */}
                <div className="flex gap-1 mb-8 bg-slate-800/30 p-1.5 rounded-xl w-fit border border-slate-700/30">
                    {[
                        { id: 'daily', icon: Layers, label: 'Command Center' },
                        { id: 'weekly', icon: TrendingUp, label: 'Strategy Map' },
                        { id: 'monthly', icon: CalendarDays, label: 'Executive Review' },
                        { id: 'finance', icon: PieChart, label: 'CFO Dashboard' }
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`
                                flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all
                                ${activeTab === tab.id
                                    ? 'bg-indigo-500/10 text-indigo-400 shadow-sm'
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/30'}
                            `}
                        >
                            <tab.icon size={14} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Draft Action Bar */}
                {isDraft && (
                    <div className="mb-6 p-4 rounded-xl bg-indigo-900/10 border border-indigo-500/20 flex justify-between items-center animate-in slide-in-from-top-2">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-indigo-500/20 rounded-lg text-indigo-400">
                                <Sparkles size={18} />
                            </div>
                            <div>
                                <h3 className="font-bold text-indigo-100">Draft Proposed</h3>
                                <p className="text-xs text-indigo-300/80">AI has architected a new {activeTab} plan for you.</p>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button onClick={handleReject} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition-colors border border-slate-700">
                                <XCircle size={14} /> Reject
                            </button>
                            <button onClick={handleApprove} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold shadow-lg shadow-emerald-500/20 transition-all border border-emerald-500">
                                <CheckCircle2 size={14} /> Approve Protocol
                            </button>
                        </div>
                    </div>
                )}

                {/* Main Content Area */}
                <div className="min-h-[400px]">
                    {!viewData || (!currentPlan && !isGenerating) ? (
                        <div className="flex flex-col items-center justify-center py-20 text-slate-500 border border-dashed border-slate-700/50 rounded-2xl bg-slate-800/10">
                            <Layers size={48} className="mb-4 opacity-20" />
                            <p className="font-medium">No active plan for this period.</p>
                            <p className="text-sm opacity-60">Click Auto-Architect to generate one.</p>
                        </div>
                    ) : (
                        <>
                            {activeTab === 'daily' && <DailyView plan={viewData} />}
                            {activeTab === 'weekly' && <WeeklyView plan={viewData} />}
                            {activeTab === 'monthly' && <MonthlyView plan={viewData} />}
                            {activeTab === 'finance' && <FinanceView plan={viewData} />}
                        </>
                    )}
                </div>
            </div>

            {/* Global Styles for Animations if not utilizing Tailwind config fully */}
            <style jsx global>{`
                @keyframes fadeInUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
                .animate-fadeIn { animation: fadeInUp 0.4s ease-out forwards; }
            `}</style>
        </MainLayout>
    );
}

