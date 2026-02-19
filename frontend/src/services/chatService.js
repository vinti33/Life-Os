import api from '../utils/apiUtils';

export const chatService = {
    sendMessage: async (message, sessionId = null) => {
        const payload = { message };
        if (sessionId) payload.session_id = sessionId;

        const response = await api.post('/chat/message', payload);
        return response.data;
    },
    getSessions: async () => {
        const response = await api.get('/history/sessions');
        return response.data;
    },
    getSessionHistory: async (sessionId) => {
        const response = await api.get(`/history/sessions/${sessionId}`);
        return response.data;
    }
};

