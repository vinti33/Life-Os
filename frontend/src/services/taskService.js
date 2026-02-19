import api from '../utils/apiUtils';

export const taskService = {
    updateTask: async (taskId, status, reasonIfMissed, completionDate) => {
        const payload = { task_id: taskId, status, reason: reasonIfMissed };
        if (completionDate) payload.completion_date = completionDate;

        const response = await api.post('/task/update', payload);
        return response.data;
    },
    reschedule: async (taskId, newStartTime, newEndTime) => {
        const response = await api.post('/task/reschedule', { task_id: taskId, new_start_time: newStartTime, new_end_time: newEndTime });
        return response.data;
    },
    getToday: async () => {
        const response = await api.get('/task/today');
        return response.data;
    },
    createTask: async (title, startTime, endTime, category = "other") => {
        const response = await api.post('/task/create', {
            title,
            start_time: startTime,
            end_time: endTime,
            category
        });
        return response.data;
    },
};

