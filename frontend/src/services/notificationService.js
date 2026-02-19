import api from '../utils/apiUtils';

export const notificationService = {
    sendPush: async (taskId, time) => {
        const response = await api.post('/notification/send', { task_id: taskId, type: 'push', time });
        return response.data;
    },
    sendEmail: async (taskId, time) => {
        const response = await api.post('/notification/send', { task_id: taskId, type: 'email', time });
        return response.data;
    },
};

