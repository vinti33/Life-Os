import { createContext, useContext, useState } from 'react';
import { planService } from '../services/planService';

const PlanContext = createContext();

export const PlanProvider = ({ children }) => {
    const [currentPlan, setCurrentPlan] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchActivePlan = async (planType = 'daily') => {
        setLoading(true);
        setError(null);
        try {
            const data = await planService.getActive(planType);
            setCurrentPlan(data);
            setTasks(data.tasks || []);
        } catch (error) {
            console.error('Failed to fetch active plan', error);
            setError('Backend unreachable. Please check if the server is running.');
        } finally {
            setLoading(false);
        }
    };

    const generatePlan = async (context, planType = 'daily') => {
        setLoading(true);
        setError(null);
        try {
            const data = await planService.fetchDraft(context, planType);
            setCurrentPlan(data);
            setTasks(data.tasks || []);
            return data;
        } catch (err) {
            console.error('Failed to generate plan', err);
            const msg = err.response?.data?.detail || err.message || 'Generation failed';
            setError(typeof msg === 'string' ? msg : 'Architecture protocol failed. Re-trying might help.');
            throw err; // Re-throw so component can handle it if needed
        } finally {
            setLoading(false);
        }
    };

    return (
        <PlanContext.Provider value={{
            currentPlan, tasks, loading, error,
            fetchActivePlan, generatePlan, setTasks, setError
        }}>
            {children}
        </PlanContext.Provider>
    );
};

export const usePlan = () => useContext(PlanContext);
