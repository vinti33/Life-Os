import api from '../utils/apiUtils';

const financeService = {
    // Log a new transaction
    logTransaction: async (transactionData) => {
        const response = await api.post('/finance/transactions', transactionData);
        return response.data;
    },

    // Get dashboard metrics
    getDashboard: async (month) => {
        const params = month ? { month } : {};
        const response = await api.get('/finance/dashboard', { params });
        return response.data;
    },

    // Set or update a budget
    setBudget: async (budgetData) => {
        const response = await api.post('/finance/budgets', budgetData);
        return response.data;
    },

    // Get recent transactions
    getTransactions: async (params) => {
        const response = await api.get('/finance/transactions', { params });
        return response.data;
    },

    // Set Total Balance
    setBalance: async (targetBalance) => {
        const response = await api.post('/finance/balance', { target_balance: targetBalance });
        return response.data;
    },

    // Update transaction
    updateTransaction: async (id, data) => {
        const response = await api.put(`/finance/transactions/${id}`, data);
        return response.data;
    },

    // Delete transaction
    deleteTransaction: async (id) => {
        const response = await api.delete(`/finance/transactions/${id}`);
        return response.data;
    }
};

export default financeService;
