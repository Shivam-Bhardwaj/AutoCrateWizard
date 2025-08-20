'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { 
  Calculator, 
  Package, 
  Ruler, 
  Weight, 
  Settings2, 
  Zap,
  AlertCircle,
  Info
} from 'lucide-react';
import { CrateInputs, VALIDATION_LIMITS } from '@/types';

// Validation schema using Zod
const crateInputSchema = z.object({
  productLength: z.number()
    .min(VALIDATION_LIMITS.productLength.min, `Minimum ${VALIDATION_LIMITS.productLength.min}"`)
    .max(VALIDATION_LIMITS.productLength.max, `Maximum ${VALIDATION_LIMITS.productLength.max}"`),
  productWidth: z.number()
    .min(VALIDATION_LIMITS.productWidth.min, `Minimum ${VALIDATION_LIMITS.productWidth.min}"`)
    .max(VALIDATION_LIMITS.productWidth.max, `Maximum ${VALIDATION_LIMITS.productWidth.max}"`),
  productHeight: z.number()
    .min(VALIDATION_LIMITS.productHeight.min, `Minimum ${VALIDATION_LIMITS.productHeight.min}"`)
    .max(VALIDATION_LIMITS.productHeight.max, `Maximum ${VALIDATION_LIMITS.productHeight.max}"`),
  productWeight: z.number()
    .min(VALIDATION_LIMITS.productWeight.min, `Minimum ${VALIDATION_LIMITS.productWeight.min} lbs`)
    .max(VALIDATION_LIMITS.productWeight.max, `Maximum ${VALIDATION_LIMITS.productWeight.max} lbs`),
  clearanceAllSides: z.number()
    .min(VALIDATION_LIMITS.clearanceAllSides.min, `Minimum ${VALIDATION_LIMITS.clearanceAllSides.min}"`)
    .max(VALIDATION_LIMITS.clearanceAllSides.max, `Maximum ${VALIDATION_LIMITS.clearanceAllSides.max}"`),
  clearanceTop: z.number()
    .min(VALIDATION_LIMITS.clearanceTop.min, `Minimum ${VALIDATION_LIMITS.clearanceTop.min}"`)
    .max(VALIDATION_LIMITS.clearanceTop.max, `Maximum ${VALIDATION_LIMITS.clearanceTop.max}"`),
  panelThickness: z.number().min(0.25).max(0.75),
  cleatThickness: z.number().min(0.75).max(2.0),
  cleatMemberWidth: z.number().min(1.5).max(5.5),
});

type FormData = z.infer<typeof crateInputSchema>;

interface CrateFormProps {
  onCalculate: (inputs: CrateInputs) => void;
  isCalculating: boolean;
}

