import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { groupsApi, expensesApi, currenciesApi } from '../../api/endpoints';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import type { GroupMembership, Currency } from '../../types';

type SplitType = 'EQUAL' | 'PERCENTAGE' | 'EXACT' | 'SHARES';

export default function ExpenseCreatePage() {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { user } = useAuthStore();

  const [form, setForm] = useState({
    title: '', description: '', amount: '',
    currency: '', paid_by: user?.id || '',
    expense_date: new Date().toISOString().split('T')[0],
    split_type: 'EQUAL' as SplitType, notes: '', category: '',
    exchange_rate: '1.0',
  });

  const [splits, setSplits] = useState<Array<{ user_id: string; amount?: string; percentage?: string; units?: string }>>([]);

  const { data: group } = useQuery({
    queryKey: ['group', groupId],
    queryFn: () => groupsApi.get(groupId!).then(r => r.data),
  });

  const { data: members } = useQuery<GroupMembership[]>({
    queryKey: ['group-members', groupId],
    queryFn: () => groupsApi.listMembers(groupId!).then(r => {
      const active = r.data.results.filter((m: GroupMembership) => m.is_active);
      setSplits(active.map((m: GroupMembership) => ({
        user_id: m.user.id,
        percentage: String(100 / active.length),
        units: '1',
        amount: '0',
      })));
      return r.data.results;
    }),
  });

  const { data: currencies } = useQuery<Currency[]>({
    queryKey: ['currencies'],
    queryFn: () => currenciesApi.list().then(r => {
      if (r.data.results.length > 0 && !form.currency) {
        setForm(f => ({ ...f, currency: r.data.results[0].id }));
      }
      return r.data.results;
    }),
  });

  const createMutation = useMutation({
    mutationFn: () => {
      const payload: Record<string, unknown> = { ...form, splits };
      if (form.split_type === 'EQUAL') delete payload.splits;
      return expensesApi.create(groupId!, payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['expenses', groupId] });
      qc.invalidateQueries({ queryKey: ['balances', groupId] });
      navigate(`/groups/${groupId}`);
    },
  });

  const activeMembers = members?.filter((m: GroupMembership) => m.is_active) || [];

  const updateSplit = (userId: string, field: string, value: string) => {
    setSplits(prev => prev.map(s => s.user_id === userId ? { ...s, [field]: value } : s));
  };

  const SPLIT_TYPES = [
    { value: 'EQUAL', label: 'Equal Split', desc: 'Divided equally among all active members' },
    { value: 'PERCENTAGE', label: 'Percentage', desc: 'Each member pays a specific percentage' },
    { value: 'EXACT', label: 'Exact Amount', desc: 'Specify exact amount per person' },
    { value: 'SHARES', label: 'Shares', desc: 'Split proportionally by share units' },
  ];

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <Link to={`/groups/${groupId}`} className="text-slate-500 hover:text-white text-sm flex items-center gap-1 mb-4 transition-colors w-fit">
          <ArrowLeft size={14} /> Back to {group?.name || 'Group'}
        </Link>
        <h1 className="section-heading">Add Expense</h1>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }} className="space-y-6">
        {/* Basic info */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-white font-semibold">Expense Details</h2>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Title *</label>
            <input className="input-field" placeholder="e.g., Hotel Stay" value={form.title}
              onChange={e => setForm({...form, title: e.target.value})} required />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Amount *</label>
              <input className="input-field" type="number" step="0.01" min="0" placeholder="0.00"
                value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Currency</label>
              <select className="input-field" value={form.currency} onChange={e => setForm({...form, currency: e.target.value})}>
                {currencies?.map(c => <option key={c.id} value={c.id}>{c.code} ({c.symbol})</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Paid By *</label>
              <select className="input-field" value={form.paid_by} onChange={e => setForm({...form, paid_by: e.target.value})}>
                {activeMembers.map((m: GroupMembership) => (
                  <option key={m.user.id} value={m.user.id}>{m.user.full_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Date *</label>
              <input className="input-field" type="date" value={form.expense_date}
                onChange={e => setForm({...form, expense_date: e.target.value})} required />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Category</label>
            <select className="input-field" value={form.category} onChange={e => setForm({...form, category: e.target.value})}>
              <option value="">Select category</option>
              {['Food', 'Travel', 'Accommodation', 'Entertainment', 'Shopping', 'Utilities', 'Other'].map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Notes</label>
            <textarea className="input-field resize-none h-20" placeholder="Optional notes..."
              value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} />
          </div>
        </div>

        {/* Split type */}
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-white font-semibold">How to Split</h2>
          <div className="grid grid-cols-2 gap-2">
            {SPLIT_TYPES.map(st => (
              <button
                key={st.value} type="button"
                onClick={() => setForm({...form, split_type: st.value as SplitType})}
                className={`p-3 rounded-xl border text-left transition-all ${
                  form.split_type === st.value
                    ? 'bg-primary-600/20 border-primary-500/50 text-white'
                    : 'bg-white/3 border-white/10 text-slate-400 hover:border-white/20'
                }`}
              >
                <p className="font-medium text-sm">{st.label}</p>
                <p className="text-xs mt-0.5 opacity-70">{st.desc}</p>
              </button>
            ))}
          </div>

          {/* Split details for non-EQUAL */}
          {form.split_type !== 'EQUAL' && activeMembers.length > 0 && (
            <div className="space-y-2 mt-4">
              <p className="text-slate-400 text-sm font-medium">Split Details</p>
              {activeMembers.map((member: GroupMembership) => {
                const split = splits.find(s => s.user_id === member.user.id);
                return (
                  <div key={member.user.id} className="flex items-center gap-3 bg-white/3 rounded-xl p-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-accent-500 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                      {member.user.full_name[0]}
                    </div>
                    <span className="text-slate-300 text-sm flex-1">{member.user.full_name}</span>
                    {form.split_type === 'PERCENTAGE' && (
                      <input type="number" min="0" max="100" step="0.1"
                        className="w-24 input-field text-sm py-1.5 px-3"
                        value={split?.percentage || ''}
                        onChange={e => updateSplit(member.user.id, 'percentage', e.target.value)}
                        placeholder="%" />
                    )}
                    {form.split_type === 'EXACT' && (
                      <input type="number" min="0" step="0.01"
                        className="w-28 input-field text-sm py-1.5 px-3"
                        value={split?.amount || ''}
                        onChange={e => updateSplit(member.user.id, 'amount', e.target.value)}
                        placeholder="Amount" />
                    )}
                    {form.split_type === 'SHARES' && (
                      <input type="number" min="1" step="1"
                        className="w-20 input-field text-sm py-1.5 px-3"
                        value={split?.units || '1'}
                        onChange={e => updateSplit(member.user.id, 'units', e.target.value)}
                        placeholder="Units" />
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {form.split_type === 'EQUAL' && (
            <div className="bg-primary-500/10 border border-primary-500/20 rounded-xl p-3 text-primary-300 text-sm">
              Will be split equally among {activeMembers.length} active members on the expense date.
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Link to={`/groups/${groupId}`} className="btn-secondary flex-1 text-center">Cancel</Link>
          <button type="submit" className="btn-primary flex-1 flex items-center justify-center gap-2"
            disabled={createMutation.isPending}>
            {createMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : 'Add Expense'}
          </button>
        </div>

        {createMutation.isError && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-red-400 text-sm">
            {(createMutation.error as { response?: { data?: { error?: string } } })?.response?.data?.error || 'Failed to create expense'}
          </div>
        )}
      </form>
    </div>
  );
}
