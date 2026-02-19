import { Sparkles, User, Clock, HelpCircle } from 'lucide-react';
import { useState } from 'react';

const FONT = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif";

export default function ChatBubble({ message, onAction }) {
    const isAI = message.role === 'assistant';
    const [hovered, setHovered] = useState(false);

    return (
        <div
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: isAI ? 'flex-start' : 'flex-end',
                marginBottom: '24px',
                animation: 'fadeInUp 0.3s ease-out',
                position: 'relative',
            }}
        >
            {/* Avatar + Label */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '6px',
                padding: '0 4px',
                flexDirection: isAI ? 'row' : 'row-reverse',
            }}>
                <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: isAI
                        ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.15))'
                        : 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    boxShadow: isAI ? '0 0 12px rgba(99, 102, 241, 0.2)' : 'none',
                }}>
                    {isAI ? <Sparkles size={14} color="#a5b4fc" /> : <User size={14} color="#94a3b8" />}
                </div>
                <span style={{
                    fontSize: '10px',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    color: '#475569',
                }}>
                    {isAI ? 'LifeOS' : 'You'}
                </span>
            </div>

            {/* Bubble */}
            <div style={{
                maxWidth: '85%',
                padding: '16px 20px',
                borderRadius: isAI ? '20px 20px 20px 4px' : '20px 20px 4px 20px',
                background: isAI
                    ? 'rgba(15, 23, 42, 0.6)'
                    : 'linear-gradient(135deg, #6366f1, #7c3aed)',
                backdropFilter: isAI ? 'blur(12px)' : 'none',
                WebkitBackdropFilter: isAI ? 'blur(12px)' : 'none',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: isAI ? '#e2e8f0' : '#ffffff',
                boxShadow: isAI
                    ? '0 10px 25px rgba(0, 0, 0, 0.2)'
                    : '0 8px 30px rgba(99, 102, 241, 0.3)',
                transition: 'all 0.3s ease',
            }}>
                <p style={{
                    fontSize: '14.5px',
                    lineHeight: '1.6',
                    margin: 0,
                    whiteSpace: 'pre-wrap',
                    fontWeight: 500,
                }}>{message.content}</p>

                {/* Questions */}
                {isAI && message.questions?.length > 0 && (
                    <div style={{
                        marginTop: '16px',
                        paddingTop: '16px',
                        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px',
                    }}>
                        {message.questions.map((q, i) => (
                            <div key={i} style={{
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '10px',
                                background: 'rgba(99, 102, 241, 0.08)',
                                border: '1px solid rgba(99, 102, 241, 0.15)',
                                padding: '10px 14px',
                                borderRadius: '14px',
                            }}>
                                <HelpCircle size={14} color="#818cf8" style={{ marginTop: '2px', flexShrink: 0 }} />
                                <span style={{ fontSize: '12px', color: '#a5b4fc', lineHeight: '1.5', fontWeight: 500 }}>
                                    {typeof q === 'object' ? (q.question || JSON.stringify(q)) : q}
                                </span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Actions */}
                {isAI && message.actions?.length > 0 && (
                    <div style={{
                        marginTop: '16px',
                        paddingTop: '16px',
                        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '10px',
                    }}>
                        {message.actions.map((action, i) => (
                            <ChatAction key={i} action={action} onClick={() => onAction && onAction(action)} />
                        ))}
                    </div>
                )}
            </div>

            {/* Timestamp */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                marginTop: '6px',
                fontSize: '10px',
                fontFamily: "'JetBrains Mono', monospace",
                color: '#334155',
                opacity: hovered ? 1 : 0,
                transition: 'opacity 0.2s ease',
                padding: '0 4px',
            }}>
                <Clock size={10} />
                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
        </div>
    );
}

function ChatAction({ action, onClick }) {
    const [hovered, setHovered] = useState(false);

    const handleClick = (e) => {
        console.log("ChatAction clicked:", action);
        if (onClick) {
            onClick(e);
        } else {
            console.warn("ChatAction clicked but no onClick handler provided");
        }
    };

    return (
        <button
            onClick={handleClick}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            style={{
                background: hovered ? 'rgba(99, 102, 241, 0.2)' : 'rgba(99, 102, 241, 0.1)',
                border: hovered ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid rgba(99, 102, 241, 0.15)',
                color: hovered ? '#fff' : '#a5b4fc',
                padding: '8px 16px',
                borderRadius: '50px',
                fontSize: '11px',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                cursor: 'pointer',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                fontFamily: FONT,
                transform: hovered ? 'scale(1.04)' : 'none',
                boxShadow: hovered ? '0 4px 12px rgba(99, 102, 241, 0.2)' : 'none',
            }}
        >
            {action.label}
        </button>
    );
}
