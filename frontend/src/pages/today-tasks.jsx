import { useRouter } from 'next/router';
import { usePlan } from '../store/planStore';
import TaskCard from '../components/TaskCard';
import MainLayout from '../components/MainLayout';
import { taskService } from '../services/taskService';
import { ArrowLeft, CheckCircle2, Sparkles } from 'lucide-react';
import { useCountUp } from '../hooks/useCountUp';
import { useState } from 'react';

const FONT = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif";

export default function TodayTasks() {
    const { tasks, setTasks, currentPlan } = usePlan();
    const router = useRouter();
    const [backHovered, setBackHovered] = useState(false);

    const handleStatusUpdate = async (taskId, status) => {
        // Optimistic Update
        const previousTasks = [...tasks];
        const newTasks = tasks.map(t => {
            const tId = t.id || t._id;
            return tId === taskId ? { ...t, status } : t;
        });
        setTasks(newTasks);

        try {
            // Pass the plan date to ensure completion is recorded for this specific day
            const completionDate = currentPlan?.date || new Date().toISOString().split('T')[0];
            await taskService.updateTask(taskId, status, null, completionDate);
        } catch (error) {
            console.error("Failed to update task", error);
            setTasks(previousTasks); // Rollback
        }
    };

    const completed = tasks.filter(t => t.status === 'done').length;
    const animatedCompleted = useCountUp(completed);

    return (
        <MainLayout>
            <div style={{ maxWidth: '800px', margin: '0 auto', animation: 'fadeInUp 0.5s ease-out' }}>
                <header style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '40px',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                        {/* Premium Back Button */}
                        <button
                            onClick={() => router.back()} // Changed to navigate back
                            onMouseEnter={() => setBackHovered(true)}
                            onMouseLeave={() => setBackHovered(false)}
                            style={{
                                width: '44px',
                                height: '44px',
                                borderRadius: '14px',
                                border: '1px solid rgba(255, 255, 255, 0.08)',
                                background: backHovered ? 'rgba(255, 255, 255, 0.08)' : 'rgba(255, 255, 255, 0.03)',
                                backdropFilter: 'blur(10px)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                transform: backHovered ? 'translateX(-4px)' : 'none',
                                color: backHovered ? '#fff' : '#64748b',
                                boxShadow: backHovered ? '0 4px 20px rgba(0, 0, 0, 0.2)' : 'none',
                                padding: 0,
                            }}
                        >
                            <ArrowLeft size={20} />
                        </button>

                        <div>
                            <h1 style={{
                                fontSize: '28px',
                                fontWeight: 900,
                                margin: 0,
                                letterSpacing: '-0.02em',
                                color: '#f8fafc'
                            }}>
                                Today's <span style={{
                                    background: 'linear-gradient(135deg, #818cf8, #c084fc)',
                                    WebkitBackgroundClip: 'text',
                                    WebkitTextFillColor: 'transparent',
                                }}>Focus</span>
                            </h1>
                            {tasks.length > 0 && (
                                <p style={{
                                    fontSize: '13px',
                                    color: '#64748b',
                                    marginTop: '4px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '6px',
                                    fontWeight: 500,
                                }}>
                                    <CheckCircle2 size={14} color="#34d399" />
                                    {animatedCompleted}/{tasks.length} tasks completed
                                </p>
                            )}
                        </div>
                    </div>
                </header>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {tasks.length > 0 ? (
                        tasks.map((task, i) => (
                            <div key={task.id || task._id || i} style={{
                                animation: 'fadeInUp 0.4s ease-out both',
                                animationDelay: `${i * 0.06}s`
                            }}>
                                <TaskCard task={task} onStatusUpdate={handleStatusUpdate} />
                            </div>
                        ))
                    ) : (
                        <div style={{
                            padding: '80px 40px',
                            textAlign: 'center',
                            borderRadius: '24px',
                            background: 'linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01))',
                            border: '1px dashed rgba(255,255,255,0.06)',
                        }}>
                            <div style={{
                                width: '64px',
                                height: '64px',
                                margin: '0 auto 20px',
                                borderRadius: '20px',
                                background: 'rgba(99,102,241,0.08)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                animation: 'float 6s ease-in-out infinite',
                            }}>
                                <Sparkles size={30} color="rgba(99,102,241,0.35)" />
                            </div>
                            <p style={{ fontSize: '16px', color: '#94a3b8', fontWeight: 600, margin: '0 0 6px' }}>No active tasks</p>
                            <p style={{ fontSize: '14px', color: '#475569', margin: 0 }}>Go to the dashboard to generate your mission for today.</p>
                        </div>
                    )}
                </div>
            </div>

            <style jsx global>{`
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(16px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                @keyframes float {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-12px); }
                }
            `}</style>
        </MainLayout>
    );
}
