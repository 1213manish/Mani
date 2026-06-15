import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { groupsApi, expensesApi } from '../../api/endpoints';
import { format } from 'date-fns';
import { 
  Mail, 
  Image as ImageIcon, 
  MousePointerClick,
  Plus,
  Search,
  MoreVertical,
  CheckCircle,
  Clock,
  ArrowRight
} from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  // Fetch groups
  const { data: groups } = useQuery({
    queryKey: ['groups'],
    queryFn: () => groupsApi.list().then(r => r.data.results),
  });

  const firstGroupId = groups?.[0]?.id;

  // Fetch expenses for the first group dynamically
  const { data: expenses, isLoading: expensesLoading } = useQuery({
    queryKey: ['expenses', firstGroupId],
    queryFn: () => firstGroupId ? expensesApi.listByGroup(firstGroupId).then(r => r.data.results) : Promise.resolve([]),
    enabled: !!firstGroupId,
  });

  // Calculations for balance donut chart
  // Sum up owed amounts dynamically from active group balances
  const totalBalance = 8700; // Mocked active Goa Trip seed summary total balance
  const requestedAmount = 7450; // Owed to Aisha
  const unrequestedAmount = 1250; // Aisha owes Rohan

  // Donut chart math
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const requestedPercent = (requestedAmount / totalBalance) * 100;
  const unrequestedPercent = (unrequestedAmount / totalBalance) * 100;
  
  // Dashoffset calculations (SVG stroke-dashoffset runs clockwise from 3 o'clock)
  const requestedOffset = circumference - (requestedPercent / 100) * circumference;
  const unrequestedOffset = circumference - (unrequestedPercent / 100) * circumference;

  // Render budget circles data
  const budgets = [
    { name: 'February Expenses', spent: 87.50, total: 300.00, color: '#ffc107', date: '01/02/26' },
    { name: 'Goa Trip splits', spent: 297.50, total: 850.00, color: '#ffc107', date: '12/06/26' },
    { name: 'Inditex Meeting', spent: 187.50, total: 400.00, color: '#2b50d8', date: '01/02/26' },
  ];

  return (
    <div className="space-y-8 text-slate-800">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-slate-400 text-sm font-medium">Hello {user?.first_name || 'Marcos'},</p>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mt-0.5">
            Take a look at your current balance 👁️👁️
          </h1>
        </div>
        <button 
          onClick={() => navigate('/groups')}
          className="btn-primary inline-flex items-center gap-1.5 self-start sm:self-center"
        >
          <Plus size={16} />
          New Group
        </button>
      </div>

      {/* Main Grid Layout (Inspired by Binder dashboard layout) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Donut Chart & Quick Actions (5 Span) */}
        <div className="lg:col-span-5 space-y-8">
          
          {/* Balance Donut Chart Card */}
          <div className="glass-card p-6 flex flex-col items-center justify-center relative min-h-[360px]">
            <div className="text-left w-full">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Requested balance</span>
              <span className="text-2xl font-extrabold text-[#2b50d8]">₹{requestedAmount.toLocaleString('en-IN')}.00</span>
            </div>

            {/* SVG Donut Chart */}
            <div className="relative w-44 h-44 flex items-center justify-center my-6 animate-fade-in">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
                {/* Gray back ring */}
                <circle cx="80" cy="80" r="60" stroke="#f1f5f9" strokeWidth="12" fill="transparent" />
                {/* Yellow segment (Unrequested) */}
                <circle 
                  cx="80" cy="80" r="60" 
                  stroke="#ffc107" strokeWidth="12" fill="transparent" 
                  strokeDasharray={circumference} 
                  strokeDashoffset={unrequestedOffset} 
                  strokeLinecap="round"
                />
                {/* Blue segment (Requested) */}
                <circle 
                  cx="80" cy="80" r="60" 
                  stroke="#2b50d8" strokeWidth="12" fill="transparent" 
                  strokeDasharray={circumference} 
                  strokeDashoffset={requestedOffset} 
                  strokeLinecap="round"
                />
              </svg>
              {/* Central text label */}
              <div className="absolute flex flex-col items-center">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Total</span>
                <span className="text-xl font-extrabold text-slate-900 mt-0.5">₹{totalBalance.toLocaleString('en-IN')}.00</span>
              </div>
            </div>

            {/* Segment Key Details */}
            <div className="flex items-center justify-between w-full border-t border-slate-100 pt-4 text-xs font-semibold text-slate-600">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#ffc107]" />
                <span>Unrequested: <span className="text-slate-800">₹{unrequestedAmount.toLocaleString('en-IN')}.00</span></span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#2b50d8]" />
                <span>Requested: <span className="text-slate-800">₹{requestedAmount.toLocaleString('en-IN')}.00</span></span>
              </div>
            </div>
          </div>

          {/* Add a New Expense Quick Actions */}
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-1">
              <Plus className="w-4 h-4 text-[#2b50d8]" /> Add a New Expense
            </h3>
            <div className="flex gap-4">
              {/* Email Button */}
              <div 
                onClick={() => navigate('/import')}
                className="bg-[#f0f3fa] hover:bg-[#e2e8f0] rounded-2xl p-4 flex flex-col items-center justify-center gap-2.5 cursor-pointer transition-all w-full group"
              >
                <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center text-[#2b50d8] shadow-sm shadow-[#2b50d8]/10 group-hover:scale-105 transition-transform">
                  <Mail className="w-4.5 h-4.5" />
                </div>
                <span className="text-[11px] font-bold text-slate-500 group-hover:text-slate-800">Email</span>
              </div>

              {/* Library Button */}
              <div 
                onClick={() => navigate('/groups')}
                className="bg-[#f0f3fa] hover:bg-[#e2e8f0] rounded-2xl p-4 flex flex-col items-center justify-center gap-2.5 cursor-pointer transition-all w-full group"
              >
                <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center text-[#2b50d8] shadow-sm shadow-[#2b50d8]/10 group-hover:scale-105 transition-transform">
                  <ImageIcon className="w-4.5 h-4.5" />
                </div>
                <span className="text-[11px] font-bold text-slate-500 group-hover:text-slate-800">Library</span>
              </div>

              {/* Manually Button */}
              <div 
                onClick={() => navigate('/groups')}
                className="bg-[#f0f3fa] hover:bg-[#e2e8f0] rounded-2xl p-4 flex flex-col items-center justify-center gap-2.5 cursor-pointer transition-all w-full group"
              >
                <div className="w-9 h-9 rounded-xl bg-white flex items-center justify-center text-[#2b50d8] shadow-sm shadow-[#2b50d8]/10 group-hover:scale-105 transition-transform">
                  <MousePointerClick className="w-4.5 h-4.5" />
                </div>
                <span className="text-[11px] font-bold text-slate-500 group-hover:text-slate-800">Manually</span>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Budgets & Expenses (7 Span) */}
        <div className="lg:col-span-7 space-y-8">
          
          {/* Your Current Budgets Circular Rings */}
          <div className="space-y-4">
            <h3 className="text-sm font-extrabold text-slate-400 uppercase tracking-widest text-left">Your Current Budgets</h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {budgets.map((budget, index) => {
                const percent = Math.round((budget.spent / budget.total) * 100);
                return (
                  <div key={index} className="glass-card p-4 flex items-center gap-4 animate-slide-up">
                    
                    {/* SVG progress circle ring */}
                    <div className="relative w-14 h-14 flex items-center justify-center flex-shrink-0">
                      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 40 40">
                        {/* Inner gray bg circle */}
                        <circle cx="20" cy="20" r="16" stroke="#f8fafc" strokeWidth="3" fill="transparent" />
                        {/* Outer color segment circle */}
                        <circle 
                          cx="20" cy="20" r="16" 
                          stroke={budget.color} strokeWidth="3" fill="transparent" 
                          strokeDasharray={100.5} 
                          strokeDashoffset={100.5 - percent}
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className="absolute text-[8px] font-bold text-slate-800">{percent}%</span>
                    </div>

                    {/* Budget Info */}
                    <div className="text-left min-w-0">
                      <h4 className="text-xs font-bold text-slate-800 truncate mb-1" title={budget.name}>{budget.name}</h4>
                      <div className="text-[9px] font-semibold text-slate-400 space-y-0.5">
                        <div className="flex justify-between gap-2">Spent: <span className="text-slate-700 font-bold">₹{budget.spent}0</span></div>
                        <div className="flex justify-between gap-2">Rem: <span className="text-slate-700 font-bold">₹{(budget.total - budget.spent)}0</span></div>
                        <div className="text-[8px] text-slate-300 font-medium">{budget.date}</div>
                      </div>
                    </div>

                  </div>
                );
              })}
            </div>
          </div>

          {/* Your Expenses Table List */}
          <div className="glass-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-extrabold text-slate-400 uppercase tracking-widest">Your Expenses</h3>
              <div className="flex items-center gap-3">
                <button className="text-slate-400 hover:text-slate-700"><Search className="w-4.5 h-4.5" /></button>
                <button className="text-slate-400 hover:text-slate-700"><MoreVertical className="w-4.5 h-4.5" /></button>
              </div>
            </div>

            {/* Expenses List Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">
                    <th className="pb-3 pr-4">Company</th>
                    <th className="pb-3 pr-4">Group</th>
                    <th className="pb-3 pr-4">Date</th>
                    <th className="pb-3 pr-4 text-right">Amount</th>
                    <th className="pb-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {expensesLoading ? (
                    [1,2,3].map(i => (
                      <tr key={i} className="shimmer h-12 rounded-xl" />
                    ))
                  ) : !expenses || expenses.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-slate-400 font-medium">
                        No expenses logged yet. Create a group and add expenses to see them here!
                      </td>
                    </tr>
                  ) : (
                    expenses.slice(0, 5).map((expense) => {
                      const isSettled = expense.splits.every(s => s.is_settled);
                      return (
                        <tr key={expense.id} className="hover:bg-slate-50/50 transition-colors">
                          {/* Company column */}
                          <td className="py-3.5 pr-4 font-bold text-slate-900 flex items-center gap-2">
                            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-[#2b50d8] flex items-center justify-center font-bold">
                              {expense.title[0].toUpperCase()}
                            </div>
                            <span className="truncate max-w-[120px]">{expense.title}</span>
                          </td>
                          {/* Budget group column */}
                          <td className="py-3.5 pr-4 font-semibold text-slate-500">
                            {groups?.find(g => g.id === expense.group)?.name || 'Goa Trip 2024'}
                          </td>
                          {/* Date column */}
                          <td className="py-3.5 pr-4 font-medium text-slate-400">
                            {format(new Date(expense.expense_date), 'dd/MM/yy')}
                          </td>
                          {/* Amount column */}
                          <td className="py-3.5 pr-4 text-right font-extrabold text-slate-900">
                            ₹{parseFloat(expense.amount).toLocaleString('en-IN')}
                          </td>
                          {/* Status column */}
                          <td className="py-3.5 text-center">
                            {isSettled ? (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">
                                <CheckCircle className="w-3 h-3" /> Approved
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-600 border border-amber-100">
                                <Clock className="w-3 h-3" /> Pending
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* View all expenses link */}
            {firstGroupId && (
              <Link 
                to={`/groups/${firstGroupId}`}
                className="text-xs font-bold text-[#2b50d8] hover:text-[#1e3a8a] transition-colors pt-2 flex items-center justify-center gap-1 border-t border-slate-100"
              >
                View group transactions <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            )}

          </div>
        </div>

      </div>
    </div>
  );
}
