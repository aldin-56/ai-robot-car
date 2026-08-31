import React from 'react';
import {
  Sparkles,
  LayoutDashboard,
  PlusCircle,
  Layers,
  Store,
  Settings as SettingsIcon,
  ShieldCheck,
  Zap,
  Activity
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'new_task', label: 'New Goal / Task', icon: PlusCircle },
    { id: 'projects', label: 'Projects', icon: Layers },
    { id: 'tools', label: 'AI Tools Registry', icon: Store },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <div
            className="flex items-center space-x-3 cursor-pointer"
            onClick={() => setActiveTab('landing')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 p-0.5 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <div className="w-full h-full bg-slate-900 rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
                LiteMind
              </span>
              <span className="text-[10px] block font-mono text-indigo-400 font-semibold tracking-wider uppercase -mt-1">
                AI Orchestration Engine
              </span>
            </div>
          </div>

          {/* Nav Items */}
          <nav className="hidden md:flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* System Status Badge & Create Quick CTA */}
          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Orchestrator Online</span>
            </div>

            <button
              onClick={() => setActiveTab('new_task')}
              className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white text-sm font-semibold px-4 py-2 rounded-lg shadow-md shadow-indigo-500/25 transition-all flex items-center space-x-2"
            >
              <Zap className="w-4 h-4" />
              <span>Create Goal</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
