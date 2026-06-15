import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { groupsApi, settlementsApi } from '../../api/endpoints';
import { ArrowLeft, Loader2, Check, ArrowRight } from 'lucide-react';
import { format } from 'date-fns';

export default function SettlementPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const qc = useQueryClient();

  const [form, setForm] = useState({
    payer: '', receiver: '', amount: '',
    settlement_date: new Date().toISOString().split('T')[0], notes: '',
  });

  const { data: members } = useQuery({
    queryKey: ['group-members', groupId],
    queryFn: () => groupsApi.listMembers(groupId!).then(r => r.data.results),
  });

  const { data: settlements } = useQuery({
    queryKey: ['settlements', groupId],
    queryFn: () => settlementsApi.listByGroup(groupId!).then(r => r.data.results),
  });

  const createMutation = useMutation({
    mutationFn: () => settlementsApi.create(groupId!, form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['settlements', groupId] });
      qc.invalidateQueries({ queryKey: ['balances', groupId] });
      setForm({ payer: '', receiver: '', amount: '', settlement_date: new Date().toISOString().split('T')[0], notes: '' });
    },
  });

  const activeMembers = members?.filter(m => m.is_active) || [];

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <Link to={`/groups/${groupId}`} className="text-slate-500 hover:text-white text-sm flex items-center gap-1 mb-4 transition-colors w-fit">
          <ArrowLeft size={14} /> Back to Group
        </Link>
        <h1 className="section-heading">Record Settlement</h1>
        <p className="text-slate-500 text-sm mt-1">Settlements are tracked separately from expenses.</p>
      </div>

      {/* Create form */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="text-white font-semibold">New Settlement</h2>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Who Paid *</label>
            <select className="input-field" value={form.payer} onChange={e => setForm({...form, payer: e.target.value})}>
              <option value="">Select payer</option>
              {activeMembers.map(m => <option key={m.user.id} value={m.user.id}>{m.user.full_name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Who Received *</label>
            <select className="input-field" value={form.receiver} onChange={e => setForm({...form, receiver: e.target.value})}>
              <option value="">Select receiver</option>
              {activeMembers.filter(m => m.user.id !== form.payer).map(m => (
                <option key={m.user.id} value={m.user.id}>{m.user.full_name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Amount (₹) *</label>
            <input type="number" min="0" step="0.01" className="input-field" placeholder="0.00"
              value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Date *</label>
            <input type="date" className="input-field" value={form.settlement_date}
              onChange={e => setForm({...form, settlement_date: e.target.value})} />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Notes</label>
          <input className="input-field" placeholder="Optional notes..." value={form.notes}
            onChange={e => setForm({...form, notes: e.target.value})} />
        </div>

        <button
          onClick={() => createMutation.mutate()}
          disabled={!form.payer || !form.receiver || !form.amount || createMutation.isPending}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {createMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : (
            <><Check size={16} /> Record Settlement</>
          )}
        </button>

        {createMutation.isSuccess && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 text-emerald-400 text-sm text-center">
            Settlement recorded successfully!
          </div>
        )}
      </div>

      {/* History */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">Settlement History</h2>
        {!settlements?.length ? (
          <div className="glass-card p-8 text-center text-slate-500 text-sm">No settlements yet.</div>
        ) : (
          <div className="glass-card overflow-hidden">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="pl-6">From</th>
                  <th>To</th>
                  <th>Amount</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {settlements.map(s => (
                  <tr key={s.id} className="hover:bg-white/3">
                    <td className="pl-6">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center text-red-400 text-xs font-bold">
                          {s.payer.full_name[0]}
                        </div>
                        <span className="text-slate-300 text-sm">{s.payer.full_name}</span>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <ArrowRight size={12} className="text-slate-600" />
                        <div className="w-6 h-6 bg-emerald-500/20 rounded-full flex items-center justify-center text-emerald-400 text-xs font-bold">
                          {s.receiver.full_name[0]}
                        </div>
                        <span className="text-slate-300 text-sm">{s.receiver.full_name}</span>
                      </div>
                    </td>
                    <td>
                      <span className="text-emerald-400 font-semibold text-sm">
                        ₹{parseFloat(s.amount).toLocaleString('en-IN')}
                      </span>
                    </td>
                    <td className="text-slate-400 text-sm">
                      {format(new Date(s.settlement_date), 'MMM d, yyyy')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
