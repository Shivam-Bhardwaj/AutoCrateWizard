'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Calculator, Download, Settings, FileText, Zap, CheckCircle } from 'lucide-react';
import CrateForm from '@/components/CrateForm';
import ResultsDisplay from '@/components/ResultsDisplay';
import LoadingSpinner from '@/components/LoadingSpinner';
import { CrateInputs, CrateResults } from '@/types';

export default function HomePage() {
  const [results, setResults] = useState<CrateResults | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async (inputs: CrateInputs) => {
    setIsCalculating(true);
    setError(null);
    
    try {
      const response = await fetch('/api/calculate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(inputs),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setResults(data.data);
      } else {
        setError(data.error || 'Calculation failed');
      }
    } catch (err) {
      setError('Failed to connect to calculation service');
    } finally {
      setIsCalculating(false);
    }
  };

  const handleDownloadExpressions = async () => {
    if (!results) return;
    
    try {
      const response = await fetch('/api/download-expressions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ expressions: results.nxExpressions }),
      });
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `AutoCrate_${new Date().toISOString().split('T')[0]}.exp`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Failed to download expressions file');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-3"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-autocrate-500 to-autocrate-600 rounded-xl flex items-center justify-center">
                <Calculator className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  AutoCrate Web
                </h1>
                <p className="text-sm text-gray-600">
                  AI-Enhanced Automated Crate Design System v12.1.4
                </p>
              </div>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-4"
            >
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>ASTM Compliant</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Zap className="w-4 h-4 text-blue-500" />
                <span>Real-time Calculations</span>
              </div>
            </motion.div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Input Form */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <CrateForm onCalculate={handleCalculate} isCalculating={isCalculating} />
            </motion.div>
          </div>
          
          {/* Results Display */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              {isCalculating && (
                <div className="card">
                  <LoadingSpinner message="Calculating crate design..." />
                </div>
              )}
              
              {error && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="card border-red-200 bg-red-50 mb-6"
                >
                  <div className="flex items-center space-x-2 text-red-800">
                    <Settings className="w-5 h-5" />
                    <span className="font-medium">Calculation Error</span>
                  </div>
                  <p className="text-red-700 mt-2">{error}</p>
                </motion.div>
              )}
              
              {results && !isCalculating && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <ResultsDisplay 
                    results={results} 
                    onDownloadExpressions={handleDownloadExpressions} 
                  />
                </motion.div>
              )}
              
              {!results && !isCalculating && !error && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="card text-center py-12"
                >
                  <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Ready to Design Your Crate
                  </h3>
                  <p className="text-gray-600 max-w-md mx-auto">
                    Enter your product specifications on the left to generate a complete 
                    crate design with ASTM-compliant calculations, klimp positioning, 
                    and NX expressions.
                  </p>
                  
                  <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto">
                    <div className="flex flex-col items-center p-4 bg-gray-50 rounded-lg">
                      <Calculator className="w-8 h-8 text-autocrate-500 mb-2" />
                      <span className="text-sm font-medium text-gray-900">Smart Calculations</span>
                      <span className="text-xs text-gray-600 text-center">ASTM-compliant structural analysis</span>
                    </div>
                    
                    <div className="flex flex-col items-center p-4 bg-gray-50 rounded-lg">
                      <Settings className="w-8 h-8 text-autocrate-500 mb-2" />
                      <span className="text-sm font-medium text-gray-900">Klimp System</span>
                      <span className="text-xs text-gray-600 text-center">30 L-brackets with 6DOF control</span>
                    </div>
                    
                    <div className="flex flex-col items-center p-4 bg-gray-50 rounded-lg">
                      <Download className="w-8 h-8 text-autocrate-500 mb-2" />
                      <span className="text-sm font-medium text-gray-900">NX Integration</span>
                      <span className="text-xs text-gray-600 text-center">Direct export to Siemens NX</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <p className="text-gray-600 text-sm">
              AutoCrate Web v12.1.4 | AI-Enhanced Engineering Software
            </p>
            <p className="text-gray-500 text-xs mt-1">
              Built with advanced algorithms, ASTM compliance, and modern web technologies
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}