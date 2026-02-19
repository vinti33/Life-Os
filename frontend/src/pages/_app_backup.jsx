import '../styles/globals.css';
import { UserProvider } from '../store/userStore';
import { PlanProvider } from '../store/planStore';
import { StatsProvider } from '../store/statsStore';
import { ChatProvider } from '../store/chatStore';
import AuthGuard from '../components/AuthGuard';

function MyApp({ Component, pageProps }) {
    return (
        <UserProvider>
            <PlanProvider>
                <StatsProvider>
                    <ChatProvider>
                        <AuthGuard>
                            <div className="min-h-screen bg-slate-950 text-slate-50">
                                <Component {...pageProps} />
                            </div>
                        </AuthGuard>
                    </ChatProvider>
                </StatsProvider>
            </PlanProvider>
        </UserProvider>
    );
}

export default MyApp;
