import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Users, ArrowUpRight, Search, Loader2, X, Check } from 'lucide-react';
import { groupsApi } from '../../api/endpoints';
import { format } from 'date-fns';

function CreateGroupModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({ name: '', description: '' });
  const qc = useQueryClient();

  const createMutation = useMutation({
    mutationFn: () => groupsApi.create(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['groups'] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass-card p-6 w-full max-w-md animate-slide-up">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Create New Group</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Group Name *</label>
            <input
              className="input-field"
              placeholder="e.g., Goa Trip 2024"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
            <textarea
              className="input-field resize-none h-24"
              placeholder="Optional description..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" className="btn-primary flex-1 flex items-center justify-center gap-2"
              disabled={createMutation.isPending}>
              {createMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : (
                <><Check size={16} /> Create Group</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function GroupsPage() {
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);

  const { data: groups, isLoading } = useQuery({
    queryKey: ['groups'],
    queryFn: () => groupsApi.list().then(r => r.data.results),
  });

  const filtered = groups?.filter(g =>
    g.name.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      {showCreate && <CreateGroupModal onClose={() => setShowCreate(false)} />}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="section-heading">Groups</h1>
          <p className="text-slate-500 text-sm mt-1">Manage your expense-sharing groups</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> New Group
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field pl-10"
          placeholder="Search groups..."
        />
      </div>

      {/* Groups grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1,2,3,4,5,6].map(i => <div key={i} className="glass-card p-6 h-44 shimmer" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-card p-16 text-center">
          <Users size={40} className="text-slate-600 mx-auto mb-4" />
          <h3 className="text-white font-semibold">
            {search ? 'No groups match your search' : 'No groups yet'}
          </h3>
          <p className="text-slate-500 mt-2">
            {search ? 'Try a different search term' : 'Create your first group to get started'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((group, idx) => (
            <Link
              key={group.id}
              to={`/groups/${group.id}`}
              className="glass-card-hover p-6 group animate-slide-up"
              style={{ animationDelay: `${idx * 0.05}s` }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-primary-900/30">
                  {group.name[0]}
                </div>
                <ArrowUpRight size={16} className="text-slate-600 group-hover:text-primary-400 transition-colors" />
              </div>

              <h3 className="text-white font-bold text-lg leading-tight">{group.name}</h3>
              {group.description && (
                <p className="text-slate-500 text-sm mt-1.5 line-clamp-2">{group.description}</p>
              )}

              <div className="flex items-center gap-4 mt-5 pt-4 border-t border-white/5">
                <div className="flex items-center gap-1.5 text-slate-500 text-xs">
                  <Users size={12} /> {group.member_count} members
                </div>
                <div className="flex items-center gap-1.5 text-slate-500 text-xs">
                  <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
                  {group.current_user_membership?.role}
                </div>
                <div className="ml-auto text-slate-600 text-xs">
                  {format(new Date(group.created_at), 'MMM d')}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
