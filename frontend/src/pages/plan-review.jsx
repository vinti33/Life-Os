import { useRouter } from 'next/router';
import { usePlan } from '../store/planStore';
import PlanCard from '../components/PlanCard';
import Button from '../components/Button';
import { planService } from '../services/planService';

export default function PlanReview() {
    const { currentPlan, fetchActivePlan } = usePlan();
    const router = useRouter();

    const handleApprove = async () => {
        await planService.approve(currentPlan.plan_id);
        router.push('/dashboard');
    };

    const handleReject = async () => {
        await planService.reject(currentPlan.plan_id);
        router.push('/dashboard');
    };

    return (
        <div className="max-w-4xl mx-auto p-4 md:p-8 animate-fade-in">
            <header className="flex items-center gap-4 mb-8">
                <Button variant="ghost" onClick={() => router.push('/dashboard')}>← Desktop</Button>
                <h1 className="text-3xl font-black">Plan <span className="text-indigo-500">Review</span></h1>
            </header>

            {currentPlan?.status === 'draft' ? (
                <PlanCard
                    plan={currentPlan}
                    onApprove={handleApprove}
                    onReject={handleReject}
                />
            ) : (
                <div className="glass p-12 text-center text-slate-500">
                    No draft plans awaiting review.
                    <Button variant="primary" className="block mx-auto mt-6" onClick={() => router.push('/dashboard')}>Go to Dashboard</Button>
                </div>
            )}
        </div>
    );
}

