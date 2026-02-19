import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useChat } from '../store/chatStore';
import { usePlan } from '../store/planStore';
import ChatBubble from '../components/ChatBubble';
import MainLayout from '../components/MainLayout';
import ErrorBoundary from '../components/ErrorBoundary'; // Import ErrorBoundary
import { taskService } from '../services/taskService';
import { planService } from '../services/planService';
import { Sparkles, Send, Plus, MessageSquare, ArrowLeft, Loader2, Trash2 } from 'lucide-react';
import api from '../utils/apiUtils';

const FONT = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif";

export default function Chat() {
    const [input, setInput] = useState('');
    const [backHovered, setBackHovered] = useState(false);
    const { messages, loading, sendMessage, addLocalMessage, sessions, loadSessions, loadSession, startNewSession, currentSessionId } = useChat();
    // const [messages, setMessages] = useState([]); // Local state test

    // const addLocalMessage = (role, content) => {
    //    setMessages(prev => [...prev, { role, content, timestamp: new Date() }]);
    // };
    const { fetchActivePlan } = usePlan();
    const router = useRouter();
    const messagesEndRef = useRef(null);

    useEffect(() => {
        loadSessions();
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;
        const content = input;
        setInput('');
        await sendMessage(content);
        if (!currentSessionId) loadSessions();
    };

    const handleAction = async (action) => {
        if (!action) return;
        const actionLabel = action.label || action.type || 'request';
        console.log(`[${new Date().toISOString()}] Button clicked:`, actionLabel);

        try {
            addLocalMessage('user', `🔄 Processing ${actionLabel}...`);

            if (action.type === 'reschedule' || action.type === 'UPDATE_TASK') {
                console.log("Calling taskService.reschedule...");
                await taskService.reschedule(action.payload.task_id, action.payload.start_time, action.payload.end_time);
                console.log("taskService.reschedule done. Adding success message...");
                addLocalMessage('assistant', `✅ Rescheduled "${action.label}".`);
                console.log("Fetching active plan...");
                await fetchActivePlan();
                console.log("fetchActivePlan done.");
            } else if (action.type === 'add_task' || action.type === 'ADD_TASK') {
                console.log("Calling taskService.createTask...");
                await taskService.createTask(action.payload.title, action.payload.start_time, action.payload.end_time, action.payload.category);
                console.log("taskService.createTask done. Adding success message...");
                addLocalMessage('assistant', `✅ Added "${action.payload.title}".`);
                console.log("Fetching active plan...");
                await fetchActivePlan();
                console.log("fetchActivePlan done.");
            } else if (action.type === 'GENERATE_ROUTINE') {
                console.log("Calling planService.fetchDraft...");
                addLocalMessage('assistant', "⏳ Generating your routine, please wait...");
                try {
                    await planService.fetchDraft(action.payload.context || 'morning routine breakdown', 'daily');
                    await fetchActivePlan();
                    addLocalMessage('assistant', "✅ Routine generated! Go to your dashboard to review and approve it.");
                } catch (err) {
                    addLocalMessage('assistant', `❌ Failed to generate routine: ${err.response?.data?.detail || err.message}`);
                }
            } else if (action.type === 'EDIT_PLAN') {
                console.log("Calling EDIT_PLAN action...");
                addLocalMessage('assistant', "⏳ Updating your plan, please wait...");
                try {
                    const context = action.payload?.context || action.label || 'Modify my plan';
                    const planType = action.payload?.plan_type || 'daily';
                    await api.post('/plan/edit', { context, plan_type: planType });
                    await fetchActivePlan();
                    addLocalMessage('assistant', "✅ Plan updated! Check your dashboard to see the changes.");
                } catch (err) {
                    addLocalMessage('assistant', `❌ Failed to update plan: ${err.response?.data?.detail || err.message}`);
                }
            } else if (action.type === 'DELETE_TASK') {
                console.log("Calling DELETE_TASK action...");
                const response = await api.post('/chat/action', {
                    action: { type: 'DELETE_TASK', payload: action.payload }
                });
                if (response.data.success) {
                    addLocalMessage('assistant', `✅ Removed "${action.payload.title}".`);
                    await fetchActivePlan();
                } else {
                    addLocalMessage('assistant', `❌ Could not remove task: ${response.data.message}`);
                }
            } else if (action.type === 'ignore') {
                addLocalMessage('system', "Action cancelled.");
            }
            console.log("Processing done successfully");
        } catch (error) {
            console.error("Processing failed in handleAction:", error);
            if (error.stack) console.error(error.stack); // Log stack trace
            console.trace("Trace from catch block:");   // Explicit trace
            let errMsg = error.response?.data?.detail || error.message;
            if (typeof errMsg === 'object') errMsg = JSON.stringify(errMsg);
            addLocalMessage('assistant', `❌ Failed: ${errMsg}`);
        }
    };

    return (
        <MainLayout>
            <div style={{
                display: 'flex',
                height: 'calc(100vh - 120px)',
                background: 'rgba(15, 23, 42, 0.4)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: '24px',
                overflow: 'hidden',
                animation: 'fadeInUp 0.6s ease-out',
            }}>
                {/* Sidebar */}
                <aside style={{
                    width: '280px',
                    borderRight: '1px solid rgba(255, 255, 255, 0.06)',
                    background: 'rgba(2, 6, 23, 0.3)',
                    display: 'flex',
                    flexDirection: 'column',
                }}>
                    <div style={{ padding: '24px', borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h2 style={{
                                fontSize: '11px',
                                fontWeight: 800,
                                color: '#475569',
                                textTransform: 'uppercase',
                                letterSpacing: '0.15em',
                                margin: 0,
                            }}>Conversations</h2>
                            <button
                                onClick={startNewSession}
                                style={{
                                    background: 'rgba(99, 102, 241, 0.1)',
                                    border: '1px solid rgba(99, 102, 241, 0.2)',
                                    color: '#818cf8',
                                    padding: '6px 12px',
                                    borderRadius: '8px',
                                    fontSize: '11px',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '6px',
                                    transition: 'all 0.2s',
                                }}
                                onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
                                onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)'; e.currentTarget.style.transform = 'translateY(0)'; }}
                            >
                                <Plus size={14} /> New
                            </button>
                        </div>
                    </div>

                    <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
                        {sessions.map(s => {
                            const active = currentSessionId === s.id;
                            return (
                                <div
                                    key={s.id}
                                    onClick={() => loadSession(s.id)}
                                    style={{
                                        padding: '12px 16px',
                                        borderRadius: '12px',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '12px',
                                        marginBottom: '4px',
                                        transition: 'all 0.2s',
                                        background: active ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                                        border: active ? '1px solid rgba(99,102,241,0.15)' : '1px solid transparent',
                                    }}
                                    onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; }}
                                    onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; }}
                                >
                                    <MessageSquare size={14} color={active ? '#818cf8' : '#334155'} />
                                    <span style={{
                                        fontSize: '13.5px',
                                        fontWeight: 500,
                                        color: active ? '#e2e8f0' : '#64748b',
                                        whiteSpace: 'nowrap',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                    }}>{s.title}</span>
                                </div>
                            );
                        })}
                        {sessions.length === 0 && (
                            <div style={{ padding: '40px 20px', textAlign: 'center' }}>
                                <p style={{ fontSize: '12px', color: '#334155', fontWeight: 500 }}>No conversations yet</p>
                            </div>
                        )}
                    </div>
                </aside>

                {/* Main Chat */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
                    {/* Header */}
                    <header style={{
                        padding: '12px 24px',
                        borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
                        background: 'rgba(15, 23, 42, 0.2)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        height: '72px',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                            <button
                                onClick={() => router.push('/dashboard')}
                                onMouseEnter={() => setBackHovered(true)}
                                onMouseLeave={() => setBackHovered(false)}
                                style={{
                                    width: '38px',
                                    height: '38px',
                                    borderRadius: '11px',
                                    border: '1px solid rgba(255, 255, 255, 0.08)',
                                    background: backHovered ? 'rgba(255, 255, 255, 0.08)' : 'rgba(255, 255, 255, 0.03)',
                                    backdropFilter: 'blur(10px)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                    transform: backHovered ? 'translateX(-3px)' : 'none',
                                    color: backHovered ? '#fff' : '#64748b',
                                    boxShadow: backHovered ? '0 4px 15px rgba(0, 0, 0, 0.2)' : 'none',
                                    padding: 0,
                                    marginRight: '8px',
                                }}
                            >
                                <ArrowLeft size={18} />
                            </button>

                            <div style={{
                                width: '36px', height: '36px', borderRadius: '12px',
                                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.1))',
                                border: '1px solid rgba(99, 102, 241, 0.25)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                            }}>
                                <Sparkles size={18} color="#a5b4fc" />
                            </div>
                            <div>
                                <h1 style={{ fontSize: '16px', fontWeight: 800, color: '#f8fafc', margin: 0 }}>
                                    {currentSessionId ? sessions.find(s => s.id === currentSessionId)?.title || 'Intelligence Assistant' : 'New Strategic Session'}
                                </h1>
                                <p style={{ fontSize: '11px', color: '#475569', fontWeight: 600, margin: '2px 0 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                    Model: GPT-4o LifeOS Agent
                                </p>
                            </div>
                        </div>
                    </header>

                    {/* Messages Area */}
                    <div style={{
                        flex: 1,
                        overflowY: 'auto',
                        padding: '32px 24px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px',
                        background: 'radial-gradient(circle at 50% 50%, rgba(99, 102, 241, 0.03) 0%, transparent 100%)',
                    }}>
                        {messages.length === 0 && (
                            <div style={{
                                height: '100%', display: 'flex', flexDirection: 'column',
                                alignItems: 'center', justifyContent: 'center', textAlign: 'center',
                            }}>
                                <div style={{
                                    width: '80px', height: '80px', borderRadius: '24px',
                                    background: 'rgba(99, 102, 241, 0.06)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    marginBottom: '24px', animation: 'float 6s ease-in-out infinite',
                                    border: '1px solid rgba(99, 102, 241, 0.1)',
                                }}>
                                    <Sparkles size={36} color="rgba(99, 102, 241, 0.3)" />
                                </div>
                                <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#e2e8f0', margin: '0 0 10px' }}>
                                    LifeOS Intelligence Hub
                                </h2>
                                <p style={{ fontSize: '14px', color: '#64748b', maxWidth: '300px', margin: 0, lineHeight: 1.6 }}>
                                    I'm your tactical assistant. Ask me to modify your schedule, analyze productivity, or plan complex tasks.
                                </p>
                            </div>
                        )}

                        {messages.map((msg, i) => (
                            <ErrorBoundary key={i}>
                                <ChatBubble message={msg} onAction={handleAction} />
                            </ErrorBoundary>
                        ))}

                        {loading && (
                            <div style={{ display: 'flex', gap: '12px', padding: '16px 20px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '20px 20px 20px 4px', border: '1px solid rgba(255,255,255,0.06)', width: 'fit-content' }}>
                                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                                    {[0, 1, 2].map(i => (
                                        <div key={i} style={{
                                            width: '8px', height: '8px', background: '#6366f1',
                                            borderRadius: '50%', animation: `bounce 1.4s ease-in-out ${i * 0.16}s infinite`,
                                        }} />
                                    ))}
                                </div>
                                <span style={{ fontSize: '11px', fontWeight: 800, color: '#818cf8', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Processing</span>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div style={{
                        padding: '24px',
                        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                        background: 'rgba(15, 23, 42, 0.4)',
                    }}>
                        <form onSubmit={handleSend} style={{
                            maxWidth: '700px',
                            margin: '0 auto',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            background: 'rgba(2, 6, 23, 0.5)',
                            border: '1px solid rgba(255, 255, 255, 0.08)',
                            borderRadius: '16px',
                            padding: '6px 8px 6px 20px',
                            transition: 'all 0.2s',
                        }} onFocusCapture={(e) => e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.4)'} onBlurCapture={(e) => e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'}>
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Command your LifeOS..."
                                style={{
                                    flex: 1,
                                    background: 'transparent',
                                    border: 'none',
                                    outline: 'none',
                                    padding: '10px 0',
                                    fontSize: '14.5px',
                                    color: '#f8fafc',
                                    fontFamily: FONT,
                                    fontWeight: 500,
                                }}
                            />
                            <button
                                type="submit"
                                disabled={loading || !input.trim()}
                                style={{
                                    width: '40px',
                                    height: '40px',
                                    borderRadius: '12px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    background: input.trim() ? 'linear-gradient(135deg, #6366f1, #7c3aed)' : 'rgba(255, 255, 255, 0.03)',
                                    color: input.trim() ? '#fff' : '#334155',
                                    border: 'none',
                                    cursor: input.trim() ? 'pointer' : 'not-allowed',
                                    transition: 'all 0.2s',
                                }}
                            >
                                <Send size={18} />
                            </button>
                        </form>
                    </div>
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
                @keyframes bounce {
                    0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
                    40% { transform: scale(1); opacity: 1; }
                }
                }
            `}</style>
        </MainLayout>
    );
}
