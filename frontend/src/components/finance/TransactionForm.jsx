import React, { useState } from 'react';
import { DollarSign, Tag, Calendar, FileText, CheckCircle, XCircle } from 'lucide-react';
import financeService from '../../services/financeService';
import clsx from 'clsx';

const CATEGORIES = [
    "Housing", "Transport", "Food", "Utilities", "Insurance",
    "Healthcare", "Savings", "Personal", "Entertainment", "Debt"
];

const TransactionForm = ({ onSuccess, onCancel, initialData = null }) => {
    const [formData, setFormData] = useState({
        type: initialData?.type || 'expense',
        amount: initialData?.amount || '',
        category: initialData?.category || 'Food',
        date: initialData?.date || new Date().toISOString().split('T')[0],
        description: initialData?.description || '',
        merchant: initialData?.merchant || ''
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (loading) return;
        setLoading(true);
        setError(null);

        try {
            const payload = {
                ...formData,
                amount: parseFloat(formData.amount)
            };

            if (initialData?.id || initialData?._id) {
                await financeService.updateTransaction(initialData.id || initialData._id, payload);
            } else {
                await financeService.logTransaction(payload);
            }

            if (onSuccess) onSuccess();
        } catch (err) {
            console.error(err);
            setError("Failed to save transaction. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {/* Type Selection */}
            <div className="flex gap-2 p-1 bg-slate-700/50 rounded-lg">
                <button
                    type="button"
                    onClick={() => setFormData({ ...formData, type: 'expense' })}
                    className={clsx(
                        "flex-1 py-2 rounded-md text-sm font-medium transition-colors",
                        formData.type === 'expense' ? "bg-rose-500 text-white shadow" : "text-slate-400 hover:text-white"
                    )}
                >
                    Expense
                </button>
                <button
                    type="button"
                    onClick={() => setFormData({ ...formData, type: 'income' })}
                    className={clsx(
                        "flex-1 py-2 rounded-md text-sm font-medium transition-colors",
                        formData.type === 'income' ? "bg-emerald-500 text-white shadow" : "text-slate-400 hover:text-white"
                    )}
                >
                    Income
                </button>
                <button
                    type="button"
                    onClick={() => setFormData({ ...formData, type: 'investment' })}
                    className={clsx(
                        "flex-1 py-2 rounded-md text-sm font-medium transition-colors",
                        formData.type === 'investment' ? "bg-indigo-500 text-white shadow" : "text-slate-400 hover:text-white"
                    )}
                >
                    Invest
                </button>
            </div>

            {/* Amount */}
            <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Amount</label>
                <div className="relative">
                    <DollarSign className="absolute left-3 top-2.5 text-slate-500" size={16} />
                    <input
                        type="number"
                        name="amount"
                        required
                        min="0.01"
                        step="0.01"
                        value={formData.amount}
                        onChange={handleChange}
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg py-2 pl-9 pr-4 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="0.00"
                    />
                </div>
            </div>

            {/* Category & Date */}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Category</label>
                    <div className="relative">
                        <Tag className="absolute left-3 top-2.5 text-slate-500" size={16} />
                        <select
                            name="category"
                            value={formData.category}
                            onChange={handleChange}
                            className="w-full bg-slate-800 border border-slate-600 rounded-lg py-2 pl-9 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 appearance-none"
                        >
                            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                            <option value="Salary">Salary</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Date</label>
                    <div className="relative">
                        <Calendar className="absolute left-3 top-2.5 text-slate-500" size={16} />
                        <input
                            type="date"
                            name="date"
                            required
                            value={formData.date}
                            onChange={handleChange}
                            className="w-full bg-slate-800 border border-slate-600 rounded-lg py-2 pl-9 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                    </div>
                </div>
            </div>

            {/* Description */}
            <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Description (Optional)</label>
                <div className="relative">
                    <FileText className="absolute left-3 top-2.5 text-slate-500" size={16} />
                    <input
                        type="text"
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg py-2 pl-9 pr-4 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="Lunch, Freelance, etc."
                    />
                </div>
            </div>

            {error && <p className="text-rose-400 text-xs">{error}</p>}

            {/* Actions */}
            <div className="flex gap-3 pt-2">
                <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-sm font-medium transition-colors"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex justify-center items-center gap-2"
                >
                    {loading ? "Saving..." : <><CheckCircle size={16} /> Save</>}
                </button>
            </div>
        </form>
    );
};

export default TransactionForm;
