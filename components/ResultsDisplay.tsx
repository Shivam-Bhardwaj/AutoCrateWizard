'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Download, 
  FileText, 
  BarChart3, 
  Settings, 
  Package, 
  Layers,
  CheckCircle,
  Eye,
  EyeOff,
  Copy,
  ExternalLink
} from 'lucide-react';
import { CrateResults } from '@/types';

interface ResultsDisplayProps {
  results: CrateResults;
  onDownloadExpressions: () => void;
}

export default function ResultsDisplay({ results, onDownloadExpressions }: ResultsDisplayProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'klimps' | 'materials' | 'expressions'>('overview');
  const [showSuppressedKlimps, setShowSuppressedKlimps] = useState(false);
  
  const visibleKlimps = results.klimpResults.filter(k => !k.suppress);
  const suppressedKlimps = results.klimpResults.filter(k => k.suppress);
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'klimps', label: 'Klimp System', icon: Settings },
    { id: 'materials', label: 'Materials', icon: Package },
    { id: 'expressions', label: 'NX Expressions', icon: FileText },
  ];

  return (
    <div className="space-y-6">
      
      {/* Results Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Crate Design Complete
              </h2>
              <p className="text-gray-600">
                {results.overallLength.toFixed(1)}" × {results.overallWidth.toFixed(1)}" × {results.overallHeight.toFixed(1)}"
              </p>
            </div>
          </div>
          
          <button
            onClick={onDownloadExpressions}
            className="btn-primary flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Download .EXP</span>
          </button>
        </div>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-200">
          <div className="text-center">
            <div className="metric-value">{visibleKlimps.length}</div>
            <div className="metric-label">Active Klimps</div>
          </div>
          <div className="text-center">
            <div className="metric-value">{results.materialSummary.plywood.sheetsUsed}</div>
            <div className="metric-label">Plywood Sheets</div>
          </div>
          <div className="text-center">
            <div className="metric-value">{results.materialSummary.lumber.totalLinearFeet.toFixed(0)}</div>
            <div className="metric-label">Lumber (ft)</div>
          </div>
          <div className="text-center">
            <div className="metric-value">${results.materialSummary.estimatedCost.total.toFixed(0)}</div>
            <div className="metric-label">Est. Cost</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="card p-0">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-autocrate-500 text-autocrate-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
        
        <div className="p-6">
          <AnimatePresence mode="wait">
            
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <motion.div
                key="overview"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                <div className="results-grid">
                  
                  {/* Panel Summary */}
                  <div className="metric-card">
                    <div className="flex items-center space-x-2 mb-3">
                      <Layers className="w-5 h-5 text-autocrate-600" />
                      <h3 className="font-medium">Panel Summary</h3>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Front/Back:</span>
                        <span className="font-mono">
                          {results.frontPanel.overallWidth.toFixed(1)}" × {results.frontPanel.overallHeight.toFixed(1)}"
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Left/Right:</span>
                        <span className="font-mono">
                          {results.leftPanel.overallWidth.toFixed(1)}" × {results.leftPanel.overallHeight.toFixed(1)}"
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Top:</span>
                        <span className="font-mono">
                          {results.topPanel.overallWidth.toFixed(1)}" × {results.topPanel.overallHeight.toFixed(1)}"
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Skid Information */}
                  <div className="metric-card">
                    <h3 className="font-medium mb-3">Skid System</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Lumber Size:</span>
                        <span className="font-mono">{results.skidResults.lumberSize}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Count:</span>
                        <span className="font-mono">{results.skidResults.lumberCount}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Spacing:</span>
                        <span className="font-mono">{results.skidResults.skidSpacing.toFixed(1)}"</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Material Efficiency */}
                  <div className="metric-card">
                    <h3 className="font-medium mb-3">Efficiency</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Plywood Waste:</span>
                        <span className="font-mono text-green-600">
                          {results.materialSummary.plywood.wastePercentage.toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Total Sheets:</span>
                        <span className="font-mono">{results.materialSummary.plywood.sheetsUsed}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Klimp System Tab */}
            {activeTab === 'klimps' && (
              <motion.div
                key="klimps"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">Klimp System (L-Brackets)</h3>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">
                      {visibleKlimps.length} of 30 klimps active
                    </span>
                    <button
                      onClick={() => setShowSuppressedKlimps(!showSuppressedKlimps)}
                      className="btn-outline text-xs"
                    >
                      {showSuppressedKlimps ? <EyeOff className="w-3 h-3 mr-1" /> : <Eye className="w-3 h-3 mr-1" />}
                      {showSuppressedKlimps ? 'Hide' : 'Show'} Suppressed
                    </button>
                  </div>
                </div>
                
                {/* Klimp Groups */}
                <div className="space-y-4">
                  {['top', 'left', 'right'].map(panel => {
                    const panelKlimps = results.klimpResults.filter(k => 
                      k.panel === panel && (showSuppressedKlimps || !k.suppress)
                    );
                    
                    return (
                      <div key={panel} className="bg-gray-50 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-3 capitalize">
                          {panel} Panel Klimps (KL_{panel === 'top' ? '1-10' : panel === 'left' ? '11-20' : '21-30'})
                        </h4>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                          {panelKlimps.map(klimp => (
                            <div
                              key={klimp.id}
                              className={`p-3 rounded-lg border ${
                                klimp.suppress 
                                  ? 'bg-gray-100 border-gray-300 opacity-50' 
                                  : 'bg-white border-green-200'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-mono text-sm font-medium">
                                  KL_{klimp.id}
                                </span>
                                <span className={`text-xs px-2 py-1 rounded ${
                                  klimp.suppress 
                                    ? 'bg-gray-200 text-gray-600' 
                                    : 'bg-green-100 text-green-700'
                                }`}>
                                  {klimp.suppress ? 'Hidden' : 'Active'}
                                </span>
                              </div>
                              
                              <div className="space-y-1 text-xs text-gray-600">
                                <div className="flex justify-between">
                                  <span>X:</span>
                                  <span className="font-mono">{klimp.positionX.toFixed(2)}"</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Y:</span>
                                  <span className="font-mono">{klimp.positionY.toFixed(2)}"</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Z:</span>
                                  <span className="font-mono">{klimp.positionZ.toFixed(2)}"</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Rot:</span>
                                  <span className="font-mono">{klimp.eulerAngles.rz.toFixed(0)}°</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        {panelKlimps.length === 0 && (
                          <p className="text-gray-500 text-sm text-center py-4">
                            No {showSuppressedKlimps ? '' : 'active '}klimps on this panel
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            )}

            {/* Materials Tab */}
            {activeTab === 'materials' && (
              <motion.div
                key="materials"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                <div className="results-grid">
                  
                  {/* Plywood Summary */}
                  <div className="metric-card">
                    <h3 className="font-medium mb-4 flex items-center space-x-2">
                      <Layers className="w-5 h-5 text-autocrate-600" />
                      <span>Plywood Usage</span>
                    </h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Sheets (4'×8'):</span>
                        <span className="font-mono font-medium">{results.materialSummary.plywood.sheetsUsed}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Area:</span>
                        <span className="font-mono">{results.materialSummary.plywood.totalArea.toFixed(0)} sq ft</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Waste:</span>
                        <span className={`font-mono ${
                          results.materialSummary.plywood.wastePercentage < 15 ? 'text-green-600' :
                          results.materialSummary.plywood.wastePercentage < 25 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {results.materialSummary.plywood.wastePercentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Lumber Summary */}
                  <div className="metric-card">
                    <h3 className="font-medium mb-4">Lumber Requirements</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Cleats:</span>
                        <span className="font-mono">{results.materialSummary.lumber.cleatLinearFeet.toFixed(0)} ft</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Skids:</span>
                        <span className="font-mono">{results.materialSummary.lumber.skidLinearFeet.toFixed(0)} ft</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Floorboards:</span>
                        <span className="font-mono">{results.materialSummary.lumber.floorboardLinearFeet.toFixed(0)} ft</span>
                      </div>
                      <div className="flex justify-between font-medium border-t border-gray-200 pt-2">
                        <span>Total Lumber:</span>
                        <span className="font-mono">{results.materialSummary.lumber.totalLinearFeet.toFixed(0)} ft</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Hardware Summary */}
                  <div className="metric-card">
                    <h3 className="font-medium mb-4">Hardware</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Klimps:</span>
                        <span className="font-mono">{results.materialSummary.hardware.klimpsUsed}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Screws (est):</span>
                        <span className="font-mono">{results.materialSummary.hardware.estimatedScrews}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Nails (est):</span>
                        <span className="font-mono">{results.materialSummary.hardware.estimatedNails}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Cost Breakdown */}
                <div className="card bg-gradient-to-br from-autocrate-50 to-blue-50">
                  <h3 className="font-medium mb-4">Cost Estimate</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-autocrate-600">
                        ${results.materialSummary.estimatedCost.materials.toFixed(0)}
                      </div>
                      <div className="text-sm text-gray-600">Materials</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-autocrate-600">
                        ${results.materialSummary.estimatedCost.labor.toFixed(0)}
                      </div>
                      <div className="text-sm text-gray-600">Labor</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-engineering-800">
                        ${results.materialSummary.estimatedCost.total.toFixed(0)}
                      </div>
                      <div className="text-sm text-gray-600 font-medium">Total</div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* NX Expressions Tab */}
            {activeTab === 'expressions' && (
              <motion.div
                key="expressions"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">NX Expressions File Preview</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => copyToClipboard(results.nxExpressions.join('\n'))}
                      className="btn-outline text-xs"
                    >
                      <Copy className="w-3 h-3 mr-1" />
                      Copy All
                    </button>
                    <button
                      onClick={onDownloadExpressions}
                      className="btn-primary text-xs"
                    >
                      <Download className="w-3 h-3 mr-1" />
                      Download
                    </button>
                  </div>
                </div>
                
                <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <pre className="text-green-400 text-xs font-mono leading-relaxed">
                    {results.nxExpressions.slice(0, 50).join('\n')}
                    {results.nxExpressions.length > 50 && (
                      <div className="text-gray-500 mt-4">
                        ... and {results.nxExpressions.length - 50} more lines
                      </div>
                    )}
                  </pre>
                </div>
                
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <ExternalLink className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-blue-900 mb-1">Siemens NX Import</h4>
                      <p className="text-sm text-blue-800 mb-2">
                        To use this file in Siemens NX:
                      </p>
                      <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
                        <li>Download the .exp file using the button above</li>
                        <li>Open your NX crate assembly model</li>
                        <li>Go to Tools → Expressions</li>
                        <li>Click "Import Expressions from File"</li>
                        <li>Select the downloaded .exp file</li>
                        <li>Choose "Replace Existing" and click OK</li>
                        <li>Update the model to see changes</li>
                      </ol>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}