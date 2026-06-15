import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { auditApi } from '../../api/endpoints';
import { ClipboardList } from 'lucide-react';
import { format } from 'date-fns';
import clsx from 'clsx';
import type { AuditLog, PaginatedResponse } from '../../types';

const ACTION_COLORS: Record<string, string> = {
  CREATE: 'badge-success',
  UPDATE: 'badge-info',
  DELETE: 'badge-error',
  SOFT_DELETE: 'badge-error',
  IMPORT: 'badge-warning',
  SETTLEMENT: 'badge-success',
  LOGIN: 'badge-info',
  LOGOUT: 'badge-info',
  MEMBER_JOIN: 'badge-success',
  MEMBER_LEAVE: 'badge-warning',
};

export default function AuditHistoryPage() {
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');

  const { data, isLoading } = useQuery<PaginatedResponse<AuditLog>>({
    queryKey: ['audit', page, actionFilter],
    queryFn: () => auditApi.list({ page, action: actionFilter || undefined }).then(r => r.data),
    placeholderData: (prev) => prev,
  });

  const totalPages = data ? Math.ceil(data.count / 20) : 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <ClipboardList size={24} className="text-primary-400" />
            <h1 className="section-heading">Audit History</h1>
          </div>
          <p className="text-slate-500 text-sm mt-1">
            Complete, immutable trail of every action. Nothing is ever hidden or deleted.
          </p>
        </div>
        {data && (
          <div className="badge badge-info">{data.count} total entries</div>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        {['', 'CREATE', 'UPDATE', 'DELETE', 'IMPORT', 'SETTLEMENT', 'LOGIN'].map(action => (
          <button
            key={action || 'all'}
            onClick={() => { setActionFilter(action); setPage(1); }}
            className={clsx(
              'px-4 py-1.5 rounded-full text-sm font-medium transition-all',
              actionFilter === action
                ? 'bg-primary-600 text-white'
                : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
            )}
          >
            {action || 'All'}
          </button>
        ))}
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2">
          {[1,2,3,4,5].map(i => <div key={i} className="h-16 glass-card shimmer" />)}
        </div>
      ) : !data?.results.length ? (
        <div className="glass-card p-12 text-center">
          <ClipboardList size={32} className="text-slate-600 mx-auto mb-3" />
          <p className="text-white font-medium">No audit logs</p>
          <p className="text-slate-500 text-sm mt-1">Actions will appear here as you use the app</p>
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <table className="data-table">
            <thead>
              <tr>
                <th className="pl-6">Action</th>
                <th>Resource</th>
                <th>Actor</th>
                <th>IP</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((log: AuditLog) => (
                <tr key={log.id} className="hover:bg-white/3 transition-colors">
                  <td className="pl-6">
                    <span className={`badge ${ACTION_COLORS[log.action] || 'badge-info'}`}>
                      {log.action}
                    </span>
                  </td>
                  <td>
                    <div>
                      <p className="text-slate-300 text-sm font-medium">{log.resource_type}</p>
                      {log.resource_repr && (
                        <p className="text-slate-600 text-xs truncate max-w-48">{log.resource_repr}</p>
                      )}
                    </div>
                  </td>
                  <td>
                    {log.actor ? (
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-gradient-to-br from-primary-500 to-accent-500 rounded-full flex items-center justify-center text-white text-xs">
                          {log.actor.full_name[0]}
                        </div>
                        <span className="text-slate-300 text-sm">{log.actor.full_name}</span>
                      </div>
                    ) : <span className="text-slate-600 text-sm">System</span>}
                  </td>
                  <td className="text-slate-500 text-xs font-mono">{log.ip_address || '—'}</td>
                  <td className="text-slate-400 text-sm">
                    {format(new Date(log.created_at), 'MMM d, HH:mm')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-secondary px-4 py-2 text-sm disabled:opacity-30"
          >
            Previous
          </button>
          <span className="text-slate-400 text-sm">Page {page} of {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="btn-secondary px-4 py-2 text-sm disabled:opacity-30"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
