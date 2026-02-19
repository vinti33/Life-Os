import { useRouter } from 'next/router';
import { useUser } from '../store/userStore';
import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

const PUBLIC_PATHS = ['/login', '/signup', '/404', '/_error'];

export default function AuthGuard({ children }) {
    const { user, loading } = useUser();
    const router = useRouter();
    const [authorized, setAuthorized] = useState(false);

    useEffect(() => {
        // Wait for user to be loaded
        if (loading) return;

        const path = router.pathname;
        const isPublic = PUBLIC_PATHS.includes(path);

        if (user) {
            // User is logged in
            if (path === '/login' || path === '/signup') {
                // Redirect to dashboard
                router.push('/dashboard');
            } else {
                setAuthorized(true);
            }
        } else {
            // User is NOT logged in
            if (isPublic) {
                setAuthorized(true);
            } else {
                // Prevent infinite loop if already on login
                if (path !== '/login') {
                    router.push({
                        pathname: '/login',
                        query: { returnUrl: router.asPath }
                    });
                }
                setAuthorized(false);
            }
        }
    }, [user, loading, router.pathname]);

    // Show loader if determining auth status
    if (loading || (!authorized && !PUBLIC_PATHS.includes(router.pathname))) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-400">
                <div className="flex flex-col items-center gap-4">
                    {/* <Loader2 className="animate-spin text-indigo-500" size={40} /> */}
                    <div style={{ width: 40, height: 40, border: '4px solid #6366f1', borderRadius: '50%', borderTopColor: 'transparent', animation: 'spin 1s linear infinite' }} />
                    <p className="text-sm font-medium animate-pulse">Initializing LifeOS...</p>
                    <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
                </div>
            </div>
        );
    }

    return children;
}
