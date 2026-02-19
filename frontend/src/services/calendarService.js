import api from '../utils/apiUtils';

export const calendarService = {
    syncPlan: async (planId) => {
        const response = await api.post('/calendar/sync', { plan_id: planId });
        return response.data;
    },

    updateTaskEvent: async (taskId, newStart, newEnd) => {
        // Bridges task reschedule with calendar update
        const response = await api.post('/task/reschedule', {
            task_id: taskId,
            new_start_time: newStart,
            new_end_time: newEnd
        });
        return response.data;
    },

    removeTaskEvent: async (taskId) => {
        // In a real app, this would delete from both DB and Google Calendar
        const response = await api.post('/task/update', {
            task_id: taskId,
            status: 'missed'
        });
        return response.data;
    },
};

