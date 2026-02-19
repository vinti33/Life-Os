import { useRouter } from 'next/router';
import { usePlan } from '../store/planStore';
import Button from '../components/Button';

export default function Upgrade() {
    const { currentPlan } = usePlan();
    const router = useRouter();

    const handleUpgrade = async () => {
        // Call planService.upgradeDraft()
        router.push('/dashboard');
    };

    return (
        <div className="max-w-4xl mx-auto p-4 md:p-8 flex flex-col items-center justify-center min-h-[80vh] animate-fade-in">
            <div className="w-48 h-48 bg-indigo-500/20 rounded-full flex items-center justify-center mb-8 relative">
                <div className="absolute inset-0 bg-indigo-500/10 rounded-full animate-ping" />
                <span className="text-6xl">🚀</span>
            </div>

            <h1 className="text-4xl font-black text-center mb-4">Adaptive Life Upgrade</h1>
            <p className="text-slate-400 text-center max-w-lg mb-12">
                My patterns show that you are consistently 20% more productive when your deep work starts 30 minutes earlier.
                I've prepared an optimized routine template for you.
            </p>

            <div className="w-full max-w-2xl glass p-8 mb-12 border-t-4 border-t-cyan-500">
                <h3 className="text-xl font-bold mb-4">Optimized Routine Deltas</h3>
                <ul className="space-y-4">
                    <li className="flex items-center gap-4 text-slate-300">
                        <span className="text-red-400 font-mono w-16">09:00</span>
                        <span className="text-slate-500">→</span>
                        <span className="text-green-400 font-mono w-16">08:30</span>
                        <span>Deep Work Initiation</span>
                    </li>
                    <li className="flex items-center gap-4 text-slate-300">
                        <span className="text-red-400 font-mono w-16">13:00</span>
                        <span className="text-slate-500">→</span>
                        <span className="text-green-400 font-mono w-16">12:30</span>
                        <span>Early Lunch (Prevents mid-day crash)</span>
                    </li>
                </ul>
            </div>

            <div className="flex gap-4 w-full max-w-md">
                <Button variant="ghost" className="flex-1 py-4" onClick={() => router.push('/dashboard')}>Skip for now</Button>
                <Button variant="primary" className="flex-1 py-4 font-bold" onClick={handleUpgrade}>Apply Upgrade</Button>
            </div>
        </div>
    );
}

