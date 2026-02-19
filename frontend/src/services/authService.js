import api from '../utils/apiUtils';

export const authService = {
    signup: async (name, email, password) => {
        const response = await api.post('/auth/signup', { name, email, password });
        return response.data;
    },
    login: async (email, password) => {
        const response = await api.post('/auth/login', { email, password });
        return response.data;
    },
    getMe: async () => {
        const response = await api.get('/auth/me');
        return response.data;
    },
};

export const profileService = {
    getProfile: async () => {
        const response = await api.get('/profile/');
        return response.data;
    },
    updateProfile: async (profileData) => {
        const response = await api.post('/profile/', profileData);
        return response.data;
    },
};

