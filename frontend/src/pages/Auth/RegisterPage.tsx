import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, EyeOff, Wallet, ArrowRight, Loader2, CheckCircle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../../api/endpoints';

export default function RegisterPage() {
  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '',
    username: '', password: '', password_confirm: '',
  });
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState(false);


  const registerMutation = useMutation({
    mutationFn: () => authApi.register(form),
    onSuccess: () => setSuccess(true),
    onError: (err: any) => {
      const data = err?.response?.data?.details || {};
      setError(data);
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError({ ...error, [e.target.name]: '' });
  };

  if (success) {
    return (
      <div className="min-h-screen auth-bg flex items-center justify-center p-4">
        <div className="glass-card p-10 max-w-md w-full text-center animate-slide-up">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-500/20 rounded-2xl mb-4">
            <CheckCircle size={32} className="text-emerald-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Check your email</h2>
          <p className="text-slate-400 mb-6">
            We sent a verification link to <strong className="text-white">{form.email}</strong>.
            Click it to activate your account.
          </p>
          <Link to="/login" className="btn-primary inline-flex items-center gap-2">
            Go to Login <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen auth-bg flex items-center justify-center p-4">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-600/15 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-accent-600/15 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-lg relative">
        <div className="text-center mb-8 animate-slide-up">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-accent-500 rounded-2xl shadow-2xl shadow-primary-900/50 mb-4">
            <Wallet size={28} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Create account</h1>
          <p className="text-slate-400 mt-2">Start managing shared expenses</p>
        </div>

        <div className="glass-card p-8 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <form onSubmit={(e) => { e.preventDefault(); registerMutation.mutate(); }} className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              {['first_name', 'last_name'].map((field) => (
                <div key={field}>
                  <label className="block text-sm font-medium text-slate-300 mb-2 capitalize">
                    {field.replace('_', ' ')}
                  </label>
                  <input
                    name={field}
                    value={(form as any)[field]}
                    onChange={handleChange}
                    className="input-field"
                    placeholder={field === 'first_name' ? 'Aisha' : 'Khan'}
                    required
                  />
                  {error[field] && <p className="text-red-400 text-xs mt-1">{error[field]}</p>}
                </div>
              ))}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
              <input
                name="email" type="email" value={form.email}
                onChange={handleChange} className="input-field"
                placeholder="aisha@example.com" required
              />
              {error.email && <p className="text-red-400 text-xs mt-1">{error.email}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Username</label>
              <input
                name="username" value={form.username}
                onChange={handleChange} className="input-field"
                placeholder="aisha_k" required
              />
              {error.username && <p className="text-red-400 text-xs mt-1">{error.username}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Password</label>
              <div className="relative">
                <input
                  name="password" type={showPass ? 'text' : 'password'}
                  value={form.password} onChange={handleChange}
                  className="input-field pr-12" placeholder="Minimum 8 characters" required
                />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                  {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {error.password && <p className="text-red-400 text-xs mt-1">{error.password}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Confirm Password</label>
              <input
                name="password_confirm" type="password" value={form.password_confirm}
                onChange={handleChange} className="input-field" placeholder="Repeat password" required
              />
              {error.password_confirm && <p className="text-red-400 text-xs mt-1">{error.password_confirm}</p>}
            </div>

            <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2"
              disabled={registerMutation.isPending}>
              {registerMutation.isPending ? <Loader2 size={18} className="animate-spin" /> : (
                <><span>Create Account</span><ArrowRight size={18} /></>
              )}
            </button>
          </form>

          <p className="text-center text-slate-500 text-sm mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
