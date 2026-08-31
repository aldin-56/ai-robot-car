import React, { useState } from 'react';
import { Sparkles, Upload, FileType, DollarSign, Sliders, ArrowRight, Loader2, AlertCircle } from 'lucide-react';

export default function TaskCreator({ onWorkflowPlanned }) {
  const [requestText, setRequestText] = useState('');
  const [outputFormat, setOutputFormat] = useState('auto');
  const [budgetLimit, setBudgetLimit] = useState(10.0);
  const [optimizationPref, setOptimizationPref] = useState('balanced');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isPlanning, setIsPlanning] = useState(false);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/workflows/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setUploadedFile(data);
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!requestText.trim()) return;

    setIsPlanning(true);
    try {
      const fullPrompt = uploadedFile
        ? `${requestText.trim()}\n\n[Attached File Reference: ${uploadedFile.filename}]`
        : requestText.trim();

      const res = await fetch('/api/workflows/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          request_text: fullPrompt,
          output_format: outputFormat,
          budget_limit: budgetLimit,
          optimization_pref: optimizationPref
        })
      });

      const data = await res.json();
      if (res.ok) {
        onWorkflowPlanned(data);
      }
    } catch (err) {
      console.error("Submit task failed", err);
    } finally {
      setIsPlanning(false);
    }
  };

  const sampleGoals = [
    "Create a presentation about renewable energy for Class 9.",
    "Research latest space missions and generate a summary report.",
    "Write Python code for a high performance WebSockets server.",
    "Generate a realistic image of a Kerala beach at sunset."
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          What do you want to accomplish?
        </h1>
        <p className="text-slate-400 text-sm max-w-xl mx-auto">
          LiteMind chooses and coordinates the tools. Simply tell us your desired final outcome.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6 shadow-2xl">
        {/* Large Goal Text Input */}
        <div className="space-y-2">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
            Your Goal / Request
          </label>
          <textarea
            rows={4}
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
            placeholder='e.g., "Create a 10-slide presentation about climate change for Class 9."'
            className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-4 text-base text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-all resize-none"
            required
          />
        </div>

        {/* Quick Sample Prompts */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-400 block">Try an example:</span>
          <div className="flex flex-wrap gap-2">
            {sampleGoals.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setRequestText(sample)}
                className="text-xs bg-slate-950 hover:bg-slate-800 text-indigo-300 border border-slate-800 px-3 py-1.5 rounded-xl transition-all text-left line-clamp-1"
              >
                "{sample}"
              </button>
            ))}
          </div>
        </div>

        {/* Options Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800">
          {/* Output Format */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-400 flex items-center space-x-1">
              <FileType className="w-3.5 h-3.5 text-indigo-400" />
              <span>Target Output</span>
            </label>
            <select
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="auto">Auto (Smart Detect)</option>
              <option value="pptx">PowerPoint (.pptx)</option>
              <option value="pdf">PDF Document (.pdf)</option>
              <option value="docx">Word Document (.docx)</option>
              <option value="image">Image (.png)</option>
              <option value="markdown">Markdown / Text</option>
            </select>
          </div>

          {/* Optimization Strategy */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-400 flex items-center space-x-1">
              <Sliders className="w-3.5 h-3.5 text-purple-400" />
              <span>Optimization</span>
            </label>
            <select
              value={optimizationPref}
              onChange={(e) => setOptimizationPref(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="balanced">Balanced (Quality + Speed)</option>
              <option value="best_quality">Best Quality Priority</option>
              <option value="lowest_cost">Lowest Cost Priority</option>
              <option value="fastest">Fastest Speed Priority</option>
            </select>
          </div>

          {/* File Upload Attachment */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-400 flex items-center space-x-1">
              <Upload className="w-3.5 h-3.5 text-emerald-400" />
              <span>Attach File (Optional)</span>
            </label>
            <label className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-300 cursor-pointer flex items-center justify-between transition-all">
              <span className="truncate">{uploadedFile ? uploadedFile.filename : (isUploading ? 'Uploading...' : 'Choose file')}</span>
              <input type="file" onChange={handleFileUpload} className="hidden" />
            </label>
          </div>
        </div>

        {/* Submit CTA Button */}
        <button
          type="submit"
          disabled={isPlanning || !requestText.trim()}
          className="w-full bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-600 hover:from-indigo-600 hover:to-pink-700 text-white font-bold py-4 rounded-2xl shadow-xl shadow-indigo-500/25 flex items-center justify-center space-x-3 transition-all text-base disabled:opacity-50"
        >
          {isPlanning ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing Goal & Generating Dynamic Workflow...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              <span>Generate Orchestration Graph</span>
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>
      </form>
    </div>
  );
}
