import api from '../utils/apiUtils';

const metricsService = {
    getDaily: async () => {
        const response = await api.get('/metrics/daily');
        return response.data;
    },
    getWeekly: async () => {
        const response = await api.get('/metrics/weekly');
        return response.data;
    },
    getMonthly: async () => {
        const response = await api.get('/metrics/monthly');
        return response.data;
    },
    getFinance: async () => {
        const response = await api.get('/metrics/finance');
        return response.data;
    },
    getLifeOSIndex: async () => {
        const response = await api.get('/metrics/lifeos-index');
        return response.data;
    }
};

export default metricsService;
