import React, { useState, useEffect } from 'react';
import {
  Play,
  CheckCircle2,
  Loader2,
  XCircle,
  Cpu,
  HelpCircle,
  Info,
  DollarSign,
  ArrowDown,
  Sparkles,
  FileText,
  Download
} from 'lucide-react';

export default function WorkflowVisualizer({ workflowData, onCompleted }) {
  const [nodes, setNodes] = useState(workflowData?.graph_structure?.nodes || []);
  const [isExecuting, setIsExecuting] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [finalResult, setFinalResult] = useState(null);
  const [logs, setLogs] = useState([]);

  const workflowId = workflowData?.workflow_id;

  useEffect(() => {
    if (!workflowId || !isExecuting) return;

    // Connect to Server-Sent Events (SSE) stream for live updates
    const eventSource = new EventSource(`/api/workflows/${workflowId}/stream`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === 'connected') return;

        // Log event
        setLogs((prev) => [data, ...prev]);

        // Update task node state in graph
        if (data.task_id || data.task_title) {
          setNodes((prevNodes) =>
            prevNodes.map((node) => {
              if (node.title === data.task_title || node.id === data.task_id) {
                return {
                  ...node,
                  status: data.status,
                  assigned_tool_name: data.tool_used || node.assigned_tool_name,
                  tool_selection_reason: data.selection_reason || node.tool_selection_reason,
                  output_data: data.result_summary || node.output_data
                };
              }
              return node;
            })
          );
        }

        // Final result delivered
        if (data.final_output) {
          setFinalResult(data.final_output);
          setIsExecuting(false);
          eventSource.close();
          if (onCompleted) onCompleted(data.final_output);
        }

        if (data.status === 'failed') {
          setIsExecuting(false);
          eventSource.close();
        }
      } catch (err) {
        console.error("Error processing SSE message", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE stream error", err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [workflowId, isExecuting]);

  const handleStartExecution = async () => {
    setIsExecuting(true);
    try {
      await fetch(`/api/workflows/${workflowId}/execute`, { method: 'POST' });
    } catch (err) {
      console.error("Failed to start workflow execution", err);
      setIsExecuting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Top Banner & Execution Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-2xl">
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h1 className="text-2xl font-extrabold text-white">Dynamic Workflow Graph</h1>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Workflow ID: {workflowId} • Estimated Cost: ${workflowData?.estimated_cost?.toFixed(4)}
          </p>
        </div>

        {!isExecuting && !finalResult && (
          <button
            onClick={handleStartExecution}
            className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold px-8 py-3.5 rounded-2xl shadow-xl shadow-emerald-500/25 flex items-center space-x-2 transition-all text-base"
          >
            <Play className="w-5 h-5 fill-white" />
            <span>Execute Workflow</span>
          </button>
        )}

        {isExecuting && (
          <div className="flex items-center space-x-3 px-4 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-semibold">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>LiteMind is orchestrating AI tools...</span>
          </div>
        )}

        {finalResult && (
          <div className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-bold">
            <CheckCircle2 className="w-5 h-5" />
            <span>Workflow Completed ✓</span>
          </div>
        )}
      </div>

      {/* Main Execution DAG Flow and Transparency Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: DAG Timeline Steps */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">
            Execution Graph Nodes ({nodes.length} Steps)
          </h2>

          <div className="space-y-4">
            {nodes.map((node, index) => {
              const isCompleted = node.status === 'completed';
              const isRunning = node.status === 'running';
              const isFailed = node.status === 'failed';
              const isSelected = selectedNode?.step_order === node.step_order;

              return (
                <React.Fragment key={index}>
                  <div
                    onClick={() => setSelectedNode(node)}
                    className={`p-5 rounded-2xl border transition-all cursor-pointer relative ${
                      isSelected ? 'border-indigo-500 bg-indigo-950/20 shadow-lg' : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {/* Status Icon Indicator */}
                        <div className="mt-0.5">
                          {isCompleted && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                          {isRunning && <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />}
                          {isFailed && <XCircle className="w-5 h-5 text-red-400" />}
                          {!isCompleted && !isRunning && !isFailed && (
                            <div className="w-5 h-5 rounded-full border-2 border-slate-700 flex items-center justify-center text-[10px] text-slate-500 font-mono">
                              {index + 1}
                            </div>
                          )}
                        </div>

                        <div className="space-y-1">
                          <h3 className="font-bold text-white text-base">{node.title}</h3>
                          <p className="text-xs text-slate-400">{node.description}</p>
                        </div>
                      </div>

                      {/* Tool Assigned Badge */}
                      <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full bg-slate-950 text-indigo-300 text-xs font-mono border border-slate-800 shrink-0">
                        <Cpu className="w-3 h-3 text-indigo-400" />
                        <span>{node.assigned_tool_name || node.assigned_tool_id}</span>
                      </span>
                    </div>

                    {/* Step details if completed */}
                    {isCompleted && node.output_data && (
                      <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs text-slate-300 line-clamp-2 bg-slate-950/50 p-2.5 rounded-xl font-mono">
                        {typeof node.output_data === 'string' ? node.output_data : (node.output_data.content || JSON.stringify(node.output_data))}
                      </div>
                    )}
                  </div>

                  {/* Connecting Arrow between dependent steps */}
                  {index < nodes.length - 1 && (
                    <div className="flex justify-center my-1">
                      <ArrowDown className="w-4 h-4 text-slate-700" />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Right Column: "Why this Tool?" Transparency Inspector */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Info className="w-4 h-4 text-indigo-400" />
            <span>Tool Selection & Rationale</span>
          </h2>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 sticky top-24">
            {selectedNode ? (
              <div className="space-y-4">
                <div className="space-y-1">
                  <span className="text-xs font-mono text-indigo-400 uppercase">Selected Node</span>
                  <h3 className="text-lg font-bold text-white">{selectedNode.title}</h3>
                </div>

                <div className="space-y-2">
                  <span className="text-xs font-semibold text-slate-400 block">Assigned AI Integration</span>
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-sm font-bold text-indigo-300 flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-indigo-400" />
                    <span>{selectedNode.assigned_tool_name || selectedNode.assigned_tool_id}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="text-xs font-semibold text-slate-400 block">Why this tool?</span>
                  <p className="p-3 bg-indigo-950/30 border border-indigo-500/20 rounded-xl text-xs text-slate-300 leading-relaxed">
                    {selectedNode.tool_selection_reason || "Selected based on capability match and quality rating."}
                  </p>
                </div>

                {selectedNode.output_data && (
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-slate-400 block">Node Output Result</span>
                    <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] text-emerald-300 overflow-x-auto max-h-40">
                      {JSON.stringify(selectedNode.output_data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 text-xs space-y-2">
                <HelpCircle className="w-8 h-8 text-slate-700 mx-auto" />
                <p>Click any step in the graph to view its assigned tool selection reasoning and output payload.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
