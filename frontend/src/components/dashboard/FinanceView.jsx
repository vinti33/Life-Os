import React, { useState, useEffect, useMemo, useRef } from 'react';
import financeService from '../../services/financeService';
import StatCard from './StatCard';
import { PieChart as RechartsPie, Pie, Cell, Tooltip, Legend } from 'recharts';
import { DollarSign, TrendingUp, PieChart, ShieldCheck, X, Edit2, Trash2 } from 'lucide-react';
import clsx from 'clsx';
import TransactionForm from '../finance/TransactionForm';

// ... imports

const COLORS = {
    Housing: '#f43f5e', // rose-500
    Transport: '#f59e0b', // amber-500
    Food: '#10b981', // emerald-500
    Utilities: '#3b82f6', // blue-500
    Insurance: '#6366f1', // indigo-500
    Healthcare: '#ec4899', // pink-500
    Savings: '#8b5cf6', // violet-500
    Personal: '#14b8a6', // teal-500
    Entertainment: '#f97316', // orange-500
    Debt: '#64748b', // slate-500
    unknown: '#94a3b8' // slate-400
};

const FinanceView = ({ plan }) => {
    // State for live dashboard data
    const [dashboardData, setDashboardData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isTransactionModalOpen, setIsTransactionModalOpen] = useState(false);

    const [editingTransaction, setEditingTransaction] = useState(null);

    // Balance Modal State
    const [isBalanceModalOpen, setIsBalanceModalOpen] = useState(false);
    const [targetBalance, setTargetBalance] = useState('');

    // Initial load
    const fetchDashboard = async () => {
        try {
            const data = await financeService.getDashboard();
            setDashboardData(data);
        } catch (error) {
            console.error("Failed to load finance dashboard", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDashboard();
    }, []);

    const handleTransactionSuccess = () => {
        setIsTransactionModalOpen(false);
        setEditingTransaction(null); // Clear editing state
        fetchDashboard(); // Refresh data
    };

    const handleDeleteTransaction = async (id) => {
        if (!window.confirm("Are you sure you want to delete this transaction?")) return;
        try {
            await financeService.deleteTransaction(id);
            fetchDashboard();
        } catch (error) {
            console.error("Failed to delete transaction", error);
        }
    };

    // Fallback to Plan data if API fails or is empty, but prioritize live data
    const metrics = dashboardData?.metrics || {};
    const budgetPerf = dashboardData?.budget_performance || [];
    const transactions = dashboardData?.recent_transactions || [];

    // Spending Data for Pie Chart
    const spendingData = useMemo(() => {
        if (!dashboardData) return [];
        return budgetPerf.filter(b => b.actual > 0).map(b => ({
            name: b.category,
            value: b.actual
        }));
    }, [dashboardData]);

    // Manual dimension calculation for Pie Chart
    const [chartDims, setChartDims] = useState({ width: 0, height: 0 });
    const chartContainerRef = useRef(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;
        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                if (entry.contentRect.width > 0) {
                    setChartDims({
                        width: entry.contentRect.width,
                        height: entry.contentRect.height
                    });
                }
            }
        });
        resizeObserver.observe(chartContainerRef.current);
        return () => resizeObserver.disconnect();
    }, []);

    const handleBalanceSubmit = async (e) => {
        e.preventDefault();
        if (!targetBalance && targetBalance !== 0) return;
        try {
            await financeService.setBalance(parseFloat(targetBalance));
            setIsBalanceModalOpen(false);
            setTargetBalance('');
            fetchDashboard();
        } catch (error) {
            console.error("Failed to update balance", error);
            alert("Failed to update balance");
        }
    };

    return (
        <div className="space-y-6 animate-fadeIn relative">
            {/* Balance Modal */}
            {isBalanceModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-sm p-6 shadow-2xl animate-scaleIn">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-white">Set Total Balance</h3>
                            <button onClick={() => setIsBalanceModalOpen(false)} className="text-slate-400 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleBalanceSubmit} className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">Current Actual Balance</label>
                                <div className="relative">
                                    <DollarSign className="absolute left-3 top-2.5 text-slate-500" size={16} />
                                    <input
                                        type="number"
                                        step="0.01"
                                        required
                                        value={targetBalance}
                                        onChange={(e) => setTargetBalance(e.target.value)}
                                        className="w-full bg-slate-800 border border-slate-600 rounded-lg py-2 pl-9 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                        placeholder="e.g. 5000.00"
                                        autoFocus
                                    />
                                </div>
                                <p className="text-xs text-slate-500 mt-2">
                                    We will create a "Balance Adjustment" transaction to match this amount.
                                </p>
                            </div>
                            <button
                                type="submit"
                                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                            >
                                Update Balance
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Transaction Modal (Existing) */}
            {isTransactionModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-md p-6 shadow-2xl animate-scaleIn">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-white">{editingTransaction ? 'Edit Transaction' : 'Log Transaction'}</h3>
                            <button onClick={() => setIsTransactionModalOpen(false)} className="text-slate-400 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>
                        <TransactionForm
                            onSuccess={handleTransactionSuccess}
                            onCancel={() => {
                                setIsTransactionModalOpen(false);
                                setEditingTransaction(null);
                            }}
                            initialData={editingTransaction}
                        />
                    </div>
                </div>
            )}

            {/* Top Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Total Balance Card (Editable) */}
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4 relative group">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">Total Balance</p>
                            <h3 className="text-2xl font-bold text-white mt-1">
                                ${(metrics.total_balance ?? 0).toLocaleString()}
                            </h3>
                        </div>
                        <div className="p-2 bg-emerald-500/10 rounded-lg">
                            <ShieldCheck size={20} className="text-emerald-500" />
                        </div>
                    </div>
                    <button
                        onClick={() => {
                            setTargetBalance(metrics.total_balance || '');
                            setIsBalanceModalOpen(true);
                        }}
                        className="absolute top-2 right-2 p-1.5 text-slate-500 hover:text-white hover:bg-slate-700 rounded-md opacity-0 group-hover:opacity-100 transition-all"
                        title="Edit Balance"
                    >
                        <Edit2 size={14} />
                    </button>
                </div>

                <StatCard title="Net Savings (Mo)" value={`$${metrics.net_savings || 0}`} unit={metrics.savings_rate + '%'} icon={DollarSign} color={metrics.net_savings >= 0 ? "emerald" : "rose"} />
                <StatCard title="Total Income" value={`$${metrics.total_income || 0}`} icon={TrendingUp} color="indigo" />
                <StatCard title="Total Expense" value={`$${metrics.total_expense || 0}`} icon={PieChart} color="rose" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Visuals & Actions */}
                <div className="space-y-6">
                    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
                        <h3 className="text-white font-bold text-lg mb-4">Capital Allocation</h3>
                        <div ref={chartContainerRef} style={{ width: '100%', height: 250, minHeight: 250, position: 'relative' }}>
                            {chartDims.width > 0 && spendingData.length > 0 ? (
                                <RechartsPie width={chartDims.width} height={chartDims.height}>
                                    <Pie
                                        data={spendingData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {spendingData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[entry.name] || COLORS.unknown} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }}
                                        formatter={(value) => `$${value}`}
                                    />
                                    <Legend />
                                </RechartsPie>
                            ) : (
                                <div className="flex items-center justify-center h-full text-slate-500 text-sm italic">
                                    No spending data yet
                                </div>
                            )}
                        </div>
                    </div>

                    <button
                        onClick={() => setIsTransactionModalOpen(true)}
                        className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                    >
                        <DollarSign size={18} /> Log Transaction
                    </button>
                </div>

                {/* Main Content: Budgets & Ledger */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Budget vs Actuals */}
                    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
                        <h3 className="text-white font-bold text-lg mb-4 flex justify-between items-center">
                            <span>Budget Adherence</span>
                            <span className="text-xs text-slate-500 font-normal">Monthly Cap</span>
                        </h3>
                        <div className="space-y-4">
                            {budgetPerf.map((b, idx) => (
                                <div key={idx} className="space-y-1">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-200 font-medium capitalize">{b.category}</span>
                                        <span className={clsx(
                                            "font-mono",
                                            b.status === 'exceeded' ? "text-rose-400" : "text-slate-400"
                                        )}>
                                            ${b.actual} / ${b.budget}
                                        </span>
                                    </div>
                                    <div className="h-2 w-full bg-slate-700/50 rounded-full overflow-hidden">
                                        <div className={clsx(
                                            "h-full rounded-full transition-all duration-500",
                                            b.status === 'exceeded' ? "bg-rose-500" : b.status === 'warning' ? "bg-amber-500" : "bg-emerald-500"
                                        )} style={{ width: `${Math.min(b.percentage, 100)}%` }} />
                                    </div>
                                </div>
                            ))}
                            {budgetPerf.length === 0 && (
                                <p className="text-slate-500 text-sm italic">No budgets set. Transactions will appear here automatically.</p>
                            )}
                        </div>
                    </div>

                    {/* Recent Transactions */}
                    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6">
                        <h3 className="text-white font-bold text-lg mb-4">Recent Transactions</h3>
                        <div className="space-y-2">
                            {transactions.length > 0 ? transactions.map((item, idx) => (
                                <div key={item.id || idx} className="flex justify-between items-center p-3 hover:bg-slate-700/20 rounded-lg transition-colors border-b border-slate-700/50 last:border-0 group">
                                    <div className="flex items-center gap-3">
                                        <div className={clsx(
                                            "w-8 h-8 rounded-full flex items-center justify-center",
                                            item.type === 'income' ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-700 text-slate-400"
                                        )}>
                                            <DollarSign size={14} />
                                        </div>
                                        <div>
                                            <p className="text-white font-medium">{item.description || item.category}</p>
                                            <p className="text-xs text-slate-500 capitalize">{item.category} • {item.date}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className={clsx(
                                            "font-mono font-medium",
                                            item.type === 'income' ? "text-emerald-400" : "text-slate-200"
                                        )}>
                                            {item.type === 'income' ? '+' : '-'}${item.amount}
                                        </span>
                                        {/* Actions */}
                                        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={() => {
                                                    setEditingTransaction(item);
                                                    setIsTransactionModalOpen(true);
                                                }}
                                                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-600 rounded-md transition-colors"
                                            >
                                                <Edit2 size={14} />
                                            </button>
                                            <button
                                                onClick={() => handleDeleteTransaction(item.id || item._id)}
                                                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-600 rounded-md transition-colors"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )) : (
                                <p className="text-slate-500 text-sm italic">No recent transactions found.</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FinanceView;