export default function CrateForm({ onCalculate, isCalculating }: CrateFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
    reset
  } = useForm<FormData>({
    resolver: zodResolver(crateInputSchema),
    defaultValues: {
      productLength: 48,
      productWidth: 36,
      productHeight: 24,
      productWeight: 150,
      clearanceAllSides: 2.0,
      clearanceTop: 2.0,
      panelThickness: 0.25,
      cleatThickness: 0.75,
      cleatMemberWidth: 3.5,
    }
  });

  const onSubmit = (data: FormData) => {
    onCalculate(data as CrateInputs);
  };

  const loadQuickTestCase = (caseIndex: number) => {
    const quickTestCases = [
      { // Standard medium crate
        productLength: 48, productWidth: 36, productHeight: 24, productWeight: 150,
        clearanceAllSides: 2.0, clearanceTop: 2.0,
        panelThickness: 0.25, cleatThickness: 0.75, cleatMemberWidth: 3.5
      },
      { // Large heavy crate
        productLength: 96, productWidth: 72, productHeight: 48, productWeight: 2000,
        clearanceAllSides: 3.0, clearanceTop: 3.0,
        panelThickness: 0.5, cleatThickness: 1.5, cleatMemberWidth: 3.5
      },
      { // Small light crate
        productLength: 24, productWidth: 18, productHeight: 12, productWeight: 75,
        clearanceAllSides: 1.0, clearanceTop: 1.0,
        panelThickness: 0.25, cleatThickness: 0.75, cleatMemberWidth: 1.5
      }
    ];
    
    const testCase = quickTestCases[caseIndex];
    Object.entries(testCase).forEach(([key, value]) => {
      setValue(key as keyof FormData, value);
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Form Header */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center space-x-2">
            <Package className="w-5 h-5 text-autocrate-600" />
            <h2 className="text-lg font-semibold text-gray-900">Crate Specifications</h2>
          </div>
          <div className="flex space-x-2">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="btn-outline text-xs py-1"
            >
              <Settings2 className="w-3 h-3 mr-1" />
              Advanced
            </button>
          </div>
        </div>
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          
          {/* Product Dimensions */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2 mb-3">
              <Ruler className="w-4 h-4 text-autocrate-600" />
              <h3 className="font-medium text-gray-900">Product Dimensions</h3>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="form-label">Length</label>
                <div className="flex items-center">
                  <input
                    {...register('productLength', { valueAsNumber: true })}
                    type="number"
                    step="0.25"
                    className="engineering-input"
                    placeholder="48"
                  />
                  <span className="engineering-unit">inches</span>
                </div>
                {errors.productLength && (
                  <p className="form-error">{errors.productLength.message}</p>
                )}
              </div>
              
              <div>
                <label className="form-label">Width</label>
                <div className="flex items-center">
                  <input
                    {...register('productWidth', { valueAsNumber: true })}
                    type="number"
                    step="0.25"
                    className="engineering-input"
                    placeholder="36"
                  />
                  <span className="engineering-unit">inches</span>
                </div>
                {errors.productWidth && (
                  <p className="form-error">{errors.productWidth.message}</p>
                )}
              </div>
              
              <div>
                <label className="form-label">Height</label>
                <div className="flex items-center">
                  <input
                    {...register('productHeight', { valueAsNumber: true })}
                    type="number"
                    step="0.25"
                    className="engineering-input"
                    placeholder="24"
                  />
                  <span className="engineering-unit">inches</span>
                </div>
                {errors.productHeight && (
                  <p className="form-error">{errors.productHeight.message}</p>
                )}
              </div>
            </div>
          </div>

          {/* Product Weight */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2 mb-3">
              <Weight className="w-4 h-4 text-autocrate-600" />
              <h3 className="font-medium text-gray-900">Product Weight</h3>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Total Weight</label>
                <div className="flex items-center">
                  <input
                    {...register('productWeight', { valueAsNumber: true })}
                    type="number"
                    step="10"
                    className="engineering-input"
                    placeholder="150"
                  />
                  <span className="engineering-unit">lbs</span>
                </div>
                {errors.productWeight && (
                  <p className="form-error">{errors.productWeight.message}</p>
                )}
              </div>
            </div>
          </div>

          {/* Clearances */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2 mb-3">
              <Info className="w-4 h-4 text-autocrate-600" />
              <h3 className="font-medium text-gray-900">Clearances</h3>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="form-label">All Sides</label>
                <div className="flex items-center">
                  <input
                    {...register('clearanceAllSides', { valueAsNumber: true })}
                    type="number"
                    step="0.25"
                    className="engineering-input"
                    placeholder="2.0"
                  />
                  <span className="engineering-unit">inches</span>
                </div>
                {errors.clearanceAllSides && (
                  <p className="form-error">{errors.clearanceAllSides.message}</p>
                )}
              </div>
              
              <div>
                <label className="form-label">Top</label>
                <div className="flex items-center">
                  <input
                    {...register('clearanceTop', { valueAsNumber: true })}
                    type="number"
                    step="0.25"
                    className="engineering-input"
                    placeholder="2.0"
                  />
                  <span className="engineering-unit">inches</span>
                </div>
                {errors.clearanceTop && (
                  <p className="form-error">{errors.clearanceTop.message}</p>
                )}
              </div>
            </div>
          </div>

          {/* Advanced Materials Section */}
          {showAdvanced && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="space-y-4 border-t border-gray-200 pt-6"
            >
              <div className="flex items-center space-x-2 mb-3">
                <Settings2 className="w-4 h-4 text-autocrate-600" />
                <h3 className="font-medium text-gray-900">Material Specifications</h3>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="form-label">Panel Thickness</label>
                  <select
                    {...register('panelThickness', { valueAsNumber: true })}
                    className="form-input"
                  >
                    <option value={0.25}>1/4" (0.25")</option>
                    <option value={0.5}>1/2" (0.5")</option>
                    <option value={0.75}>3/4" (0.75")</option>
                  </select>
                </div>
                
                <div>
                  <label className="form-label">Cleat Thickness</label>
                  <select
                    {...register('cleatThickness', { valueAsNumber: true })}
                    className="form-input"
                  >
                    <option value={0.75}>3/4" (0.75")</option>
                    <option value={1.5}>1 1/2" (1.5")</option>
                    <option value={2.0}>2" (2.0")</option>
                  </select>
                </div>
                
                <div>
                  <label className="form-label">Cleat Width</label>
                  <select
                    {...register('cleatMemberWidth', { valueAsNumber: true })}
                    className="form-input"
                  >
                    <option value={1.5}>2x2 (1.5")</option>
                    <option value={2.5}>2x3 (2.5")</option>
                    <option value={3.5}>2x4 (3.5")</option>
                    <option value={5.5}>2x6 (5.5")</option>
                  </select>
                </div>
              </div>
            </motion.div>
          )}

          {/* Action Buttons */}
          <div className="space-y-4 border-t border-gray-200 pt-6">
            
            {/* Quick Test Cases */}
            <div>
              <label className="form-label mb-2">Quick Test Cases</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => loadQuickTestCase(0)}
                  className="btn-outline text-xs py-2"
                >
                  <Zap className="w-3 h-3 mr-1" />
                  Standard
                </button>
                <button
                  type="button"
                  onClick={() => loadQuickTestCase(1)}
                  className="btn-outline text-xs py-2"
                >
                  <Package className="w-3 h-3 mr-1" />
                  Large Heavy
                </button>
                <button
                  type="button"
                  onClick={() => loadQuickTestCase(2)}
                  className="btn-outline text-xs py-2"
                >
                  <Ruler className="w-3 h-3 mr-1" />
                  Small Light
                </button>
              </div>
            </div>
            
            {/* Main Calculate Button */}
            <button
              type="submit"
              disabled={isCalculating}
              className={`w-full btn-primary py-3 text-base font-semibold ${
                isCalculating ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {isCalculating ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="spinner w-5 h-5"></div>
                  <span>Calculating...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center space-x-2">
                  <Calculator className="w-5 h-5" />
                  <span>Generate Crate Design</span>
                </div>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Input Summary Card */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <Info className="w-4 h-4 text-blue-600" />
          <h3 className="font-medium text-gray-900">Design Summary</h3>
        </div>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Product Size:</span>
            <span className="font-mono">
              {watch('productLength') || 0}" × {watch('productWidth') || 0}" × {watch('productHeight') || 0}"
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Weight:</span>
            <span className="font-mono">{watch('productWeight') || 0} lbs</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Clearance:</span>
            <span className="font-mono">{watch('clearanceAllSides') || 0}"</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Panel Material:</span>
            <span className="font-mono">{watch('panelThickness') || 0}" plywood</span>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-blue-800">
            <strong>ASTM Compliant:</strong> All calculations follow industry standards 
            for structural integrity and safety factors.
          </p>
        </div>
      </div>

      {/* Help Information */}
      <div className="card bg-gray-50">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-gray-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Engineering Notes</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Dimensions are interior product measurements</li>
              <li>• Weight determines skid lumber sizing automatically</li>
              <li>• Clearances ensure proper fit and access</li>
              <li>• Material options affect structural calculations</li>
              <li>• Klimp system provides L-bracket reinforcement</li>
            </ul>
          </div>
        </div>
      </div>
    </motion.div>
  );
}