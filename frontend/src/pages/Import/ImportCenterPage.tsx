import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { importsApi, groupsApi } from '../../api/endpoints';
import {
  Upload, FileText, AlertTriangle, CheckCircle, Clock,
  Download, ArrowRight, Plus, X, Loader2,
} from 'lucide-react';
import { format } from 'date-fns';
import clsx from 'clsx';
import type { ImportStatus } from '../../types';

const STATUS_CONFIG: Record<ImportStatus, { label: string; color: string; icon: any }> = {
  PENDING: { label: 'Pending', color: 'badge-info', icon: Clock },
  PARSING: { label: 'Parsing', color: 'badge-info', icon: Loader2 },
  AWAITING_APPROVAL: { label: 'Needs Review', color: 'badge-warning', icon: AlertTriangle },
  APPROVED: { label: 'Approved', color: 'badge-success', icon: CheckCircle },
  REJECTED: { label: 'Rejected', color: 'badge-error', icon: X },
  COMPLETED: { label: 'Completed', color: 'badge-success', icon: CheckCircle },
  FAILED: { label: 'Failed', color: 'badge-error', icon: X },
};

function UploadModal({ groups, onClose }: { groups: any[]; onClose: () => void }) {
  const [groupId, setGroupId] = useState(groups[0]?.id || '');
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();
  const navigate = useNavigate();

  const uploadMutation = useMutation({
    mutationFn: () => importsApi.upload(groupId, file!),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['imports'] });
      onClose();
      navigate(`/import/${res.data.id}/review`);
    },
  });

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped?.name.endsWith('.csv')) setFile(dropped);
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass-card p-6 w-full max-w-lg animate-slide-up">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Import Expenses</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors"><X size={20} /></button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Target Group *</label>
            <select className="input-field" value={groupId} onChange={e => setGroupId(e.target.value)}>
              {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
            </select>
          </div>

          <div
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            className={clsx(
              'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all',
              dragging ? 'border-primary-500 bg-primary-500/10' : 'border-white/10 hover:border-white/20 hover:bg-white/3'
            )}
          >
            <input ref={fileRef} type="file" accept=".csv" className="hidden"
              onChange={e => setFile(e.target.files?.[0] || null)} />
            {file ? (
              <div>
                <FileText size={32} className="text-primary-400 mx-auto mb-2" />
                <p className="text-white font-medium">{file.name}</p>
                <p className="text-slate-500 text-sm">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            ) : (
              <div>
                <Upload size={32} className="text-slate-600 mx-auto mb-3" />
                <p className="text-white font-medium">Drop CSV file here</p>
                <p className="text-slate-500 text-sm mt-1">or click to browse • Max 10MB</p>
              </div>
            )}
          </div>

          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 text-amber-300 text-xs">
            Your original file will never be modified. All anomalies require your review before import.
          </div>

          <div className="flex gap-3">
            <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button
              onClick={() => uploadMutation.mutate()}
              disabled={!file || !groupId || uploadMutation.isPending}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {uploadMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : (
                <><Upload size={16} /> Upload & Analyze</>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ImportCenterPage() {
  const [showUpload, setShowUpload] = useState(false);

  const { data: imports, isLoading } = useQuery({
    queryKey: ['imports'],
    queryFn: () => importsApi.list().then(r => r.data.results),
  });

  const { data: groups } = useQuery({
    queryKey: ['groups'],
    queryFn: () => groupsApi.list().then(r => r.data.results),
  });

  const handleDownloadReport = async (jobId: string, fileName: string) => {
    const res = await importsApi.downloadReport(jobId);
    const blob = new Blob([res.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `import_report_${fileName}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {showUpload && groups && <UploadModal groups={groups} onClose={() => setShowUpload(false)} />}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="section-heading">Import Center</h1>
          <p className="text-slate-500 text-sm mt-1">Import expenses from CSV with intelligent anomaly detection</p>
        </div>
        <button onClick={() => setShowUpload(true)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> New Import
        </button>
      </div>

      {/* How it works */}
      <div className="glass-card p-6">
        <h2 className="text-white font-semibold mb-4">How Import Works</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { step: '1', title: 'Upload CSV', desc: 'Original file never modified', icon: '📤' },
            { step: '2', title: 'AI Analysis', desc: '15 anomaly checks run automatically', icon: '🔍' },
            { step: '3', title: 'Review', desc: 'Approve or reject each anomaly', icon: '✅' },
            { step: '4', title: 'Import', desc: 'Only approved rows imported', icon: '✨' },
          ].map(s => (
            <div key={s.step} className="bg-white/3 rounded-xl p-4 text-center">
              <div className="text-2xl mb-2">{s.icon}</div>
              <p className="text-white font-semibold text-sm">{s.title}</p>
              <p className="text-slate-500 text-xs mt-1">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Import history */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Import History</h2>
        {isLoading ? (
          <div className="space-y-3">
            {[1,2,3].map(i => <div key={i} className="glass-card p-5 h-20 shimmer" />)}
          </div>
        ) : !imports?.length ? (
          <div 
            onClick={() => setShowUpload(true)}
            className="glass-card p-12 text-center cursor-pointer hover:bg-white/5 hover:border-white/20 transition-all duration-200 group"
          >
            <Upload size={32} className="text-slate-600 group-hover:text-primary-400 mx-auto mb-3 transition-colors" />
            <p className="text-white font-medium group-hover:text-primary-300 transition-colors">No imports yet</p>
            <p className="text-slate-500 text-sm mt-1">Click here to upload your first CSV to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {imports.map((job) => {
              const cfg = STATUS_CONFIG[job.status];
              const Icon = cfg.icon;
              return (
                <div key={job.id} className="glass-card p-5 flex items-center gap-4">
                  <div className="w-10 h-10 bg-primary-500/15 rounded-xl flex items-center justify-center flex-shrink-0">
                    <FileText size={18} className="text-primary-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-white font-medium text-sm truncate">{job.file_name}</p>
                      <span className={`badge ${cfg.color}`}>
                        <Icon size={10} className={job.status === 'PARSING' ? 'animate-spin' : ''} />
                        {cfg.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-1">
                      <span className="text-slate-500 text-xs">{format(new Date(job.created_at), 'MMM d, yyyy HH:mm')}</span>
                      <span className="text-slate-500 text-xs">{job.rows_total} rows</span>
                      {job.anomalies_count > 0 && (
                        <span className="text-amber-400 text-xs flex items-center gap-1">
                          <AlertTriangle size={10} /> {job.anomalies_count} anomalies
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {(job.status === 'AWAITING_APPROVAL') && (
                      <Link to={`/import/${job.id}/review`} className="btn-secondary text-sm py-1.5 flex items-center gap-1">
                        Review <ArrowRight size={13} />
                      </Link>
                    )}
                    {(job.status === 'COMPLETED' || job.status === 'FAILED') && (
                      <button
                        onClick={() => handleDownloadReport(job.id, job.file_name)}
                        className="btn-secondary text-sm py-1.5 flex items-center gap-1"
                      >
                        <Download size={13} /> Report
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
