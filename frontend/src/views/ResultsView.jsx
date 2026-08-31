import React, { useState, useEffect } from 'react';
import { Download, FileText, CheckCircle2, Sparkles, Layers, ArrowLeft, ExternalLink } from 'lucide-react';

export default function ResultsView({ projectData, onBack }) {
  const [details, setDetails] = useState(projectData || null);

  const finalOutput = details?.outputs?.[0] || {};
  const isFilePath = Boolean(finalOutput.file_path);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-slate-400 hover:text-white px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 flex items-center space-x-2 text-xs font-semibold transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold flex items-center space-x-1.5">
          <CheckCircle2 className="w-4 h-4" />
          <span>Final Outcome Delivered</span>
        </span>
      </div>

      {/* Main Output Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6 shadow-2xl">
        <div className="space-y-2 border-b border-slate-800 pb-6">
          <span className="text-xs font-mono text-indigo-400 font-bold uppercase tracking-wider">
            Generated Output • {finalOutput.output_type?.toUpperCase() || 'RESULT'}
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            {details?.project?.title || 'Execution Outcome'}
          </h1>
        </div>

        {/* Output Preview */}
        {finalOutput.file_path ? (
          <div className="bg-slate-950 rounded-2xl border border-slate-800 p-8 text-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto">
              <FileText className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-white">
                Download Generated {finalOutput.output_type?.toUpperCase()} Document
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                {finalOutput.file_path}
              </p>
            </div>

            <a
              href={`/api/workflows/download?path=${encodeURIComponent(finalOutput.file_path)}`}
              download
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-bold px-6 py-3.5 rounded-xl shadow-lg shadow-indigo-500/25 transition-all text-sm"
            >
              <Download className="w-4 h-4" />
              <span>Download File ({finalOutput.output_type?.toUpperCase()})</span>
            </a>
          </div>
        ) : (
          <div className="bg-slate-950 rounded-2xl border border-slate-800 p-6 font-mono text-sm text-slate-200 leading-relaxed whitespace-pre-wrap max-h-[500px] overflow-y-auto">
            {finalOutput.content || "Outcome completed successfully."}
          </div>
        )}
      </div>
    </div>
  );
}
