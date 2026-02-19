import api from '../utils/apiUtils';

export const statsService = {
    getDaily: async () => {
        const response = await api.get('/stats/daily');
        return response.data;
    },
    getHistory: async () => {
        const response = await api.get('/stats/history');
        return response.data;
    },
};

