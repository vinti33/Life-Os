import { createContext, useContext, useState } from 'react';
import { planService } from '../services/planService';

const PlanContext = createContext();

export const PlanProvider = ({ children }) => {
    const [currentPlan, setCurrentPlan] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(false);

    const fetchActivePlan = async (planType = 'daily') => {
        setLoading(true);
        try {
            const data = await planService.getActive(planType);
            setCurrentPlan(data);
            setTasks(data.tasks || []);
        } catch (error) {
            console.error('Failed to fetch active plan', error);
        } finally {
            setLoading(false);
        }
    };

    const generatePlan = async (context, planType = 'daily') => {
        setLoading(true);
        try {
            const data = await planService.fetchDraft(context, planType);
            setCurrentPlan(data);
            setTasks(data.tasks || []);
            return data;
        } finally {
            setLoading(false);
        }
    };

    return (
        <PlanContext.Provider value={{ currentPlan, tasks, loading, fetchActivePlan, generatePlan, setTasks }}>
            {children}
        </PlanContext.Provider>
    );
};

export const usePlan = () => useContext(PlanContext);
