import api from '../utils/apiUtils';

const progressService = {
    getYearProgress: async (year) => {
        const response = await api.get(`/progress/year/${year}`);
        return response.data;
    },
    getMonthProgress: async (year, month) => {
        const response = await api.get(`/progress/month/${year}/${month}`);
        return response.data;
    },
    getDayDetail: async (dateStr) => {
        const response = await api.get(`/progress/day/${dateStr}`);
        return response.data;
    },
    getSuggestions: async () => {
        const response = await api.get('/progress/suggestions');
        return response.data;
    }
};

export default progressService;
