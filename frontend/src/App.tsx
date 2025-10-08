
import React, { useState } from 'react';
import { WizardContainer, WizardConfig } from './components/wizard/WizardContainer';
import { ResultsPage } from './components/results/ResultsPage';


function App() {
  const [currentView, setCurrentView] = useState<'wizard' | 'results'>('wizard');
  const [backtestId, setBacktestId] = useState<string | null>(null);

  const handleWizardComplete = (config: WizardConfig) => {
    // This will be handled by the WizardContainer's handleComplete function
    console.log('Wizard completed with config:', config);
  };

  const handleShowResults = (id: string) => {
    setBacktestId(id);
    setCurrentView('results');
  };

  const handleBack = () => {
    setCurrentView('wizard');
    setBacktestId(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {currentView === 'wizard' ? (
        <WizardContainer
          onComplete={handleWizardComplete}
          onCancel={() => setCurrentView('wizard')}
          onShowResults={handleShowResults}
        />
      ) : backtestId ? (
        <ResultsPage
          backtestId={backtestId}
          onBack={handleBack}
        />
      ) : (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading results...</p>
          </div>
        </div>
      )}
    </div>
  );
}


export default App;
