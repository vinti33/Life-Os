import { useRouter } from 'next/router';
import { useUser } from '../store/userStore';
import { useChat } from '../store/chatStore';
import { useState, useRef, useEffect } from 'react';
import ChatBubble from './ChatBubble';
import { LayoutDashboard, MessageSquare, Calendar, Settings, LogOut, Sparkles, X, Send, Activity } from 'lucide-react';
import { usePlan } from '../store/planStore';
import { taskService } from '../services/taskService';

import api from '../utils/apiUtils';

const FONT = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif";

export default function MainLayout({ children }) {
    const { user, logout } = useUser();
    const { messages, loading, sendMessage, addLocalMessage } = useChat();
    const { fetchActivePlan } = usePlan();
    const [input, setInput] = useState('');
    const [isFloatingChatOpen, setFloatingChatOpen] = useState(false);
    const router = useRouter();
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages, isFloatingChatOpen]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;
        const content = input;
        setInput('');
        await sendMessage(content);
    };

    const handleAction = async (action) => {
        // Optimistic UI update or just a toast
        // await sendMessage(`🔄 Processing ${action.label}...`); 
        // User requested NO "Processing Button Label..." message that hangs.
        // We will just show a loading state or a toast if we had one.
        // For now, let's just call the API and let the backend response drive the next message.

        try {
            const response = await api.post('/chat/action', {
                action: {
                    type: action.type,
                    payload: action.payload
                }
            });

            if (response.data.success) {
                await fetchActivePlan(); // Refresh data
                // Show success message from backend as an Assistant message
                addLocalMessage('assistant', `✅ ${response.data.message}`);
            } else {
                addLocalMessage('assistant', `❌ ${response.data.message}`);
            }

        } catch (error) {
            console.error(error);
            const errorMsg = error.response?.data?.detail || error.message;
            addLocalMessage('assistant', `❌ Action failed: ${errorMsg}`);
        }
    };

    const navItems = [
        { label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={18} /> },
        { label: 'Schedule', path: '/today-tasks', icon: <Calendar size={18} /> },
        { label: 'Progress', path: '/progress', icon: <Activity size={18} /> },
        { label: 'Chat', path: '/chat', icon: <MessageSquare size={18} /> },
        { label: 'Profile', path: '/question-sheet', icon: <Settings size={18} /> },
    ];

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #020617 0%, #0f172a 50%, #020617 100%)',
            color: '#e2e8f0',
            fontFamily: FONT,
            position: 'relative',
            overflow: 'hidden',
        }}>
            {/* Background orbs */}
            <div style={{
                position: 'fixed', top: '10%', left: '-5%', width: '500px', height: '500px',
                background: 'radial-gradient(circle, rgba(99, 102, 241, 0.07) 0%, transparent 70%)',
                borderRadius: '50%', filter: 'blur(80px)', pointerEvents: 'none', zIndex: 0,
            }} />
            <div style={{
                position: 'fixed', bottom: '10%', right: '-5%', width: '400px', height: '400px',
                background: 'radial-gradient(circle, rgba(168, 85, 247, 0.06) 0%, transparent 70%)',
                borderRadius: '50%', filter: 'blur(80px)', pointerEvents: 'none', zIndex: 0,
            }} />

            {/* Top Navigation */}
            <header style={{
                position: 'sticky',
                top: 0,
                zIndex: 40,
                background: 'rgba(2, 6, 23, 0.85)',
                backdropFilter: 'blur(24px) saturate(180%)',
                WebkitBackdropFilter: 'blur(24px) saturate(180%)',
                borderBottom: '1px solid rgba(255,255,255,0.06)',
            }}>
                <div style={{
                    maxWidth: '1200px',
                    margin: '0 auto',
                    padding: '0 24px',
                    height: '64px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
                        <h1
                            onClick={() => router.push('/dashboard')}
                            style={{
                                fontSize: '20px', fontWeight: 900, cursor: 'pointer',
                                margin: 0, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center',
                            }}
                        >
                            <span style={{
                                background: 'linear-gradient(135deg, #818cf8, #c084fc)',
                                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                            }}>Life</span>
                            <span style={{ color: '#f8fafc' }}>OS</span>
                        </h1>

                        <nav style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            {navItems.map(item => {
                                const active = router.pathname === item.path;
                                return (
                                    <button
                                        key={item.path}
                                        onClick={() => router.push(item.path)}
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: '6px',
                                            padding: '8px 16px',
                                            borderRadius: '10px',
                                            border: 'none',
                                            background: active ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                                            color: active ? '#818cf8' : '#64748b',
                                            fontSize: '14px',
                                            fontWeight: 600,
                                            fontFamily: FONT,
                                            cursor: 'pointer',
                                            transition: 'all 0.2s ease',
                                            position: 'relative',
                                        }}
                                        onMouseEnter={(e) => { if (!active) { e.target.style.color = '#94a3b8'; e.target.style.background = 'rgba(255,255,255,0.04)'; } }}
                                        onMouseLeave={(e) => { if (!active) { e.target.style.color = '#64748b'; e.target.style.background = 'transparent'; } }}
                                    >
                                        {item.label}
                                    </button>
                                );
                            })}
                        </nav>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        {user && (
                            <span style={{ fontSize: '13px', color: '#475569', fontWeight: 500 }}>
                                {user.name}
                            </span>
                        )}
                        <button
                            onClick={logout}
                            style={{
                                padding: '8px', background: 'none', border: 'none',
                                color: '#475569', cursor: 'pointer', borderRadius: '8px',
                                transition: 'all 0.2s', display: 'flex', alignItems: 'center',
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.color = '#f87171'; e.currentTarget.style.background = 'rgba(239,68,68,0.08)'; }}
                            onMouseLeave={(e) => { e.currentTarget.style.color = '#475569'; e.currentTarget.style.background = 'none'; }}
                        >
                            <LogOut size={18} />
                        </button>
                    </div>
                </div>
                {/* Gradient accent line */}
                <div style={{
                    height: '1px',
                    background: 'linear-gradient(90deg, transparent, rgba(99,102,241,0.3), rgba(168,85,247,0.2), transparent)',
                }} />
            </header>

            {/* Main Content */}
            <main style={{
                maxWidth: '1100px',
                width: '100%',
                margin: '0 auto',
                padding: '32px 24px 80px',
                position: 'relative',
                zIndex: 1,
            }}>
                {children}
            </main>

            {/* Floating AI Button */}
            {!isFloatingChatOpen && (
                <button
                    onClick={() => setFloatingChatOpen(true)}
                    style={{
                        position: 'fixed', bottom: '24px', right: '24px', zIndex: 50,
                        width: '56px', height: '56px', borderRadius: '18px',
                        background: 'linear-gradient(135deg, #6366f1, #7c3aed)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        boxShadow: '0 6px 30px rgba(99,102,241,0.35)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#fff', cursor: 'pointer',
                        transition: 'all 0.3s ease',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.1)'; e.currentTarget.style.boxShadow = '0 8px 40px rgba(99,102,241,0.5)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 6px 30px rgba(99,102,241,0.35)'; }}
                >
                    <Sparkles size={22} />
                </button>
            )}

            {/* Floating Chat Modal */}
            {isFloatingChatOpen && (
                <div style={{ position: 'fixed', inset: 0, zIndex: 60, display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-end', padding: '24px' }}>
                    <div
                        onClick={() => setFloatingChatOpen(false)}
                        style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}
                    />
                    <div style={{
                        position: 'relative',
                        width: '400px', height: '520px',
                        background: 'rgba(15, 23, 42, 0.9)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255,255,255,0.08)',
                        borderRadius: '20px',
                        display: 'flex', flexDirection: 'column',
                        boxShadow: '0 25px 60px rgba(0,0,0,0.6)',
                        overflow: 'hidden',
                        animation: 'fadeInUp 0.3s ease-out',
                    }}>
                        {/* Chat Header */}
                        <div style={{
                            padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            borderBottom: '1px solid rgba(255,255,255,0.06)',
                            background: 'rgba(99,102,241,0.04)',
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <div style={{
                                    width: '28px', height: '28px', borderRadius: '50%',
                                    background: 'linear-gradient(135deg, rgba(99,102,241,0.3), rgba(168,85,247,0.2))',
                                    border: '1px solid rgba(99,102,241,0.3)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>
                                    <Sparkles size={13} color="#a5b4fc" />
                                </div>
                                <span style={{
                                    fontSize: '14px', fontWeight: 800,
                                    background: 'linear-gradient(135deg, #818cf8, #c084fc)',
                                    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                                }}>LifeOS AI</span>
                            </div>
                            <button
                                onClick={() => setFloatingChatOpen(false)}
                                style={{
                                    background: 'none', border: 'none', color: '#64748b',
                                    cursor: 'pointer', padding: '4px', borderRadius: '6px',
                                    transition: 'all 0.2s', display: 'flex',
                                }}
                                onMouseEnter={(e) => { e.currentTarget.style.color = '#f8fafc'; e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
                                onMouseLeave={(e) => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'none'; }}
                            >
                                <X size={18} />
                            </button>
                        </div>

                        {/* Messages */}
                        <div style={{ flex: 1, overflowY: 'auto', padding: '16px', background: 'rgba(2,6,23,0.3)' }}>
                            {messages.map((msg, i) => (
                                <ChatBubble key={i} message={msg} onAction={handleAction} />
                            ))}
                            {loading && (
                                <div style={{ display: 'flex', gap: '6px', padding: '12px', background: 'rgba(15,23,42,0.6)', borderRadius: '12px', width: 'fit-content' }}>
                                    {[0, 1, 2].map(i => (
                                        <div key={i} style={{
                                            width: '8px', height: '8px', background: '#6366f1',
                                            borderRadius: '50%', animation: `bounce 1.4s ease-in-out ${i * 0.16}s infinite`,
                                        }} />
                                    ))}
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input */}
                        <form onSubmit={handleSend} style={{
                            padding: '12px 16px',
                            borderTop: '1px solid rgba(255,255,255,0.06)',
                            background: 'rgba(2,6,23,0.5)',
                        }}>
                            <div style={{
                                display: 'flex', alignItems: 'center', gap: '8px',
                                background: 'rgba(15,23,42,0.5)',
                                border: '1px solid rgba(255,255,255,0.08)',
                                borderRadius: '12px', padding: '4px 12px',
                            }}>
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Ask anything..."
                                    style={{
                                        flex: 1, background: 'transparent', border: 'none', outline: 'none',
                                        padding: '8px 0', fontSize: '14px', color: '#e2e8f0', fontFamily: FONT,
                                    }}
                                />
                                <button
                                    type="submit"
                                    disabled={loading || !input.trim()}
                                    style={{
                                        padding: '6px', background: 'none', border: 'none',
                                        color: input.trim() ? '#818cf8' : '#334155',
                                        cursor: input.trim() ? 'pointer' : 'not-allowed',
                                        display: 'flex', transition: 'color 0.2s',
                                    }}
                                >
                                    <Send size={16} />
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <style jsx global>{`
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                @keyframes bounce {
                    0%, 80%, 100% { transform: scale(0); }
                    40% { transform: scale(1); }
                }
            `}</style>
        </div>
    );
}
