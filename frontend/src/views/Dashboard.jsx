import React, { useState, useEffect } from 'react';
import {
  Zap,
  Layers,
  Store,
  Clock,
  CheckCircle2,
  AlertCircle,
  PlusCircle,
  ArrowRight,
  RefreshCw,
  Cpu
} from 'lucide-react';

export default function Dashboard({ onNewTask, onViewProject, onManageTools }) {
  const [projects, setProjects] = useState([]);
  const [credentials, setCredentials] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [projRes, credRes] = await Promise.all([
        fetch('/api/projects'),
        fetch('/api/credentials')
      ]);
      const projData = await projRes.json();
      const credData = await credRes.json();

      setProjects(projData || []);
      setCredentials(credData || []);
    } catch (err) {
      console.error("Failed to load dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  const activeConnectedCount = credentials.filter(c => c.is_connected).length;

  return (
    <div className="space-y-8">
      {/* Top Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-900 via-purple-900 to-slate-900 border border-indigo-500/30 p-8 shadow-2xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <span className="text-xs font-mono font-bold uppercase tracking-widest text-indigo-400 bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20">
              Goal Orchestrator Active
            </span>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              What do you want to accomplish today?
            </h1>
            <p className="text-slate-300 text-sm">
              LiteMind dynamically generates dynamic multi-AI execution workflows for your goals.
            </p>
          </div>

          <button
            onClick={onNewTask}
            className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-bold px-6 py-3.5 rounded-xl shadow-lg shadow-indigo-500/30 flex items-center justify-center space-x-2 transition-all shrink-0"
          >
            <PlusCircle className="w-5 h-5" />
            <span>Create New Goal</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Projects</p>
            <h3 className="text-3xl font-extrabold text-white mt-1">{projects.length}</h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Layers className="w-6 h-6" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm flex items-center justify-between cursor-pointer" onClick={onManageTools}>
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Connected Providers</p>
            <h3 className="text-3xl font-extrabold text-emerald-400 mt-1">{activeConnectedCount}</h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Store className="w-6 h-6" />
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Orchestration Health</p>
            <h3 className="text-xl font-bold text-white mt-1 flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
              <span>100% Ready</span>
            </h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <Cpu className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Recent Projects Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-white">Recent Projects & Workflows</h2>
          </div>

          <button
            onClick={fetchDashboardData}
            className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-all"
            title="Refresh History"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 text-sm">Loading project history...</div>
        ) : projects.length === 0 ? (
          <div className="py-12 text-center border-2 border-dashed border-slate-800 rounded-xl space-y-3">
            <p className="text-slate-400 text-sm">No project workflows created yet.</p>
            <button
              onClick={onNewTask}
              className="inline-flex items-center space-x-2 text-indigo-400 hover:text-indigo-300 font-semibold text-sm"
            >
              <span>Submit your first goal</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {projects.slice(0, 5).map((p) => (
              <div
                key={p.id}
                onClick={() => onViewProject(p.id)}
                className="py-4 flex items-center justify-between hover:bg-slate-800/50 px-4 rounded-xl cursor-pointer transition-all group"
              >
                <div className="space-y-1">
                  <h3 className="font-semibold text-white group-hover:text-indigo-400 transition-colors">
                    {p.title}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-1">{p.original_request}</p>
                </div>

                <div className="flex items-center space-x-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold capitalize ${
                    p.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                    p.status === 'in_progress' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 animate-pulse' :
                    'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}>
                    {p.status.replace('_', ' ')}
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
