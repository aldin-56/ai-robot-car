import React, { useState } from 'react';
import Navbar from './components/Navbar';
import LandingPage from './views/LandingPage';
import Dashboard from './views/Dashboard';
import TaskCreator from './views/TaskCreator';
import WorkflowVisualizer from './views/WorkflowVisualizer';
import ResultsView from './views/ResultsView';
import ProjectsView from './views/ProjectsView';
import ToolsMarketplace from './views/ToolsMarketplace';
import SettingsView from './views/SettingsView';

export default function App() {
  const [activeTab, setActiveTab] = useState('landing');
  const [currentWorkflowData, setCurrentWorkflowData] = useState(null);
  const [currentProjectDetails, setCurrentProjectDetails] = useState(null);

  const handleWorkflowPlanned = (planData) => {
    setCurrentWorkflowData(planData);
    setActiveTab('visualizer');
  };

  const handleViewProjectDetails = async (projectId) => {
    try {
      const res = await fetch(`/api/projects/${projectId}`);
      const data = await res.json();
      setCurrentProjectDetails(data);
      setActiveTab('results');
    } catch (err) {
      console.error("Failed to load project details", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'landing' && (
          <LandingPage onGetStarted={() => setActiveTab('new_task')} />
        )}

        {activeTab === 'dashboard' && (
          <Dashboard
            onNewTask={() => setActiveTab('new_task')}
            onViewProject={handleViewProjectDetails}
            onManageTools={() => setActiveTab('tools')}
          />
        )}

        {activeTab === 'new_task' && (
          <TaskCreator onWorkflowPlanned={handleWorkflowPlanned} />
        )}

        {activeTab === 'visualizer' && (
          <WorkflowVisualizer
            workflowData={currentWorkflowData}
            onCompleted={(finalOutput) => {
              // Option to navigate to results or stay on graph
            }}
          />
        )}

        {activeTab === 'results' && (
          <ResultsView
            projectData={currentProjectDetails}
            onBack={() => setActiveTab('dashboard')}
          />
        )}

        {activeTab === 'projects' && (
          <ProjectsView onViewProject={handleViewProjectDetails} />
        )}

        {activeTab === 'tools' && (
          <ToolsMarketplace />
        )}

        {activeTab === 'settings' && (
          <SettingsView />
        )}
      </main>
    </div>
  );
}
