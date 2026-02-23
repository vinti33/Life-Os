import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: `${API_URL}/api/v1`,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to include the auth token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Add a response interceptor to handle 401 errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            console.warn('Unauthorized protocol detected. Purging credentials and redirecting.');
            localStorage.removeItem('token');
            if (typeof window !== 'undefined') {
                window.location.href = '/login?reason=session_expired';
            }
        }
        return Promise.reject(error);
    }
);

/**
 * Extracts a human-readable error message from a backend response.
 * Handles both simple strings and structured Pydantic validation errors.
 */
export const getErrorMessage = (err, defaultMessage = 'An unexpected error occurred') => {
    const detail = err.response?.data?.detail;

    if (!detail) return err.message || defaultMessage;

    if (typeof detail === 'string') return detail;

    if (Array.isArray(detail)) {
        // Handle Pydantic validation errors: [{type, loc, msg, input, ctx}, ...]
        return detail
            .map(d => {
                const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : '';
                return field ? `${field}: ${d.msg}` : d.msg;
            })
            .join(', ');
    }

    return defaultMessage;
};

export default api;
