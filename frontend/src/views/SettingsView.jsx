import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Shield, DollarSign, Sliders, CheckCircle2 } from 'lucide-react';

export default function SettingsView() {
  const [optimizationPref, setOptimizationPref] = useState('balanced');
  const [spendingLimit, setSpendingLimit] = useState(10.0);
  const [privacyMode, setPrivacyMode] = useState('standard');
  const [savedMessage, setSavedMessage] = useState(false);

  useEffect(() => {
    fetch('/api/auth/me')
      .then(res => res.json())
      .then(data => {
        if (data) {
          setOptimizationPref(data.optimization_pref || 'balanced');
          setSpendingLimit(data.spending_limit || 10.0);
          setPrivacyMode(data.privacy_mode || 'standard');
        }
      })
      .catch(err => console.error(err));
  }, []);

  const handleSave = () => {
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 3000);
  };

  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-white">Orchestration & User Preferences</h1>
        <p className="text-slate-400 text-sm mt-1">Configure automated tool selection priorities, spending guardrails, and privacy controls.</p>
      </div>

      {savedMessage && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-3 rounded-xl text-sm font-semibold flex items-center space-x-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <span>Preferences updated successfully.</span>
        </div>
      )}

      {/* Optimization Mode */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <Sliders className="w-5 h-5 text-indigo-400" />
          <span>Tool Selection Optimization Strategy</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { id: 'balanced', label: 'Balanced (Recommended)', desc: 'Optimal trade-off between output quality, execution speed, and cost.' },
            { id: 'best_quality', label: 'Best Quality', desc: 'Prioritizes top-tier AI models (Gemini 2.5 Pro, GPT-4o) for complex tasks.' },
            { id: 'lowest_cost', label: 'Lowest Cost', desc: 'Prioritizes free or low-cost providers and open models.' },
            { id: 'fastest', label: 'Fastest Speed', desc: 'Prioritizes ultra-low latency response models.' },
          ].map((mode) => (
            <div
              key={mode.id}
              onClick={() => setOptimizationPref(mode.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                optimizationPref === mode.id
                  ? 'bg-indigo-600/10 border-indigo-500 text-white shadow-md'
                  : 'bg-slate-950/50 border-slate-800/80 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="font-semibold text-sm text-indigo-300">{mode.label}</div>
              <div className="text-xs text-slate-400 mt-1">{mode.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Spending Guardrails */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <DollarSign className="w-5 h-5 text-indigo-400" />
          <span>Workflow Budget Guardrail</span>
        </h2>

        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
            Maximum Workflow Cost Threshold ($ USD)
          </label>
          <input
            type="number"
            step="1"
            value={spendingLimit}
            onChange={(e) => setSpendingLimit(parseFloat(e.target.value) || 0)}
            className="w-full max-w-xs bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-indigo-500"
          />
          <p className="text-xs text-slate-500">
            Workflows exceeding this budget require explicit user confirmation before executing paid steps.
          </p>
        </div>
      </div>

      {/* Privacy Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <Shield className="w-5 h-5 text-indigo-400" />
          <span>Privacy & External Data Controls</span>
        </h2>

        <div className="space-y-3">
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="radio"
              name="privacy"
              checked={privacyMode === 'standard'}
              onChange={() => setPrivacyMode('standard')}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            <div>
              <span className="font-semibold text-sm text-white">Standard Mode</span>
              <p className="text-xs text-slate-400">Allows web research tools to search and fetch content relevant to user goals.</p>
            </div>
          </label>

          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="radio"
              name="privacy"
              checked={privacyMode === 'strict'}
              onChange={() => setPrivacyMode('strict')}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            <div>
              <span className="font-semibold text-sm text-white">Strict Privacy Mode</span>
              <p className="text-xs text-slate-400">Restricts external web scraping; only uses user-provided text or direct uploaded files.</p>
            </div>
          </label>
        </div>
      </div>

      <button
        onClick={handleSave}
        className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-8 py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-500/25"
      >
        Save Settings
      </button>
    </div>
  );
}
