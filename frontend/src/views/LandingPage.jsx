import React from 'react';
import { Sparkles, ArrowRight, Layers, Cpu, ShieldCheck, CheckCircle2, Zap } from 'lucide-react';

export default function LandingPage({ onGetStarted }) {
  return (
    <div className="bg-slate-950 text-white min-h-screen">
      {/* Hero Section */}
      <div className="relative overflow-hidden pt-12 pb-20 sm:pt-20 sm:pb-32">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.25),rgba(255,255,255,0))]"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">

          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-8">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>AI Goal Orchestration Engine</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight max-w-4xl mx-auto leading-tight">
            One Goal. Multiple AIs.{' '}
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              One Finished Result.
            </span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto font-normal">
            Don't choose the AI. Choose the goal. LiteMind automatically decomposes your objective, selects the best specialized tools, executes multi-stage workflows, and delivers complete outputs.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={onGetStarted}
              className="w-full sm:w-auto bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-600 hover:from-indigo-600 hover:to-pink-700 text-white font-bold px-8 py-4 rounded-xl shadow-lg shadow-indigo-500/30 flex items-center justify-center space-x-3 transition-all text-lg"
            >
              <span>Start Creating Now</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>

          {/* Key Value Props */}
          <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Smart Tool Selection</h3>
              <p className="text-slate-400 text-sm">
                Evaluates speed, cost, quality rating, and capabilities across Gemini, OpenAI, Claude, web search, and image models for every single task.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Dynamic DAG Workflows</h3>
              <p className="text-slate-400 text-sm">
                Generates execution graphs tailored specifically to your goal with output passing, automatic retries, and fallback tool execution.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
              <div className="w-12 h-12 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400 mb-4">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Quality & Security</h3>
              <p className="text-slate-400 text-sm">
                Backend API credential key encryption, prompt injection defense boundaries, and automated quality control evaluation.
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
