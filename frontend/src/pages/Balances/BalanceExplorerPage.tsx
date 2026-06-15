import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { balancesApi, aiApi } from '../../api/endpoints';
import { ArrowLeft, TrendingUp, TrendingDown, Scale, Sparkles, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { format } from 'date-fns';
import clsx from 'clsx';
import { useAuthStore } from '../../store/authStore';

export default function BalanceExplorerPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const { user } = useAuthStore();
  const [selectedUser, setSelectedUser] = useState(user?.id || '');
  const [showExpenses, setShowExpenses] = useState(true);
  const [aiExplanation, setAiExplanation] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);

  const { data: groupBalances, isLoading: balancesLoading } = useQuery({
    queryKey: ['balances', groupId],
    queryFn: () => balancesApi.groupBalances(groupId!).then(r => r.data),
  });

  const { data: simplified } = useQuery({
    queryKey: ['balances-simplified', groupId],
    queryFn: () => balancesApi.simplifiedSettlements(groupId!).then(r => r.data),
  });

  const { data: explanation, isLoading: explanationLoading } = useQuery({
    queryKey: ['balance-explain', groupId, selectedUser],
    queryFn: () => balancesApi.explainBalance(groupId!, selectedUser).then(r => r.data),
    enabled: !!selectedUser,
  });

  const handleAiExplain = async () => {
    setAiLoading(true);
    try {
      const res = await aiApi.explainBalance(groupId!, selectedUser);
      setAiExplanation(res.data.explanation);
    } catch {
      setAiExplanation('AI explanation not available at this time.');
    }
    setAiLoading(false);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <Link to={`/groups/${groupId}`} className="text-slate-500 hover:text-white text-sm flex items-center gap-1 mb-4 transition-colors w-fit">
          <ArrowLeft size={14} /> Back to Group
        </Link>
        <div className="flex items-center gap-3">
          <Scale size={24} className="text-primary-400" />
          <h1 className="section-heading">Balance Explorer</h1>
        </div>
        <p className="text-slate-500 text-sm mt-1">Every balance is fully explainable — no magic numbers.</p>
      </div>

      {/* Group overview */}
      {balancesLoading ? (
        <div className="h-40 glass-card shimmer" />
      ) : (
        <div className="glass-card p-6">
          <h2 className="text-white font-semibold mb-4">Group Balances</h2>
          <div className="space-y-3">
            {groupBalances?.balances.map(b => (
              <button
                key={b.user_id}
                onClick={() => setSelectedUser(b.user_id)}
                className={clsx(
                  'w-full flex items-center gap-3 p-3 rounded-xl transition-all',
                  selectedUser === b.user_id
                    ? 'bg-primary-600/20 border border-primary-500/30'
                    : 'bg-white/3 hover:bg-white/5 border border-transparent'
                )}
              >
                <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
                  {b.user_name[0]}
                </div>
                <div className="flex-1 text-left">
                  <p className="text-white font-medium text-sm">{b.user_name}</p>
                  <p className="text-slate-500 text-xs">{b.email}</p>
                </div>
                <div className="text-right">
                  <p className={clsx(
                    'font-bold text-lg',
                    parseFloat(b.net_balance) > 0 ? 'text-emerald-400' :
                    parseFloat(b.net_balance) < 0 ? 'text-red-400' : 'text-slate-400'
                  )}>
                    {parseFloat(b.net_balance) > 0 ? '+' : ''}₹{Math.abs(parseFloat(b.net_balance)).toFixed(2)}
                  </p>
                  <p className={clsx(
                    'text-xs capitalize',
                    b.status === 'creditor' ? 'text-emerald-500' :
                    b.status === 'debtor' ? 'text-red-500' : 'text-slate-500'
                  )}>
                    {b.status}
                  </p>
                </div>
                {parseFloat(b.net_balance) > 0 ? <TrendingUp size={16} className="text-emerald-400" /> :
                 parseFloat(b.net_balance) < 0 ? <TrendingDown size={16} className="text-red-400" /> : null}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Simplified settlements */}
      {simplified && simplified.transactions.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-white font-semibold mb-4">
            Settle Up — {simplified.transaction_count} transaction{simplified.transaction_count !== 1 ? 's' : ''} needed
          </h2>
          <div className="space-y-2">
            {simplified.transactions.map((t, i) => (
              <div key={i} className="flex items-center gap-3 bg-white/3 rounded-xl p-4">
                <div className="w-8 h-8 bg-red-500/20 rounded-lg flex items-center justify-center text-red-400 font-bold text-sm">
                  {t.from_user.full_name[0]}
                </div>
                <div className="flex-1">
                  <span className="text-white font-medium text-sm">{t.from_user.full_name}</span>
                  <span className="text-slate-500 text-sm mx-2">pays</span>
                  <span className="text-white font-medium text-sm">{t.to_user.full_name}</span>
                </div>
                <span className="text-emerald-400 font-bold text-lg">₹{t.amount}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explainability section */}
      {selectedUser && (
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-white font-semibold">
              Balance Explanation — {explanation?.user_name}
            </h2>
            <button
              onClick={handleAiExplain}
              disabled={aiLoading}
              className="btn-secondary flex items-center gap-2 text-sm py-2"
            >
              {aiLoading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
              AI Explain
            </button>
          </div>

          {aiExplanation && (
            <div className="bg-primary-500/10 border border-primary-500/20 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles size={14} className="text-primary-400" />
                <span className="text-primary-300 text-xs font-medium">AI Explanation (Read-only suggestion)</span>
              </div>
              <p className="text-slate-300 text-sm">{aiExplanation}</p>
            </div>
          )}

          {explanationLoading ? (
            <div className="h-24 shimmer rounded-xl" />
          ) : explanation && (
            <>
              {/* Summary */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center">
                  <p className="text-slate-400 text-xs">You Are Owed</p>
                  <p className="text-emerald-400 font-bold text-xl mt-1">₹{parseFloat(explanation.you_are_owed).toFixed(2)}</p>
                </div>
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-center">
                  <p className="text-slate-400 text-xs">You Owe</p>
                  <p className="text-red-400 font-bold text-xl mt-1">₹{parseFloat(explanation.you_owe).toFixed(2)}</p>
                </div>
                <div className={clsx(
                  'border rounded-xl p-4 text-center',
                  parseFloat(explanation.net_balance) >= 0
                    ? 'bg-emerald-500/10 border-emerald-500/20'
                    : 'bg-red-500/10 border-red-500/20'
                )}>
                  <p className="text-slate-400 text-xs">Net Balance</p>
                  <p className={clsx(
                    'font-bold text-xl mt-1',
                    parseFloat(explanation.net_balance) >= 0 ? 'text-emerald-400' : 'text-red-400'
                  )}>
                    {parseFloat(explanation.net_balance) >= 0 ? '+' : ''}₹{parseFloat(explanation.net_balance).toFixed(2)}
                  </p>
                </div>
              </div>

              {/* Expense breakdown */}
              <button
                onClick={() => setShowExpenses(!showExpenses)}
                className="flex items-center justify-between w-full text-white font-medium py-2"
              >
                <span>Expense Breakdown ({explanation.expense_breakdown.length})</span>
                {showExpenses ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              {showExpenses && (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {explanation.expense_breakdown.map((exp) => (
                    <div key={exp.expense_id} className={clsx(
                      'flex items-center gap-3 p-3 rounded-xl border',
                      exp.direction === 'YOU_PAID'
                        ? 'bg-emerald-500/5 border-emerald-500/15'
                        : 'bg-red-500/5 border-red-500/15'
                    )}>
                      <div className="flex-1 min-w-0">
                        <p className="text-white text-sm font-medium truncate">{exp.title}</p>
                        <p className="text-slate-500 text-xs">{format(new Date(exp.expense_date), 'MMM d, yyyy')}</p>
                      </div>
                      <div className="text-right">
                        <p className={clsx(
                          'font-semibold text-sm',
                          exp.direction === 'YOU_PAID' ? 'text-emerald-400' : 'text-red-400'
                        )}>
                          {exp.direction === 'YOU_PAID' ? '+' : '-'}₹{
                            exp.direction === 'YOU_PAID'
                              ? parseFloat(exp.others_owe_you || '0').toFixed(2)
                              : parseFloat(exp.your_share).toFixed(2)
                          }
                        </p>
                        <p className="text-slate-600 text-xs">
                          {exp.direction === 'YOU_PAID' ? 'you paid' : `paid by ${exp.paid_by}`}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
