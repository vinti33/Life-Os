import { useState, useEffect } from 'react';

export default function Notification({ message, type = 'info', duration = 3000, onClose }) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => {
            setVisible(false);
            setTimeout(onClose, 300); // Wait for fade out
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    if (!visible) return null;

    const styles = {
        info: 'bg-indigo-600 text-white shadow-indigo-500/20',
        success: 'bg-green-600 text-white shadow-green-500/20',
        warning: 'bg-amber-500 text-white shadow-amber-500/20',
        error: 'bg-red-600 text-white shadow-red-500/20',
    };

    return (
        <div
            className={`fixed top-4 right-4 z-[100] p-4 rounded-xl shadow-2xl animate-fade-in cursor-pointer ${styles[type]}`}
            onClick={() => (window.location.href = '/today-tasks')}
        >
            <div className="flex items-center gap-3">
                <span className="text-sm font-medium">{message}</span>
                <button onClick={() => setVisible(false)} className="opacity-50 hover:opacity-100 transition-all">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
    );
}

