import api from '../utils/apiUtils';

export const planService = {
    fetchDraft: async (context, planType = 'daily') => {
        console.log("Generating plan with:", { context, plan_type: planType });
        const response = await api.post('/plan/generate', { context, plan_type: planType });
        return response.data;
    },
    approve: async (planId) => {
        const response = await api.post(`/plan/approve?plan_id=${planId}`);
        return response.data;
    },
    reject: async (planId) => {
        const response = await api.post(`/plan/reject?plan_id=${planId}`);
        return response.data;
    },
    getActive: async (planType = 'daily') => {
        const response = await api.get(`/plan/active?plan_type=${planType}`);
        return response.data;
    },
    upgradeDraft: async (planId) => {
        const response = await api.post('/plan/upgrade', { plan_id: planId });
        return response.data;
    },
};

