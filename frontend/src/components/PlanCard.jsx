import Button from './Button';
import { Sparkles, CheckCircle2, XCircle, Clock, Info, ListChecks } from 'lucide-react';

export default function PlanCard({ plan, onApprove, onReject }) {
    if (!plan) return null;

    const taskCount = plan.tasks?.length || 0;

    return (
        <div className="glass-card overflow-hidden border-l-4 border-l-indigo-500 animate-slide-up">
            <div className="p-8 space-y-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start gap-6">
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2 text-indigo-400 text-[10px] font-black uppercase tracking-[0.2em]">
                                <Sparkles size={14} />
                                AI Strategy Proposal
                            </div>
                            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20">
                                <ListChecks size={12} className="text-indigo-400" />
                                <span className="text-[10px] font-bold text-indigo-300">{taskCount} tasks</span>
                            </div>
                        </div>
                        <h2 className="text-2xl font-black text-white">Daily Protocol Draft</h2>
                        <p className="text-slate-400 text-sm leading-relaxed max-w-xl">{plan.summary}</p>
                    </div>
                    <div className="flex gap-3 w-full md:w-auto shrink-0">
                        <Button variant="ghost" onClick={onReject} className="flex-1 md:flex-none">
                            <XCircle size={16} className="mr-1.5" /> Reject
                        </Button>
                        <Button variant="primary" onClick={onApprove} className="flex-1 md:flex-none">
                            <CheckCircle2 size={16} className="mr-1.5" /> Approve
                        </Button>
                    </div>
                </div>

                {/* Timeline */}
                <div className="space-y-3">
                    <h3 className="text-[10px] font-black uppercase text-slate-500 tracking-[0.2em] mb-4">Operations Timeline</h3>
                    <div className="grid grid-cols-1 gap-2">
                        {plan.tasks?.map((task, i) => (
                            <div
                                key={i}
                                className="flex items-center gap-4 text-sm text-slate-300 p-4 bg-white/[0.03] rounded-xl border border-white/5 transition-all hover:bg-white/[0.06] hover:border-white/10 animate-fade-in"
                                style={{ animationDelay: `${i * 60}ms` }}
                            >
                                {/* Timeline dot */}
                                <div className="w-2 h-2 rounded-full bg-indigo-500/60 shrink-0 ring-2 ring-indigo-500/20" />
                                <span className="font-mono text-indigo-400 font-semibold bg-indigo-500/10 px-3 py-1 rounded-lg text-xs whitespace-nowrap">
                                    {task.start_time} — {task.end_time}
                                </span>
                                <span className="flex-1 font-medium truncate">{task.title}</span>
                                <span className="text-[9px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full bg-white/5 border border-white/5 text-slate-500 shrink-0">
                                    {task.category}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Clarification Questions */}
                {plan.clarification_questions?.length > 0 && (
                    <div className="bg-amber-500/5 border border-amber-500/10 p-5 rounded-2xl flex gap-4 animate-fade-in delay-300">
                        <Info className="text-amber-500 shrink-0 mt-0.5" size={18} />
                        <div>
                            <p className="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-2">Needs Clarification</p>
                            {plan.clarification_questions.map((q, i) => (
                                <p key={i} className="text-sm text-amber-200/80 mb-1">• {typeof q === 'object' ? (q.question || JSON.stringify(q)) : q}</p>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
