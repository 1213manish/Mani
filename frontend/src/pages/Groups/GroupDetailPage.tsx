import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { groupsApi, expensesApi, balancesApi } from '../../api/endpoints';
import {
  Receipt, Scale, ArrowLeft, Plus, Upload,
  TrendingUp, TrendingDown, CalendarDays, ArrowRight,
} from 'lucide-react';
import { format } from 'date-fns';
import clsx from 'clsx';

function MemberAvatars({ members }: { members: any[] }) {
  return (
    <div className="flex -space-x-2">
      {members.slice(0, 5).map((m) => (
        <div
          key={m.id}
          className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 border-2 border-slate-900 flex items-center justify-center text-white text-xs font-semibold"
          title={m.user.full_name}
        >
          {m.user.full_name[0]}
        </div>
      ))}
      {members.length > 5 && (
        <div className="w-8 h-8 rounded-full bg-slate-700 border-2 border-slate-900 flex items-center justify-center text-slate-400 text-xs">
          +{members.length - 5}
        </div>
      )}
    </div>
  );
}

export default function GroupDetailPage() {
  const { groupId } = useParams<{ groupId: string }>();

  const { data: group, isLoading: groupLoading } = useQuery({
    queryKey: ['group', groupId],
    queryFn: () => groupsApi.get(groupId!).then(r => r.data),
  });

  const { data: expenses } = useQuery({
    queryKey: ['expenses', groupId],
    queryFn: () => expensesApi.listByGroup(groupId!).then(r => r.data.results),
  });

  const { data: balances } = useQuery({
    queryKey: ['balances', groupId],
    queryFn: () => balancesApi.groupBalances(groupId!).then(r => r.data),
  });

  const { data: members } = useQuery({
    queryKey: ['group-members', groupId],
    queryFn: () => groupsApi.listMembers(groupId!).then(r => r.data.results),
  });

  if (groupLoading) {
    return (
      <div className="space-y-4">
        <div className="h-40 glass-card shimmer" />
        <div className="grid grid-cols-3 gap-4">
          {[1,2,3].map(i => <div key={i} className="h-24 glass-card shimmer" />)}
        </div>
      </div>
    );
  }

  if (!group) return <div className="text-slate-400">Group not found.</div>;

  return (
    <div className="space-y-6">
      {/* Breadcrumb + header */}
      <div>
        <Link to="/groups" className="text-slate-500 hover:text-white text-sm flex items-center gap-1 mb-4 transition-colors w-fit">
          <ArrowLeft size={14} /> Back to Groups
        </Link>
        <div className="glass-card p-6">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl flex items-center justify-center text-white font-bold text-2xl shadow-xl shadow-primary-900/30">
                {group.name[0]}
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">{group.name}</h1>
                {group.description && (
                  <p className="text-slate-400 text-sm mt-1">{group.description}</p>
                )}
                <div className="flex items-center gap-3 mt-2">
                  {members && <MemberAvatars members={members.filter(m => m.is_active)} />}
                  <span className="text-slate-500 text-xs">
                    {members?.filter(m => m.is_active).length || 0} active members
                  </span>
                </div>
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Link to={`/groups/${groupId}/expenses/new`} className="btn-primary flex items-center gap-2 text-sm">
                <Plus size={15} /> Add Expense
              </Link>
              <Link to={`/import?group=${groupId}`} className="btn-secondary flex items-center gap-2 text-sm">
                <Upload size={15} /> Import CSV
              </Link>
              <Link to={`/groups/${groupId}/balances`} className="btn-secondary flex items-center gap-2 text-sm">
                <Scale size={15} /> Balances
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Balance summary */}
      {balances && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">Balance Summary</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {balances.balances.map((b) => (
              <div key={b.user_id} className={clsx(
                'glass-card p-4 flex items-center gap-3',
                parseFloat(b.net_balance) > 0 ? 'border-emerald-500/20' :
                parseFloat(b.net_balance) < 0 ? 'border-red-500/20' : 'border-white/5'
              )}>
                <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
                  {b.user_name[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium truncate">{b.user_name}</p>
                  <p className={clsx(
                    'text-sm font-bold',
                    parseFloat(b.net_balance) > 0 ? 'text-emerald-400' :
                    parseFloat(b.net_balance) < 0 ? 'text-red-400' : 'text-slate-400'
                  )}>
                    {parseFloat(b.net_balance) > 0 ? '+' : ''}₹{parseFloat(b.net_balance).toFixed(2)}
                  </p>
                </div>
                {parseFloat(b.net_balance) > 0 ? (
                  <TrendingUp size={16} className="text-emerald-400" />
                ) : parseFloat(b.net_balance) < 0 ? (
                  <TrendingDown size={16} className="text-red-400" />
                ) : null}
              </div>
            ))}
          </div>
          <Link
            to={`/groups/${groupId}/balances`}
            className="mt-3 text-primary-400 hover:text-primary-300 text-sm flex items-center gap-1 transition-colors"
          >
            View detailed breakdown <ArrowRight size={14} />
          </Link>
        </div>
      )}

      {/* Expenses list */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-white">Recent Expenses</h2>
          <span className="text-slate-500 text-sm">{expenses?.length || 0} total</span>
        </div>

        {!expenses?.length ? (
          <div className="glass-card p-10 text-center">
            <Receipt size={32} className="text-slate-600 mx-auto mb-3" />
            <p className="text-white font-medium">No expenses yet</p>
            <p className="text-slate-500 text-sm mt-1">Add your first expense to start tracking</p>
          </div>
        ) : (
          <div className="glass-card overflow-hidden">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="pl-6">Expense</th>
                  <th>Paid By</th>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Split</th>
                </tr>
              </thead>
              <tbody>
                {expenses.slice(0, 20).map((expense) => (
                  <tr key={expense.id} className="hover:bg-white/3 transition-colors">
                    <td className="pl-6">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-primary-500/15 rounded-xl flex items-center justify-center">
                          <Receipt size={15} className="text-primary-400" />
                        </div>
                        <div>
                          <p className="text-white font-medium text-sm">{expense.title}</p>
                          {expense.category && (
                            <span className="badge-info text-xs">{expense.category}</span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-gradient-to-br from-primary-500 to-accent-500 rounded-full flex items-center justify-center text-white text-xs">
                          {expense.paid_by.full_name[0]}
                        </div>
                        <span className="text-slate-300 text-sm">{expense.paid_by.full_name}</span>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-1.5 text-slate-400 text-sm">
                        <CalendarDays size={13} />
                        {format(new Date(expense.expense_date), 'MMM d, yyyy')}
                      </div>
                    </td>
                    <td>
                      <span className="text-white font-semibold text-sm">
                        {expense.currency.symbol}{parseFloat(expense.amount).toLocaleString('en-IN')}
                      </span>
                    </td>
                    <td>
                      <span className="badge-info">{expense.split_type}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Members section */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">Members</h2>
        <div className="glass-card overflow-hidden">
          <table className="data-table">
            <thead>
              <tr>
                <th className="pl-6">Member</th>
                <th>Role</th>
                <th>Joined</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {members?.map((m) => (
                <tr key={m.id} className="hover:bg-white/3 transition-colors">
                  <td className="pl-6">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center text-white text-sm font-semibold">
                        {m.user.full_name[0]}
                      </div>
                      <div>
                        <p className="text-white font-medium text-sm">{m.user.full_name}</p>
                        <p className="text-slate-500 text-xs">{m.user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={clsx('badge', m.role === 'ADMIN' ? 'badge-warning' : 'badge-info')}>
                      {m.role}
                    </span>
                  </td>
                  <td className="text-slate-400 text-sm">
                    {format(new Date(m.joined_at), 'MMM d, yyyy')}
                  </td>
                  <td>
                    <span className={clsx('badge', m.is_active ? 'badge-success' : 'badge-error')}>
                      {m.is_active ? 'Active' : `Left ${m.left_at ? format(new Date(m.left_at), 'MMM d') : ''}`}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
