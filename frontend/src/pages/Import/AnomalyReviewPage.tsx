import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { importsApi, aiApi } from '../../api/endpoints';
import {
  AlertTriangle, CheckCircle, XCircle, Info, Loader2,
  ChevronDown, ChevronRight, Sparkles, Play, ArrowLeft,
} from 'lucide-react';
import clsx from 'clsx';
import type { ImportAnomaly, AnomalySeverity } from '../../types';

const SEVERITY_CONFIG: Record<AnomalySeverity, { icon: any; color: string; bg: string }> = {
  ERROR: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
  WARNING: { icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
  INFO: { icon: Info, color: 'text-sky-400', bg: 'bg-sky-500/10 border-sky-500/20' },
};

function AnomalyCard({ anomaly, jobId }: { anomaly: ImportAnomaly; jobId: string }) {
  const [expanded, setExpanded] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const qc = useQueryClient();

  const cfg = SEVERITY_CONFIG[anomaly.severity];
  const SeverityIcon = cfg.icon;

  const resolveMutation = useMutation({
    mutationFn: (action: 'APPROVE' | 'REJECT') =>
      importsApi.resolveAnomaly(jobId, anomaly.id, action),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['import-anomalies', jobId] }),
  });

  const handleAiSuggest = async () => {
    setAiLoading(true);
    try {
      const res = await aiApi.suggestResolution(anomaly.id);
      setAiSuggestion(res.data.suggested_action);
    } catch {
      setAiSuggestion('AI not available.');
    }
    setAiLoading(false);
  };

  const isResolved = anomaly.status !== 'PENDING';

  return (
    <div className={clsx('border rounded-xl overflow-hidden transition-all', cfg.bg, isResolved && 'opacity-70')}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-4 text-left"
      >
        <SeverityIcon size={16} className={cfg.color} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={clsx('text-xs font-semibold px-2 py-0.5 rounded-full', cfg.bg, cfg.color)}>
              {anomaly.severity}
            </span>
            <span className="text-slate-400 text-xs">Row {anomaly.row_number}</span>
            <span className="text-slate-500 text-xs">•</span>
            <span className="text-slate-500 text-xs">{anomaly.anomaly_type.replace(/_/g, ' ')}</span>
          </div>
          <p className="text-white text-sm font-medium mt-1 line-clamp-1">{anomaly.description}</p>
        </div>
        {isResolved && (
          <span className={clsx('badge flex-shrink-0',
            anomaly.status === 'APPROVED' ? 'badge-success' : 'badge-error'
          )}>
            {anomaly.status === 'APPROVED' ? <CheckCircle size={10} /> : <XCircle size={10} />}
            {anomaly.status}
          </span>
        )}
        {expanded ? <ChevronDown size={14} className="text-slate-400 flex-shrink-0" /> :
          <ChevronRight size={14} className="text-slate-400 flex-shrink-0" />}
      </button>

      {expanded && (
        <div className="border-t border-white/5 p-4 space-y-3">
          {/* Raw data */}
          <div>
            <p className="text-slate-400 text-xs font-medium mb-1">Raw CSV Row</p>
            <div className="bg-black/30 rounded-lg p-3 overflow-x-auto">
              <pre className="text-slate-300 text-xs whitespace-pre-wrap">
                {JSON.stringify(anomaly.raw_data, null, 2)}
              </pre>
            </div>
          </div>

          {/* Recommendation */}
          <div className="bg-white/3 rounded-lg p-3">
            <p className="text-slate-400 text-xs font-medium mb-1">Recommendation</p>
            <p className="text-slate-300 text-sm">{anomaly.recommendation}</p>
          </div>

          {/* AI suggestion */}
          {aiSuggestion && (
            <div className="bg-primary-500/10 border border-primary-500/20 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-1">
                <Sparkles size={12} className="text-primary-400" />
                <p className="text-primary-300 text-xs font-medium">AI Suggestion (Read-only)</p>
              </div>
              <p className="text-slate-300 text-sm">{aiSuggestion}</p>
            </div>
          )}

          {/* Actions */}
          {!isResolved && (
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => resolveMutation.mutate('APPROVE')}
                disabled={resolveMutation.isPending}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 text-sm font-medium border border-emerald-500/30 transition-all"
              >
                {resolveMutation.isPending ? <Loader2 size={13} className="animate-spin" /> : <CheckCircle size={13} />}
                Approve Row
              </button>
              <button
                onClick={() => resolveMutation.mutate('REJECT')}
                disabled={resolveMutation.isPending}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 text-sm font-medium border border-red-500/30 transition-all"
              >
                <XCircle size={13} /> Skip Row
              </button>
              <button
                onClick={handleAiSuggest}
                disabled={aiLoading}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-primary-500/20 hover:bg-primary-500/30 text-primary-400 text-sm font-medium border border-primary-500/30 transition-all ml-auto"
              >
                {aiLoading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                AI Suggest
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AnomalyReviewPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [filter, setFilter] = useState<string>('all');

  const { data: job } = useQuery({
    queryKey: ['import-job', jobId],
    queryFn: () => importsApi.get(jobId!).then(r => r.data),
    refetchInterval: 3000,
  });

  const { data: anomalies, isLoading } = useQuery({
    queryKey: ['import-anomalies', jobId],
    queryFn: () => importsApi.getAnomalies(jobId!).then(r => r.data.results),
  });

  const executeMutation = useMutation({
    mutationFn: () => importsApi.execute(jobId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['imports'] });
      navigate('/import');
    },
  });

  const filteredAnomalies = anomalies?.filter(a => {
    if (filter === 'all') return true;
    if (filter === 'pending') return a.status === 'PENDING';
    return a.severity === filter.toUpperCase();
  }) || [];

  const pendingErrors = anomalies?.filter(a => a.severity === 'ERROR' && a.status === 'PENDING').length || 0;
  const pendingWarnings = anomalies?.filter(a => a.severity === 'WARNING' && a.status === 'PENDING').length || 0;

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <button onClick={() => navigate('/import')} className="text-slate-500 hover:text-white text-sm flex items-center gap-1 mb-4 transition-colors">
          <ArrowLeft size={14} /> Back to Import Center
        </button>
        <h1 className="section-heading">Anomaly Review</h1>
        <p className="text-slate-500 text-sm mt-1">
          Review and resolve detected anomalies before importing. Your original file is unchanged.
        </p>
      </div>

      {/* Job summary */}
      {job && (
        <div className="glass-card p-5 flex flex-wrap items-center gap-4">
          <div>
            <p className="text-slate-400 text-xs">File</p>
            <p className="text-white font-medium text-sm">{job.file_name}</p>
          </div>
          <div>
            <p className="text-slate-400 text-xs">Status</p>
            <p className="text-amber-400 font-medium text-sm">{job.status.replace('_', ' ')}</p>
          </div>
          <div>
            <p className="text-slate-400 text-xs">Total Rows</p>
            <p className="text-white font-medium text-sm">{job.rows_total}</p>
          </div>
          <div className="flex gap-3">
            {pendingErrors > 0 && (
              <span className="badge badge-error">{pendingErrors} errors pending</span>
            )}
            {pendingWarnings > 0 && (
              <span className="badge badge-warning">{pendingWarnings} warnings pending</span>
            )}
          </div>
          <div className="ml-auto flex gap-2">
            <button
              onClick={() => executeMutation.mutate()}
              disabled={pendingErrors > 0 || executeMutation.isPending}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm transition-all',
                pendingErrors > 0
                  ? 'bg-white/5 text-slate-500 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/30'
              )}
              title={pendingErrors > 0 ? `Resolve ${pendingErrors} errors first` : 'Execute Import'}
            >
              {executeMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
              Execute Import
            </button>
          </div>
        </div>
      )}

      {pendingErrors > 0 && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-red-300 text-sm flex items-center gap-2">
          <AlertTriangle size={14} /> Resolve all {pendingErrors} ERROR anomalies before executing the import.
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {['all', 'pending', 'error', 'warning', 'info'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={clsx(
              'px-4 py-1.5 rounded-full text-sm font-medium transition-all capitalize',
              filter === f
                ? 'bg-primary-600 text-white'
                : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
            )}
          >
            {f}
            {f === 'all' && ` (${anomalies?.length || 0})`}
            {f === 'pending' && ` (${anomalies?.filter(a => a.status === 'PENDING').length || 0})`}
          </button>
        ))}
      </div>

      {/* Anomalies */}
      {isLoading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="h-16 glass-card shimmer" />)}
        </div>
      ) : filteredAnomalies.length === 0 ? (
        <div className="glass-card p-10 text-center">
          <CheckCircle size={32} className="text-emerald-400 mx-auto mb-3" />
          <p className="text-white font-medium">No anomalies to show</p>
          <p className="text-slate-500 text-sm mt-1">
            {filter === 'all' ? 'No anomalies were detected' : 'No anomalies match this filter'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredAnomalies.map(a => (
            <AnomalyCard key={a.id} anomaly={a} jobId={jobId!} />
          ))}
        </div>
      )}
    </div>
  );
}
