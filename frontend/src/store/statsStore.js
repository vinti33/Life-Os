import { createContext, useContext, useState } from 'react';
import { statsService } from '../services/statsService';

const StatsContext = createContext();

export const StatsProvider = ({ children }) => {
    const [dailyStats, setDailyStats] = useState(null);
    const [history, setHistory] = useState([]);

    const fetchStats = async () => {
        try {
            const daily = await statsService.getDaily();
            setDailyStats(daily);
            const hist = await statsService.getHistory();
            setHistory(hist);
        } catch (error) {
            console.error('Failed to fetch stats', error);
        }
    };

    return (
        <StatsContext.Provider value={{ dailyStats, history, fetchStats }}>
            {children}
        </StatsContext.Provider>
    );
};

export const useStats = () => useContext(StatsContext);
