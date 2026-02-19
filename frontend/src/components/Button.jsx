import { Loader2 } from 'lucide-react';

export default function Button({ children, onClick, type = 'button', variant = 'primary', loading = false, className = '', ...props }) {
    const variants = {
        primary: 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_20px_rgba(99,102,241,0.15)] hover:shadow-[0_0_35px_rgba(99,102,241,0.3)]',
        secondary: 'bg-white/5 text-slate-100 border border-white/10 hover:bg-white/10 hover:border-white/20',
        accent: 'bg-gradient-to-r from-fuchsia-600 to-indigo-600 hover:from-fuchsia-500 hover:to-indigo-500 text-white shadow-[0_0_20px_rgba(217,70,239,0.15)] hover:shadow-[0_0_35px_rgba(217,70,239,0.3)]',
        ghost: 'bg-transparent hover:bg-white/5 text-slate-400 hover:text-white',
        danger: 'bg-red-600/10 text-red-400 border border-red-500/20 hover:bg-red-600/20 hover:border-red-500/30',
        success: 'bg-emerald-600/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-600/20 hover:border-emerald-500/30',
    };

    return (
        <button
            type={type}
            onClick={onClick}
            disabled={loading || props.disabled}
            className={`
                px-6 py-2.5 rounded-xl font-semibold text-sm
                transition-all duration-300 ease-out
                active:scale-[0.97] 
                disabled:opacity-40 disabled:pointer-events-none disabled:cursor-not-allowed
                inline-flex items-center justify-center gap-2
                ${variants[variant]} ${className}
            `}
            {...props}
        >
            {loading && <Loader2 size={16} className="animate-spin" />}
            {children}
        </button>
    );
}
