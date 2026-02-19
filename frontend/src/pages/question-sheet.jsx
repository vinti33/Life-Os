import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useUser } from '../store/userStore';
import { profileService } from '../services/authService';
import MainLayout from '../components/MainLayout';
import {
    ArrowLeft, Clock, Sun, Moon, Briefcase, Activity, BookOpen,
    DollarSign, Shield, Save, Target, Zap, Loader2, Sparkles, User
} from 'lucide-react';

const FONT = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif";

export default function QuestionSheet() {
    const { profile, fetchUser } = useUser();
    const [formData, setFormData] = useState({
        work_start_time: '09:00',
        work_end_time: '18:00',
        sleep_time: '23:00',
        wake_time: '07:00',
        energy_levels: 'High in morning',
        health_goals: '',
        learning_goals: '',
        finance_goals: '',
        role: 'Working',
        constraints: '',
    });
    const [saving, setSaving] = useState(false);
    const [backHovered, setBackHovered] = useState(false);
    const router = useRouter();

    useEffect(() => {
        if (profile) {
            setFormData(prev => ({ ...prev, ...profile }));
        }
    }, [profile]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            await profileService.updateProfile(formData);
            await fetchUser();
            router.push('/dashboard');
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    return (
        <MainLayout>
            <div style={{ maxWidth: '800px', margin: '0 auto', animation: 'fadeInUp 0.6s ease-out' }}>
                {/* Header */}
                <header style={{ marginBottom: '40px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '24px' }}>
                        <button
                            onClick={() => router.back()}
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
                                padding: 0,
                            }}
                        >
                            <ArrowLeft size={20} />
                        </button>
                        <div>
                            <h1 style={{ fontSize: '32px', fontWeight: 900, margin: 0, letterSpacing: '-0.02em', color: '#f8fafc' }}>
                                Personalize <span style={{ background: 'linear-gradient(135deg, #818cf8, #c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>LifeOS</span>
                            </h1>
                            <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px', fontWeight: 500 }}>
                                Your preferences define the core logic of my optimization engine.
                            </p>
                        </div>
                    </div>
                </header>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {/* Routine & Energy Section */}
                    <div style={{
                        background: 'rgba(15, 23, 42, 0.4)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.06)',
                        borderRadius: '24px',
                        padding: '32px',
                        animation: 'fadeInUp 0.4s ease-out 0.1s both',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '28px', borderBottom: '1px solid rgba(255, 255, 255, 0.06)', paddingBottom: '20px' }}>
                            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <Zap size={18} color="#818cf8" />
                            </div>
                            <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', margin: 0 }}>Routine & Energy</h2>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px', marginBottom: '28px' }}>
                            <InputField label="Work Commences" type="time" name="work_start_time" value={formData.work_start_time} onChange={handleChange} icon={<Briefcase size={14} />} />
                            <InputField label="Work Concludes" type="time" name="work_end_time" value={formData.work_end_time} onChange={handleChange} icon={<Briefcase size={14} />} />
                            <InputField label="Activation (Wake)" type="time" name="wake_time" value={formData.wake_time} onChange={handleChange} icon={<Sun size={14} />} />
                            <InputField label="Rest (Sleep)" type="time" name="sleep_time" value={formData.sleep_time} onChange={handleChange} icon={<Moon size={14} />} />
                        </div>

                        <div style={{ marginBottom: '28px' }}>
                            <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>Employment Status</label>
                            <CustomSelect
                                value={formData.role}
                                onChange={(val) => setFormData(prev => ({ ...prev, role: val }))}
                                options={[
                                    { value: 'Working', label: 'Working Professional', icon: <Briefcase size={14} /> },
                                    { value: 'Student', label: 'Academic Student', icon: <BookOpen size={14} /> },
                                    { value: 'House Free', label: 'Creative / Free Spirit', icon: <Sparkles size={14} /> },
                                ]}
                            />
                        </div>

                        <div>
                            <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>Energy Modulation Patterns</label>
                            <textarea
                                name="energy_levels"
                                value={formData.energy_levels}
                                onChange={handleChange}
                                placeholder="e.g. Peak focus at 10 AM, natural crash after 2 PM..."
                                style={{
                                    width: '100%',
                                    padding: '16px',
                                    height: '100px',
                                    background: 'rgba(2, 6, 23, 0.5)',
                                    border: '1px solid rgba(255, 255, 255, 0.08)',
                                    borderRadius: '16px',
                                    color: '#e2e8f0',
                                    fontSize: '14px',
                                    fontFamily: FONT,
                                    fontWeight: 500,
                                    outline: 'none',
                                    resize: 'none',
                                    lineHeight: 1.6,
                                }}
                            />
                        </div>
                    </div>

                    {/* Goals & Context Section */}
                    <div style={{
                        background: 'rgba(15, 23, 42, 0.4)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.06)',
                        borderRadius: '24px',
                        padding: '32px',
                        animation: 'fadeInUp 0.4s ease-out 0.2s both',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '28px', borderBottom: '1px solid rgba(255, 255, 255, 0.06)', paddingBottom: '20px' }}>
                            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(168, 85, 247, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <Target size={18} color="#c084fc" />
                            </div>
                            <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#f8fafc', margin: 0 }}>Strategic Intent</h2>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '28px' }}>
                            <InputField label="Biometric Goal (Health)" type="text" name="health_goals" value={formData.health_goals} onChange={handleChange} icon={<Activity size={14} />} placeholder="e.g. Optimize sleep, intermittent fasting 16:8..." />
                            <InputField label="Cognitive Goal (Learning)" type="text" name="learning_goals" value={formData.learning_goals} onChange={handleChange} icon={<BookOpen size={14} />} placeholder="e.g. Deep work on machine learning..." />
                            <InputField label="Economic Goal (Finance)" type="text" name="finance_goals" value={formData.finance_goals} onChange={handleChange} icon={<DollarSign size={14} />} placeholder="e.g. Reduce non-essential burn..." />
                        </div>

                        <div>
                            <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>Hard Constraints & Operational Rules</label>
                            <textarea
                                name="constraints"
                                value={formData.constraints}
                                onChange={handleChange}
                                placeholder="e.g. Wednesdays are strictly meeting-free..."
                                style={{
                                    width: '100%',
                                    padding: '16px',
                                    height: '120px',
                                    background: 'rgba(2, 6, 23, 0.5)',
                                    border: '1px solid rgba(255, 255, 255, 0.08)',
                                    borderRadius: '16px',
                                    color: '#e2e8f0',
                                    fontSize: '14px',
                                    fontFamily: FONT,
                                    fontWeight: 500,
                                    outline: 'none',
                                    resize: 'none',
                                    lineHeight: 1.6,
                                }}
                            />
                        </div>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={saving}
                        style={{
                            width: '100%',
                            padding: '18px',
                            borderRadius: '18px',
                            border: 'none',
                            background: saving ? '#334155' : 'linear-gradient(135deg, #6366f1, #a855f7)',
                            color: '#fff',
                            fontSize: '16px',
                            fontWeight: 800,
                            fontFamily: FONT,
                            cursor: saving ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '12px',
                            boxShadow: saving ? 'none' : '0 8px 32px rgba(99, 102, 241, 0.3)',
                            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                            marginBottom: '40px',
                        }}
                        onMouseEnter={(e) => { if (!saving) { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 12px 40px rgba(99, 102, 241, 0.5)'; } }}
                        onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 8px 32px rgba(99, 102, 241, 0.3)'; }}
                    >
                        {saving ? <Loader2 size={20} style={{ animation: 'spin 1.2s linear infinite' }} /> : <Save size={20} />}
                        {saving ? 'Synchronizing...' : 'Save & Optimize LifeOS'}
                    </button>
                </form>
            </div>

            <style jsx global>{`
                @keyframes fadeInUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
                @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            `}</style>
        </MainLayout>
    );
}

function CustomSelect({ value, options, onChange }) {
    const [isOpen, setIsOpen] = useState(false);
    const selectedOption = options.find(opt => opt.value === value) || options[0];

    return (
        <div style={{ position: 'relative', width: '100%' }}>
            <div
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    width: '100%',
                    padding: '12px 16px',
                    background: 'rgba(2, 6, 23, 0.5)',
                    border: isOpen ? '1px solid rgba(99, 102, 241, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: '12px',
                    color: '#e2e8f0',
                    fontSize: '14px',
                    fontFamily: FONT,
                    fontWeight: 500,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    boxShadow: isOpen ? '0 0 0 4px rgba(99, 102, 241, 0.1)' : 'none',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ opacity: 0.6 }}>{selectedOption.icon}</span>
                    {selectedOption.label}
                </div>
                <div style={{
                    transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                    color: '#475569',
                    display: 'flex',
                    alignItems: 'center'
                }}>
                    <Clock size={14} />
                </div>
            </div>

            {isOpen && (
                <>
                    <div
                        onClick={() => setIsOpen(false)}
                        style={{ position: 'fixed', inset: 0, zIndex: 40 }}
                    />
                    <div style={{
                        position: 'absolute',
                        top: 'calc(100% + 8px)',
                        left: 0,
                        right: 0,
                        background: 'rgba(15, 23, 42, 0.95)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        borderRadius: '14px',
                        overflow: 'hidden',
                        zIndex: 50,
                        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
                        animation: 'dropdownIn 0.2s ease-out',
                    }}>
                        {options.map((opt) => (
                            <div
                                key={opt.value}
                                onClick={() => {
                                    onChange(opt.value);
                                    setIsOpen(false);
                                }}
                                style={{
                                    padding: '12px 16px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '12px',
                                    cursor: 'pointer',
                                    fontSize: '14px',
                                    fontWeight: 500,
                                    color: value === opt.value ? '#818cf8' : '#94a3b8',
                                    background: value === opt.value ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                                    transition: 'all 0.2s',
                                }}
                                onMouseEnter={(e) => {
                                    if (value !== opt.value) {
                                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                                        e.currentTarget.style.color = '#e2e8f0';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    if (value !== opt.value) {
                                        e.currentTarget.style.background = 'transparent';
                                        e.currentTarget.style.color = '#94a3b8';
                                    }
                                }}
                            >
                                <span style={{ opacity: value === opt.value ? 1 : 0.4 }}>{opt.icon}</span>
                                {opt.label}
                            </div>
                        ))}
                    </div>
                </>
            )}

            <style jsx>{`
                @keyframes dropdownIn {
                    from { opacity: 0; transform: translateY(-10px) scale(0.98); }
                    to { opacity: 1; transform: translateY(0) scale(1); }
                }
            `}</style>
        </div>
    );
}

function InputField({ label, icon, type, name, value, onChange, placeholder }) {
    const [focused, setFocused] = useState(false);

    return (
        <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px' }}>{label}</label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <div style={{ position: 'absolute', left: '16px', display: 'flex', alignItems: 'center', pointerEvents: 'none', transition: 'color 0.2s', color: focused ? '#818cf8' : '#475569' }}>
                    {icon}
                </div>
                <input
                    type={type}
                    name={name}
                    value={value}
                    onChange={onChange}
                    onFocus={() => setFocused(true)}
                    onBlur={() => setFocused(false)}
                    placeholder={placeholder}
                    style={{
                        width: '100%',
                        padding: `12px 16px 12px ${icon ? '42px' : '16px'}`,
                        background: 'rgba(2, 6, 23, 0.5)',
                        border: focused ? '1.5px solid rgba(99, 102, 241, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                        borderRadius: '12px',
                        color: '#e2e8f0',
                        fontSize: '14px',
                        fontFamily: FONT,
                        fontWeight: 500,
                        outline: 'none',
                        transition: 'all 0.2s ease',
                        boxShadow: focused ? '0 0 0 4px rgba(99, 102, 241, 0.1)' : 'none',
                    }}
                />
            </div>
        </div>
    );
}
