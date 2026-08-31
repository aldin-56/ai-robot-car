import React, { useState, useEffect } from 'react';
import { Layers, Clock, ArrowRight, FileText, CheckCircle2, RefreshCw } from 'lucide-react';

export default function ProjectsView({ onViewProject }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/projects');
      const data = await res.json();
      setProjects(data || []);
    } catch (err) {
      console.error("Failed to load projects", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-white">My Projects & Workflows</h1>
          <p className="text-slate-400 text-sm">View past AI orchestrated execution graphs and final results.</p>
        </div>
        <button
          onClick={fetchProjects}
          className="text-slate-400 hover:text-white p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loading ? (
        <div className="py-16 text-center text-slate-500 text-sm">Loading project history...</div>
      ) : projects.length === 0 ? (
        <div className="py-16 text-center border-2 border-dashed border-slate-800 rounded-2xl">
          <p className="text-slate-400 text-sm">No projects found. Create a new goal to start!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {projects.map((p) => (
            <div
              key={p.id}
              onClick={() => onViewProject(p.id)}
              className="bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-6 cursor-pointer transition-all hover:shadow-xl space-y-4 group"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1 pr-4">
                  <h3 className="font-bold text-white text-lg group-hover:text-indigo-400 transition-colors line-clamp-1">
                    {p.title}
                  </h3>
                  <span className="inline-block px-2.5 py-0.5 rounded-md bg-slate-800 text-indigo-300 text-xs font-mono">
                    Format: {p.output_format.toUpperCase()}
                  </span>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold capitalize shrink-0 ${
                  p.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                  p.status === 'in_progress' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 animate-pulse' :
                  'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                }`}>
                  {p.status.replace('_', ' ')}
                </span>
              </div>

              <p className="text-sm text-slate-400 line-clamp-2 bg-slate-950/50 p-3 rounded-xl border border-slate-800/50 italic">
                "{p.original_request}"
              </p>

              <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-800/50">
                <span className="flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{p.created_at ? new Date(p.created_at).toLocaleDateString() : 'Recent'}</span>
                </span>
                <span className="flex items-center space-x-1 text-indigo-400 font-semibold group-hover:translate-x-1 transition-transform">
                  <span>View Details</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
