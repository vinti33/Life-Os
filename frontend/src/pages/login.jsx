import { useState } from 'react';
import { useRouter } from 'next/router';
import { useUser } from '../store/userStore';
import { Sparkles, Mail, Lock, User as UserIcon, Loader2 } from 'lucide-react';
import { getErrorMessage } from '../utils/apiUtils';

export default function Login() {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login, signup } = useUser();
    const router = useRouter();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            if (isLogin) {
                await login(email, password);
            } else {
                await signup(name, email, password);
            }
            router.push('/dashboard');
        } catch (err) {
            setError(getErrorMessage(err, 'Authentication failed. Please try again.'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div
            style={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #020617 0%, #0f172a 50%, #020617 100%)',
                fontFamily: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
                padding: '24px',
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            {/* Background orbs */}
            <div style={{
                position: 'absolute',
                top: '15%',
                left: '-10%',
                width: '500px',
                height: '500px',
                background: 'radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, transparent 70%)',
                borderRadius: '50%',
                filter: 'blur(60px)',
                animation: 'float 8s ease-in-out infinite',
                pointerEvents: 'none',
            }} />
            <div style={{
                position: 'absolute',
                bottom: '10%',
                right: '-10%',
                width: '400px',
                height: '400px',
                background: 'radial-gradient(circle, rgba(168, 85, 247, 0.1) 0%, transparent 70%)',
                borderRadius: '50%',
                filter: 'blur(60px)',
                animation: 'float 10s ease-in-out infinite reverse',
                pointerEvents: 'none',
            }} />

            <div style={{
                width: '100%',
                maxWidth: '420px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '32px',
                position: 'relative',
                zIndex: 1,
                animation: 'fadeInUp 0.6s ease-out forwards',
            }}>
                {/* Brand */}
                <div style={{ textAlign: 'center' }}>
                    <div style={{
                        width: '64px',
                        height: '64px',
                        margin: '0 auto 20px',
                        borderRadius: '18px',
                        background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 8px 40px rgba(99, 102, 241, 0.35)',
                    }}>
                        <Sparkles size={30} color="#fff" />
                    </div>
                    <h1 style={{
                        fontSize: '36px',
                        fontWeight: 900,
                        letterSpacing: '-0.03em',
                        margin: 0,
                        lineHeight: 1.1,
                    }}>
                        <span style={{
                            background: 'linear-gradient(135deg, #818cf8, #c084fc)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                        }}>Life</span>
                        <span style={{ color: '#f8fafc' }}>OS</span>
                    </h1>
                    <p style={{
                        fontSize: '14px',
                        color: '#64748b',
                        marginTop: '8px',
                        fontWeight: 500,
                        letterSpacing: '0.01em',
                    }}>
                        Your AI-powered life operating system
                    </p>
                </div>

                {/* Card */}
                <div style={{
                    width: '100%',
                    background: 'rgba(15, 23, 42, 0.6)',
                    backdropFilter: 'blur(20px) saturate(180%)',
                    WebkitBackdropFilter: 'blur(20px) saturate(180%)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '24px',
                    padding: '40px 32px',
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.04)',
                }}>
                    <h2 style={{
                        fontSize: '22px',
                        fontWeight: 700,
                        color: '#e2e8f0',
                        textAlign: 'center',
                        marginBottom: '28px',
                        letterSpacing: '-0.02em',
                    }}>
                        {isLogin ? 'Welcome back' : 'Create your account'}
                    </h2>

                    {error && (
                        <div style={{
                            background: 'rgba(239, 68, 68, 0.1)',
                            border: '1px solid rgba(239, 68, 68, 0.2)',
                            borderRadius: '12px',
                            padding: '12px 16px',
                            marginBottom: '20px',
                            fontSize: '13px',
                            color: '#fca5a5',
                            textAlign: 'center',
                        }}>
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        {!isLogin && (
                            <FormField
                                label="Full Name"
                                icon={<UserIcon size={16} color="#475569" />}
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="John Doe"
                                required={!isLogin}
                            />
                        )}

                        <FormField
                            label="Email Address"
                            icon={<Mail size={16} color="#475569" />}
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                            required
                        />

                        <FormField
                            label="Password"
                            icon={<Lock size={16} color="#475569" />}
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                        />

                        <button
                            type="submit"
                            disabled={loading}
                            style={{
                                width: '100%',
                                padding: '14px',
                                marginTop: '4px',
                                borderRadius: '14px',
                                border: 'none',
                                background: loading ? '#334155' : 'linear-gradient(135deg, #6366f1, #7c3aed)',
                                color: '#fff',
                                fontSize: '15px',
                                fontWeight: 700,
                                fontFamily: 'inherit',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                transition: 'all 0.25s ease',
                                boxShadow: loading ? 'none' : '0 4px 20px rgba(99, 102, 241, 0.3)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                letterSpacing: '0.01em',
                            }}
                            onMouseEnter={(e) => {
                                if (!loading) {
                                    e.target.style.boxShadow = '0 6px 30px rgba(99, 102, 241, 0.45)';
                                    e.target.style.transform = 'translateY(-1px)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.boxShadow = loading ? 'none' : '0 4px 20px rgba(99, 102, 241, 0.3)';
                                e.target.style.transform = 'translateY(0)';
                            }}
                        >
                            {loading && <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />}
                            {isLogin ? 'Sign In' : 'Create Account'}
                        </button>
                    </form>

                    <div style={{ textAlign: 'center', marginTop: '24px' }}>
                        <button
                            onClick={() => { setIsLogin(!isLogin); setError(''); }}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: '#818cf8',
                                fontSize: '14px',
                                fontWeight: 500,
                                cursor: 'pointer',
                                fontFamily: 'inherit',
                                transition: 'color 0.2s',
                            }}
                            onMouseEnter={(e) => e.target.style.color = '#a5b4fc'}
                            onMouseLeave={(e) => e.target.style.color = '#818cf8'}
                        >
                            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
                        </button>
                    </div>
                </div>

                {/* Footer */}
                <p style={{
                    fontSize: '12px',
                    color: '#334155',
                    textAlign: 'center',
                    fontWeight: 500,
                }}>
                    Powered by AI • Built for you
                </p>
            </div>

            <style jsx global>{`
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                @keyframes float {
                    0%, 100% { transform: translateY(0px); }
                    50% { transform: translateY(-20px); }
                }

                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}

function FormField({ label, icon, type, value, onChange, placeholder, required }) {
    const [focused, setFocused] = useState(false);

    return (
        <div>
            <label style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: 600,
                color: '#94a3b8',
                marginBottom: '8px',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
            }}>
                {label}
            </label>
            <div style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
            }}>
                <div style={{
                    position: 'absolute',
                    left: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    pointerEvents: 'none',
                    transition: 'color 0.2s',
                }}>
                    {icon}
                </div>
                <input
                    type={type}
                    value={value}
                    onChange={onChange}
                    onFocus={() => setFocused(true)}
                    onBlur={() => setFocused(false)}
                    placeholder={placeholder}
                    required={required}
                    style={{
                        width: '100%',
                        padding: '13px 16px 13px 42px',
                        borderRadius: '12px',
                        border: focused
                            ? '1.5px solid rgba(99, 102, 241, 0.5)'
                            : '1px solid rgba(255, 255, 255, 0.08)',
                        background: 'rgba(15, 23, 42, 0.5)',
                        color: '#e2e8f0',
                        fontSize: '15px',
                        fontFamily: 'inherit',
                        fontWeight: 500,
                        outline: 'none',
                        transition: 'all 0.2s ease',
                        boxShadow: focused
                            ? '0 0 0 3px rgba(99, 102, 241, 0.1)'
                            : 'none',
                    }}
                />
            </div>
        </div>
    );
}
