import React, { useState, useEffect } from 'react';
import { Store, Key, CheckCircle2, XCircle, RefreshCw, Shield, Star, Zap, Plus, Trash2 } from 'lucide-react';

export default function ToolsMarketplace() {
  const [tools, setTools] = useState([]);
  const [credentials, setCredentials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeModalProvider, setActiveModalProvider] = useState(null);
  const [inputApiKey, setInputApiKey] = useState('');
  const [savingKey, setSavingKey] = useState(false);
  const [testStatus, setTestStatus] = useState({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tRes, cRes] = await Promise.all([
        fetch('/api/tools'),
        fetch('/api/credentials')
      ]);
      const tData = await tRes.json();
      const cData = await cRes.json();
      setTools(tData || []);
      setCredentials(cData || []);
    } catch (err) {
      console.error("Failed to load tools registry", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCredential = async () => {
    if (!inputApiKey.trim() || !activeModalProvider) return;
    setSavingKey(true);
    try {
      const res = await fetch('/api/credentials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_id: activeModalProvider.provider_id,
          api_key: inputApiKey.trim()
        })
      });
      if (res.ok) {
        setActiveModalProvider(null);
        setInputApiKey('');
        await loadData();
      }
    } catch (err) {
      console.error("Failed to save key", err);
    } finally {
      setSavingKey(false);
    }
  };

  const handleRemoveCredential = async (providerId) => {
    if (!confirm(`Are you sure you want to disconnect ${providerId.toUpperCase()}?`)) return;
    try {
      await fetch(`/api/credentials/${providerId}`, { method: 'DELETE' });
      await loadData();
    } catch (err) {
      console.error("Failed to remove credential", err);
    }
  };

  const handleTestConnection = async (providerId) => {
    setTestStatus(prev => ({ ...prev, [providerId]: 'testing' }));
    try {
      const res = await fetch('/api/credentials/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: providerId })
      });
      const data = await res.json();
      setTestStatus(prev => ({
        ...prev,
        [providerId]: data.is_valid ? 'success' : 'failed'
      }));
    } catch (err) {
      setTestStatus(prev => ({ ...prev, [providerId]: 'failed' }));
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-white">AI Tool Registry & Integrations</h1>
        <p className="text-slate-400 text-sm mt-1">
          Connect your AI provider API keys. LiteMind automatically selects and coordinates connected tools.
        </p>
      </div>

      {/* Connected Providers Row */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <Key className="w-5 h-5 text-indigo-400" />
          <span>Connected AI Providers</span>
        </h2>

        {loading ? (
          <div className="py-8 text-center text-slate-500 text-sm">Loading connection status...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {credentials.map((c) => (
              <div
                key={c.provider_id}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 relative flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-white text-lg">{c.provider_name}</h3>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold flex items-center space-x-1 ${
                      c.is_connected
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}>
                      {c.is_connected ? (
                        <>
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          <span>Connected ✓</span>
                        </>
                      ) : (
                        <span>Not connected</span>
                      )}
                    </span>
                  </div>

                  <p className="text-slate-400 text-xs line-clamp-2">{c.description}</p>

                  {c.masked_key && (
                    <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 font-mono text-xs text-indigo-300 flex items-center justify-between">
                      <span>{c.masked_key}</span>
                      <Shield className="w-3.5 h-3.5 text-slate-500" />
                    </div>
                  )}
                </div>

                <div className="pt-2 flex items-center justify-between border-t border-slate-800/80 gap-2">
                  {c.is_connected ? (
                    <>
                      <button
                        onClick={() => handleTestConnection(c.provider_id)}
                        className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white transition-all flex items-center space-x-1"
                      >
                        <RefreshCw className={`w-3 h-3 ${testStatus[c.provider_id] === 'testing' ? 'animate-spin' : ''}`} />
                        <span>
                          {testStatus[c.provider_id] === 'testing' ? 'Testing...' :
                           testStatus[c.provider_id] === 'success' ? 'Valid ✓' :
                           testStatus[c.provider_id] === 'failed' ? 'Invalid ❌' : 'Test'}
                        </span>
                      </button>

                      {c.masked_key && (
                        <button
                          onClick={() => handleRemoveCredential(c.provider_id)}
                          className="text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-all flex items-center space-x-1"
                          title="Disconnect API Key"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </>
                  ) : (
                    <button
                      onClick={() => setActiveModalProvider(c)}
                      className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-xl transition-all flex items-center justify-center space-x-1"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Connect Provider</span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Available Marketplace Tools */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <Store className="w-5 h-5 text-indigo-400" />
          <span>Available AI Tools & Capabilities</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tools.map((t) => (
            <div key={t.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-bold text-white text-base">{t.name}</h3>
                  <span className="text-xs font-mono text-indigo-400 capitalize">{t.category}</span>
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-800 text-slate-300">
                  {t.provider.toUpperCase()}
                </span>
              </div>

              <p className="text-slate-400 text-xs">{t.description}</p>

              <div className="flex flex-wrap gap-1.5 pt-1">
                {(t.capabilities || []).map((cap) => (
                  <span key={cap} className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 text-[10px] font-mono border border-indigo-500/20">
                    {cap}
                  </span>
                ))}
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center space-x-1">
                  <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                  <span>Rating: {t.quality_rating}/10</span>
                </span>
                <span className="flex items-center space-x-1">
                  <Zap className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Speed: {t.speed_rating}/10</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Connect API Key Modal */}
      {activeModalProvider && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-md w-full p-6 space-y-6 shadow-2xl">
            <div className="space-y-1">
              <h3 className="text-xl font-bold text-white">
                Connect {activeModalProvider.provider_name}
              </h3>
              <p className="text-xs text-slate-400">
                API keys are encrypted backend-only using Fernet key cryptography. Never exposed to the frontend.
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
                API Secret Key
              </label>
              <input
                type="password"
                placeholder="sk-..."
                value={inputApiKey}
                onChange={(e) => setInputApiKey(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setActiveModalProvider(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCredential}
                disabled={savingKey || !inputApiKey.trim()}
                className="px-6 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all disabled:opacity-50"
              >
                {savingKey ? 'Saving Encrypted Key...' : 'Save Credential'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
