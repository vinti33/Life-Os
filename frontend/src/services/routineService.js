import api from '../utils/apiUtils';

const routineService = {
    createFromPlan: async (planId, name, daysOfWeek) => {
        const response = await api.post('/routine/create_from_plan', {
            plan_id: planId,
            name,
            days_of_week: daysOfWeek,
        });
        return response.data;
    },

    list: async () => {
        const response = await api.get('/routine/list');
        return response.data;
    },

    delete: async (id) => {
        const response = await api.delete(`/routine/${id}`);
        return response.data;
    }
};

export default routineService;
