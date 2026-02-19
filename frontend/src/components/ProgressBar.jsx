export default function ProgressBar({ value, max = 100, className = '' }) {
    const percentage = Math.min(100, Math.max(0, (value / max) * 100));

    return (
        <div className={`w-full bg-slate-800 rounded-full overflow-hidden h-2 ${className}`}>
            <div
                className="bg-indigo-500 h-full transition-all duration-500 ease-out"
                style={{ width: `${percentage}%` }}
            />
        </div>
    );
}

