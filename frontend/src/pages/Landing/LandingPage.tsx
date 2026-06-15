import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import {
  ArrowRight,
  Layers,
  TrendingUp
} from 'lucide-react';

export default function LandingPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmitWaitlist = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setIsSubmitted(true);
      setTimeout(() => {
        setIsSubmitted(false);
        setEmail('');
      }, 3000);
    }
  };

  return (
    <div className="bg-white text-slate-800 min-h-screen font-sans antialiased overflow-x-hidden selection:bg-[#8b5cf6] selection:text-white">

      {/* ─── Hero Spotlight Background ─── */}
      <div className="absolute top-[0px] left-1/2 -translate-x-1/2 w-full max-w-7xl h-[800px] pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[25%] left-[50%] -translate-x-1/2 -translate-y-1/2 w-[75%] h-[60%] rounded-full bg-gradient-to-br from-[#d8b4fe]/50 via-[#c7d2fe]/30 to-transparent blur-[130px] opacity-80" />
        <div className="absolute top-[35%] left-[50%] -translate-x-1/2 -translate-y-1/2 w-[50%] h-[40%] rounded-full bg-gradient-to-tr from-[#a78bfa]/40 via-[#8b5cf6]/20 to-transparent blur-[100px] opacity-70" />
      </div>

      {/* ─── Header Navigation ─── */}
      <header className="relative max-w-7xl mx-auto px-6 py-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#8b5cf6] to-[#a78bfa] flex items-center justify-center shadow-md">
            <Layers className="w-4.5 h-4.5 text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight text-slate-900">Simplified</span>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-[13px] font-medium text-slate-500 tracking-wide">
          <a href="#home" className="hover:text-slate-900 transition-colors">Home</a>
          <a href="#about" className="hover:text-slate-900 transition-colors">About</a>
          <a href="#features" className="hover:text-slate-900 transition-colors">Features</a>
          <a href="#service" className="hover:text-slate-900 transition-colors">Service</a>
          <a href="#blog" className="hover:text-slate-900 transition-colors">Blog</a>
          <a href="#contact" className="hover:text-slate-900 transition-colors">Contact</a>
        </nav>

        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-[#8b5cf6] text-white rounded-lg px-5 py-2.5 text-xs font-bold hover:bg-[#7c3aed] transition shadow-md shadow-purple-500/10"
            >
              Get App
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/login')}
                className="bg-transparent hover:bg-slate-100 text-[#8b5cf6] rounded-full px-4 py-2 text-xs font-bold transition"
              >
                Sign In
              </button>
              <button
                onClick={() => navigate('/register')}
                className="bg-[#8b5cf6] text-white rounded-lg px-6 py-2.5 text-xs font-bold hover:bg-[#7c3aed] transition shadow-md shadow-purple-500/10"
              >
                Get App
              </button>
            </div>
          )}
        </div>
      </header>

      {/* ─── Hero Section ─── */}
      <section className="relative max-w-7xl mx-auto px-6 pt-12 pb-16 z-10 flex flex-col items-center text-center">

        {/* Giant Title "Simplified" */}
        <h1 className="text-[100px] sm:text-[140px] font-black tracking-tighter text-[#1e1b4b] leading-[0.9] mb-2 select-none">
          Simplified
        </h1>

        {/* Slanted Pill "Download App" */}
        <div className="bg-slate-950 text-white text-xs font-bold uppercase tracking-widest px-8 py-3.5 rounded-xl shadow-xl -rotate-2 hover:rotate-0 transition-all duration-500 mb-12 inline-block select-none cursor-pointer hover:scale-110" onClick={() => navigate('/register')}>
          Download App
        </div>

        {/* Hero Central Graphic & Floating Side Text */}
        <div className="relative w-full max-w-6xl h-[500px] sm:h-[650px] flex items-center justify-center mt-2">

          {/* Floating Text Left */}
          <div className="hidden lg:block absolute left-[2%] top-[10%] max-w-[240px] text-left">
            <p className="text-[13px] text-slate-500 leading-relaxed font-medium">
              This streamlined approach provides an immediate, high-level view of your spending patterns, allowing you to identify trends and adjust your habits in real time.
            </p>
          </div>

          {/* Central smartphone mockup illustration */}
          <div className="relative z-10 w-[300px] sm:w-[420px] aspect-[1/2] select-none transform hover:scale-[1.02] transition-transform duration-700 cursor-default">
            {/* Using the existing phone mockup but we'll try to position it like the hand-held phone */}
            <img
              src="/simplified_hero_phone.png"
              alt="Simplified Phone Application"
              className="w-full h-full object-contain drop-shadow-[0_45px_65px_rgba(139,92,246,0.3)]"
            />
          </div>

          {/* Floating Text Right */}
          <div className="hidden lg:block absolute right-[2%] top-[10%] max-w-[240px] text-right">
            <p className="text-[13px] text-slate-500 leading-relaxed font-medium">
              You gain the total focus needed to prioritize your long term financial goals and make informed decisions with absolute confidence.
            </p>
          </div>

        </div>

      </section>

      {/* ─── Metrics Section (Stress-Free Expense Management) ─── */}
      <section id="metrics" className="bg-[#fcfdff] border-y border-slate-100 py-32 relative z-10">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">

          {/* Left info panel */}
          <div className="lg:col-span-12 text-center flex flex-col items-center mb-12">
            <div className="flex flex-col md:flex-row justify-between w-full items-start md:items-end mb-16 text-left">
              <div className="max-w-xl">
                <h2 className="text-4xl sm:text-5xl font-extrabold text-[#100e34] tracking-tight leading-tight mb-8">
                  Stress-Free Expense<br />Management
                </h2>
                <div className="mt-4">
                  <button className="bg-[#8b5cf6] text-white rounded-lg px-8 py-3 text-xs font-bold hover:bg-[#7c3aed] transition shadow-lg shadow-purple-500/20">
                    Know More
                  </button>
                </div>
              </div>
              
              <div className="max-w-xs mt-12 md:mt-0">
                <p className="text-slate-500 text-[14px] leading-relaxed font-medium">
                  Over 380,000 transactions tracked across different countries and currencies, giving users a reliable dashboard of expense accounts.
                </p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 hidden lg:block text-left">
             <p className="text-slate-500 text-[14px] leading-relaxed max-w-xs font-medium">
              Manage your daily expenses with ease and confidence. With everything organized in one place, you keep absolute control.
            </p>
          </div>

          {/* Right vertical stats bars panel */}
          <div className="lg:col-span-7 flex justify-end gap-5 sm:gap-10 h-[400px] sm:h-[480px] items-end">

            {/* Stat Bar 1: Global Transactions */}
            <div className="flex flex-col items-center flex-1 h-full justify-end group">
              <div className="text-left w-full pl-2 sm:pl-4 mb-2">
                <span className="text-[10px] sm:text-xs text-slate-400 font-bold uppercase tracking-wider block">Global Trans.</span>
                <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">380K</span>
              </div>
              <div className="w-full bg-[#fde8e8] hover:bg-[#fbd5d5] rounded-3xl transition-all duration-500 h-[55%] flex items-end overflow-hidden shadow-sm shadow-red-100 animate-rise">
                <div className="w-full h-full bg-gradient-to-t from-orange-400/90 to-amber-300/80 flex items-center justify-center opacity-90 group-hover:opacity-100 transition-opacity">
                  <div className="w-full h-full opacity-10 bg-[radial-gradient(circle_at_center,_#fff_1px,_transparent_1px)] bg-[size:10px_10px]" />
                </div>
              </div>
            </div>

            {/* Stat Bar 2: Savings Growth */}
            <div className="flex flex-col items-center flex-1 h-full justify-end group">
              <div className="text-left w-full pl-2 sm:pl-4 mb-2">
                <span className="text-[10px] sm:text-xs text-slate-400 font-bold uppercase tracking-wider block">Savings Growth</span>
                <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">92%</span>
              </div>
              <div className="w-full bg-[#f3e8ff] hover:bg-[#e9d5ff] rounded-3xl transition-all duration-500 h-[80%] flex items-end overflow-hidden shadow-sm shadow-purple-100 animate-rise">
                <div className="w-full h-full bg-gradient-to-t from-purple-500/90 to-indigo-400/80 flex items-center justify-center opacity-90 group-hover:opacity-100 transition-opacity">
                  <div className="w-full h-full opacity-10 bg-[radial-gradient(circle_at_center,_#fff_1px,_transparent_1px)] bg-[size:10px_10px]" />
                </div>
              </div>
            </div>

            {/* Stat Bar 3: Retention Rate */}
            <div className="flex flex-col items-center flex-1 h-full justify-end group">
              <div className="text-left w-full pl-2 sm:pl-4 mb-2">
                <span className="text-[10px] sm:text-xs text-slate-400 font-bold uppercase tracking-wider block">Retention Rate</span>
                <span className="text-2xl sm:text-3xl font-extrabold text-slate-900">82%</span>
              </div>
              <div className="w-full bg-[#e6fffa] hover:bg-[#b2f5ea] rounded-3xl transition-all duration-500 h-[100%] flex items-end overflow-hidden shadow-sm shadow-teal-100 animate-rise">
                <div className="w-full h-full bg-gradient-to-t from-[#2dd4bf] to-[#0ea5e9] flex items-center justify-center opacity-90 group-hover:opacity-100 transition-opacity">
                  <div className="w-full h-full opacity-10 bg-[radial-gradient(circle_at_center,_#fff_1px,_transparent_1px)] bg-[size:10px_10px]" />
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ─── Features Grid Section (Everything You Need to Stay in Control) ─── */}
      <section id="features" className="py-24 max-w-7xl mx-auto px-6 relative z-10">

        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-16 text-left">
          <div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#1e1b4b] tracking-tight mb-2">
              Everything You Need<br />to Stay in Control
            </h2>
            <p className="text-slate-500 text-xs max-w-md">Track shared costs, create custom splits, audit ledger history, and simplify settlements.</p>
          </div>
          <div className="mt-6 sm:mt-0">
            <button
              onClick={() => navigate('/register')}
              className="bg-[#8b5cf6] text-white rounded-full px-6 py-3 text-xs font-bold hover:bg-[#7c3aed] transition shadow-md shadow-purple-500/10 inline-flex items-center gap-1.5"
            >
              Get Started Now
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Feature Cards Grid (4 Cards: 2x2 layout) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-left">

          {/* Card 1: Daily Cost Tracking */}
          <div className="bg-[#f8fafc]/80 border border-slate-100 rounded-3xl p-8 flex flex-col justify-between transition-all duration-300 hover:shadow-lg hover:shadow-slate-100/50">
            <div className="mb-8">
              <h3 className="text-lg font-bold text-slate-900 mb-2">Daily Cost Tracking</h3>
              <p className="text-slate-500 text-xs leading-relaxed font-medium">
                Easily log and split every household expense in seconds. Always maintain a clear, chronological ledger of payments.
              </p>
            </div>

            {/* Visual: Daily Cost Chart Mockup */}
            <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm">
              <div className="flex justify-between items-center mb-6">
                <span className="text-[10px] font-bold text-slate-800 uppercase tracking-wider">Daily Costing</span>
                <div className="w-5 h-5 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center"><TrendingUp className="w-3 h-3 text-slate-400" /></div>
              </div>
              <div className="flex items-end justify-between h-[100px] pt-4 relative">
                <div className="absolute top-[-8px] left-[45%] -translate-x-1/2 bg-slate-950 text-white text-[9px] font-bold px-2 py-0.5 rounded shadow flex items-center gap-1 z-10">
                  <span>₹1,395</span>
                </div>
                {[35, 50, 40, 75, 55, 30, 45].map((val, idx) => (
                  <div key={idx} className="flex flex-col items-center flex-1">
                    <div
                      className={`w-3.5 rounded-t-sm ${idx === 3 ? 'bg-[#8b5cf6]' : 'bg-indigo-100'}`}
                      style={{ height: `${val}px` }}
                    />
                    <span className="text-[8px] text-slate-400 mt-2 font-medium">
                      {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][idx]}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Card 2: Smart Budgeting */}
          <div className="bg-[#f8fafc]/80 border border-slate-100 rounded-3xl p-8 flex flex-col justify-between transition-all duration-300 hover:shadow-lg hover:shadow-slate-100/50">
            <div className="mb-8">
              <h3 className="text-lg font-bold text-slate-900 mb-2">Smart Budgeting</h3>
              <p className="text-slate-500 text-xs leading-relaxed font-medium">
                Set active category limits and monitor allocations. Get smart notifications for spikes, duplicates, and timeline errors.
              </p>
            </div>

            {/* Visual: Budget Category Sliders */}
            <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm flex flex-col gap-3.5">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-slate-800 uppercase tracking-wider">Expense Tracker</span>
                <span className="text-[9px] font-semibold text-slate-400">All ▾</span>
              </div>
              {[
                { name: 'Groceries', val: '42%', color: 'from-orange-400 to-amber-300' },
                { name: 'Transportation', val: '32%', color: 'from-[#8b5cf6] to-[#c084fc]' },
                { name: 'Medical', val: '65%', color: 'from-emerald-400 to-teal-300' }
              ].map((bar, idx) => (
                <div key={idx} className="flex flex-col gap-1 text-left">
                  <div className="flex justify-between text-[10px] font-bold text-slate-700">
                    <span>{bar.name}</span>
                    <span>{bar.val}</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div className={`bg-gradient-to-r ${bar.color} h-full rounded-full`} style={{ width: bar.val }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Card 3: Visual Dashboard */}
          <div className="bg-[#f8fafc]/80 border border-slate-100 rounded-3xl p-8 flex flex-col justify-between transition-all duration-300 hover:shadow-lg hover:shadow-slate-100/50">
            <div className="mb-8">
              <h3 className="text-lg font-bold text-slate-900 mb-2">Visual Dashboard</h3>
              <p className="text-slate-500 text-xs leading-relaxed font-medium">
                Identify spending trends instantly. Filter historical charts to visualize contributions and balances over time.
              </p>
            </div>

            {/* Visual: Line Chart SVG Mockup */}
            <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm flex flex-col justify-between h-[155px]">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-slate-800 uppercase tracking-wider">Balance Trend</span>
                <span className="text-[9px] text-emerald-500 font-bold bg-emerald-50 px-1.5 py-0.5 rounded">+15.8%</span>
              </div>
              <div className="h-[70px] w-full pt-2">
                <svg className="w-full h-full overflow-visible" viewBox="0 0 200 60">
                  <path
                    d="M 0 50 Q 30 30 60 40 T 120 10 T 180 20 T 200 5"
                    fill="none"
                    stroke="#8b5cf6"
                    strokeWidth="3.5"
                    strokeLinecap="round"
                  />
                  <path
                    d="M 0 50 Q 30 30 60 40 T 120 10 T 180 20 T 200 5 L 200 60 L 0 60 Z"
                    fill="url(#grad)"
                    opacity="0.1"
                  />
                  <defs>
                    <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="#8b5cf6" />
                      <stop offset="100%" stopColor="#ffffff" />
                    </linearGradient>
                  </defs>
                  {/* Glowing end point */}
                  <circle cx="200" cy="5" r="4.5" fill="#8b5cf6" stroke="#ffffff" strokeWidth="1.5" />
                </svg>
              </div>
              <div className="flex justify-between text-[8px] text-slate-400 font-semibold border-t border-slate-50 pt-2">
                <span>Jan</span><span>Mar</span><span>May</span><span>Jul</span><span>Sep</span><span>Nov</span>
              </div>
            </div>
          </div>

          {/* Card 4: Expenses Tracker */}
          <div className="bg-[#f8fafc]/80 border border-slate-100 rounded-3xl p-8 flex flex-col justify-between transition-all duration-300 hover:shadow-lg hover:shadow-slate-100/50">
            <div className="mb-8">
              <h3 className="text-lg font-bold text-slate-900 mb-2">Expenses Tracker</h3>
              <p className="text-slate-500 text-xs leading-relaxed font-medium">
                Keep every transaction categorized and logged. Search and filter by user, tag, currency, or settlement state.
              </p>
            </div>

            {/* Visual: Area Chart SVG Mockup */}
            <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm flex flex-col justify-between h-[155px]">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-slate-800 uppercase tracking-wider">Monthly Spend</span>
                <span className="text-[9px] text-[#2b50d8] font-bold bg-[#f0f3fa] px-1.5 py-0.5 rounded">₹35,240</span>
              </div>
              <div className="h-[70px] w-full pt-2">
                <svg className="w-full h-full overflow-visible" viewBox="0 0 200 60">
                  <path
                    d="M 0 55 C 30 50, 40 25, 70 30 C 100 35, 120 15, 150 20 C 180 25, 190 5, 200 8"
                    fill="none"
                    stroke="#2b50d8"
                    strokeWidth="3"
                  />
                  <path
                    d="M 0 55 C 30 50, 40 25, 70 30 C 100 35, 120 15, 150 20 C 180 25, 190 5, 200 8 L 200 60 L 0 60 Z"
                    fill="url(#grad2)"
                    opacity="0.12"
                  />
                  <defs>
                    <linearGradient id="grad2" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="#2b50d8" />
                      <stop offset="100%" stopColor="#ffffff" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <div className="flex justify-between text-[8px] text-slate-400 font-semibold border-t border-slate-50 pt-2">
                <span>Week 1</span><span>Week 2</span><span>Week 3</span><span>Week 4</span>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ─── Why You'll Love Using It Section ─── */}
      <section id="why" className="pt-24 pb-36 bg-[#fafbfc] border-y border-slate-100/50">
        <div className="max-w-7xl mx-auto px-6 text-center">

          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-16 text-left">
            <div>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#1e1b4b] tracking-tight mb-2">
                Why You'll Love<br />Using It
              </h2>
              <p className="text-slate-500 text-xs max-w-md">Our users choose Simplified because of its security, clarity, and automation.</p>
            </div>
            <div className="mt-6 sm:mt-0">
              <button
                onClick={() => navigate('/register')}
                className="bg-[#8b5cf6] text-white rounded-full px-6 py-2.5 text-xs font-bold hover:bg-[#7c3aed] transition shadow-md shadow-purple-500/10"
              >
                Sign Up
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-left">

            {/* Card 1: Visibility */}
            <div className="bg-gradient-to-b from-orange-100 to-orange-50/20 border border-orange-100/50 p-8 rounded-[32px] flex flex-col justify-between h-[320px] transition-transform duration-300 hover:-translate-y-2 hover:shadow-md">
              <div>
                <h4 className="text-xl sm:text-2xl font-extrabold text-slate-900 leading-snug">Gain full visibility over your finances</h4>
              </div>
              <p className="text-[13px] sm:text-sm text-slate-500 leading-relaxed font-medium">
                Understand your finances at a glance with clean charts and summaries.
              </p>
            </div>

            {/* Card 2: Reduce Spending */}
            <div className="bg-gradient-to-b from-pink-100 to-pink-50/20 border border-pink-100/50 p-8 rounded-[32px] flex flex-col justify-between h-[320px] transition-transform duration-300 lg:translate-y-10 hover:shadow-md">
              <div>
                <h4 className="text-xl sm:text-2xl font-extrabold text-slate-900 leading-snug">Reduce unnecessary spending</h4>
              </div>
              <p className="text-[13px] sm:text-sm text-slate-500 leading-relaxed font-medium">
                Flag duplicate transactions, receipt spikes, and statistical outliers automatically.
              </p>
            </div>

            {/* Card 3: Stay Organized */}
            <div className="bg-gradient-to-b from-sky-100 to-sky-50/20 border border-sky-100/50 p-8 rounded-[32px] flex flex-col justify-between h-[320px] transition-transform duration-300 hover:-translate-y-2 hover:shadow-md">
              <div>
                <h4 className="text-xl sm:text-2xl font-extrabold text-slate-900 leading-snug">Stay organized without extra effort</h4>
              </div>
              <p className="text-[13px] sm:text-sm text-slate-500 leading-relaxed font-medium">
                Drag and drop CSV bank statements to bulk-upload expenses in seconds.
              </p>
            </div>

            {/* Card 4: Confident Decisions */}
            <div className="bg-gradient-to-b from-indigo-100 to-indigo-50/20 border border-indigo-100/50 p-8 rounded-[32px] flex flex-col justify-between h-[320px] transition-transform duration-300 lg:translate-y-10 hover:shadow-md">
              <div>
                <h4 className="text-xl sm:text-2xl font-extrabold text-slate-900 leading-snug">Make confident financial decisions</h4>
              </div>
              <p className="text-[13px] sm:text-sm text-slate-500 leading-relaxed font-medium">
                Leverage AI-assisted narration to explain balances and suggest actions.
              </p>
            </div>

          </div>

        </div>
      </section>

      {/* ─── Testimonials Section (Trusted by People Who Want Control) ─── */}
      <section id="testimonials" className="py-24 max-w-7xl mx-auto px-6 relative z-10">

        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-16 text-left">
          <div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#1e1b4b] tracking-tight mb-2">
              Trusted by People<br />Who Want Control
            </h2>
            <p className="text-slate-500 text-xs max-w-md">Hear what families and remote teams say about their experience using our platform.</p>
          </div>
          <div className="mt-6 sm:mt-0">
            <button className="bg-slate-950 text-white rounded-full px-5 py-2.5 text-xs font-bold hover:bg-slate-800 transition">
              Read More Reviews
            </button>
          </div>
        </div>

        {/* Testimonials Profile Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-left">

          {/* Testimonial 1 */}
          <div className="bg-white border border-slate-100 shadow-md p-8 rounded-3xl flex flex-col justify-between gap-6 hover:shadow-lg transition-shadow">
            <p className="text-slate-600 text-xs leading-relaxed font-medium italic">
              "This app completely changed how I manage my family expenses. Group splits take seconds, and the AI explanation features mean there are never any arguments about who owes what. It has made our budget completely transparent."
            </p>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-100 overflow-hidden flex items-center justify-center font-bold text-xs text-indigo-600 border border-indigo-50">
                MW
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-800">Marc West</h4>
                <p className="text-[9px] text-slate-400">Verified Home Administrator</p>
              </div>
            </div>
          </div>

          {/* Testimonial 2 */}
          <div className="bg-white border border-slate-100 shadow-md p-8 rounded-3xl flex flex-col justify-between gap-6 hover:shadow-lg transition-shadow">
            <p className="text-slate-600 text-xs leading-relaxed font-medium italic">
              "Outstanding. We manage our remote shared workspace costs using Goa Trip style ledger pools. Since we joined, our accounts are 100% auditable. Highly recommended for anyone splitting business or personal costs."
            </p>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-100 overflow-hidden flex items-center justify-center font-bold text-xs text-indigo-600 border border-indigo-50">
                LY
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-800">Lee Yuan</h4>
                <p className="text-[9px] text-slate-400">Co-working Space Partner</p>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ─── Call to Action (Start Managing Your Home Expenses Today) ─── */}
      <section className="bg-white py-32 text-center relative overflow-hidden">
        <div className="relative z-10 max-w-2xl mx-auto px-6 space-y-8">
          <h2 className="text-5xl sm:text-6xl font-extrabold text-[#100e34] tracking-tight leading-tight">
            Start Managing Your<br />Home Expenses Today
          </h2>
          <p className="text-slate-500 text-sm leading-relaxed max-w-lg mx-auto font-medium">
            Take the first step toward financial clarity and control. No complicated setup just smarter living.
          </p>
          <div className="flex justify-center items-center gap-4 pt-6">
            <button
              onClick={() => navigate('/register')}
              className="bg-[#8b5cf6] text-white rounded-lg px-8 py-3.5 text-sm font-bold hover:bg-[#7c3aed] transition shadow-xl shadow-purple-500/20"
            >
              Get Started Now
            </button>
            <button
              onClick={() => navigate('/login')}
              className="bg-transparent text-slate-500 border border-slate-200 rounded-lg px-8 py-3.5 text-sm font-bold hover:bg-slate-50 transition"
            >
              Try Demo
            </button>
          </div>
        </div>
      </section>

      {/* ─── Footer Section ─── */}
      <footer className="bg-[#f8f9ff] pt-24 pb-12 text-slate-500 text-sm relative z-10 overflow-hidden">
        
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-5 gap-12 mb-20 text-left">

          <div className="col-span-1 space-y-6">
            <h4 className="text-[13px] font-extrabold text-slate-900 uppercase tracking-widest">Features</h4>
            <ul className="space-y-4 font-medium text-slate-500 text-xs">
              <li><a href="#features" className="hover:text-[#8b5cf6] transition-colors">Features</a></li>
              <li><a href="/dashboard" className="hover:text-[#8b5cf6] transition-colors">Dashboard</a></li>
              <li><a href="#" className="hover:text-[#8b5cf6] transition-colors">Mobile App</a></li>
              <li><a href="#" className="hover:text-[#8b5cf6] transition-colors">Pricing</a></li>
              <li><a href="#" className="hover:text-[#8b5cf6] transition-colors">Updates</a></li>
            </ul>
          </div>

          <div className="col-span-1 space-y-6">
            <h4 className="text-[13px] font-extrabold text-slate-900 uppercase tracking-widest">Company</h4>
            <ul className="space-y-4 font-medium text-slate-500 text-xs">
              <li><a href="#about" className="hover:text-[#8b5cf6] transition-colors">About Us</a></li>
              <li><a href="#contact" className="hover:text-[#8b5cf6] transition-colors">Contact</a></li>
              <li><a href="#" className="hover:text-[#8b5cf6] transition-colors">Career</a></li>
              <li><a href="#blog" className="hover:text-[#8b5cf6] transition-colors">Blogs</a></li>
            </ul>
          </div>

          <div className="col-span-1 space-y-6">
            <h4 className="text-[13px] font-extrabold text-slate-900 uppercase tracking-widest">Resources</h4>
            <ul className="space-y-4 font-medium text-slate-500 text-xs">
              <li><a href="#" className="hover:text-[#8b5cf6] transition-colors">Help Center</a></li>
              <li><a href="#" className="hover:text-[#8b5cf6] transition-colors">FAQs</a></li>
              <li><a href="#" className="hover:text-[#8b5cf6] transition-colors">Guides</a></li>
              <li><a href="#" className="hover:text-[#8b5cf6] transition-colors">Support</a></li>
            </ul>
          </div>

          <div className="col-span-2 space-y-6">
            <h4 className="text-[13px] font-extrabold text-slate-900 uppercase tracking-widest">Subscribe Our Newsletter</h4>
            <form onSubmit={handleSubmitWaitlist} className="relative max-w-sm">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Submit you email"
                className="bg-white border border-slate-100 rounded-xl px-4 py-4 w-full focus:outline-none focus:ring-2 focus:ring-[#8b5cf6]/20 focus:border-[#8b5cf6] text-xs font-medium text-slate-800 shadow-sm"
              />
              <button type="submit" className="absolute right-1 top-1 bottom-1 bg-[#8b5cf6] text-white rounded-lg px-6 font-bold text-xs hover:bg-[#7c3aed] transition shadow-md shadow-purple-500/20">
                Subscribe
              </button>
            </form>
            {isSubmitted && (
              <p className="text-[10px] text-emerald-600 font-bold mt-2 bg-emerald-50 px-3 py-1.5 rounded-lg inline-block">
                Awesome! You're on the list.
              </p>
            )}
          </div>

        </div>

        {/* Global Bottom Bar */}
        <div className="max-w-7xl mx-auto px-6 pt-12 border-t border-slate-200/50 flex flex-col md:flex-row items-center justify-between gap-8">
          
          <div className="flex flex-wrap gap-6 font-bold text-[11px] text-slate-400 order-2 md:order-1">
            <a href="#" className="hover:text-slate-900 transition-colors uppercase tracking-wider">Privacy Policy</a>
            <a href="#" className="hover:text-slate-900 transition-colors uppercase tracking-wider">Terms of Service</a>
            <a href="#" className="hover:text-slate-900 transition-colors uppercase tracking-wider">Cookie Policy</a>
          </div>

          <div className="text-center order-3 md:order-2">
            <p className="text-[11px] text-slate-400 font-bold uppercase tracking-widest">
              Website by Taqwah Agency © 2026 kodo finance management
            </p>
          </div>

          <div className="flex items-center gap-3 order-1 md:order-3">
             <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#8b5cf6] to-[#a78bfa] flex items-center justify-center shadow-lg shadow-purple-500/20 rotate-12">
               <Layers className="w-6 h-6 text-white" />
             </div>
             <span className="text-4xl font-black text-slate-900 tracking-tighter">Simplified</span>
          </div>

        </div>

      </footer>

    </div>
  );
}
