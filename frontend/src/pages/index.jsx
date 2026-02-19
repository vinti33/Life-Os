import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useUser } from '../store/userStore';

export default function Home() {
    const { user, loading } = useUser();
    const router = useRouter();

    useEffect(() => {
        if (!loading) {
            if (user) {
                router.push('/dashboard');
            } else {
                router.push('/login');
            }
        }
    }, [user, loading, router]);

    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="animate-pulse text-indigo-400">Initializing LifeOS...</div>
        </div>
    );
}
