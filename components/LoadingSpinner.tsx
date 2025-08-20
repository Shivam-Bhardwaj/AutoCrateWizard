'use client';

import { motion } from 'framer-motion';
import { Loader2, Calculator, Settings } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  progress?: number;
  stage?: string;
}

export default function LoadingSpinner({ 
  message = "Processing...", 
  progress,
  stage 
}: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      
      {/* Animated Icon */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="relative mb-6"
      >
        {/* Outer ring */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
          className="w-20 h-20 border-4 border-gray-200 rounded-full border-t-autocrate-500"
        />
        
        {/* Inner icon */}
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="absolute inset-0 flex items-center justify-center"
        >
          <Calculator className="w-8 h-8 text-autocrate-600" />
        </motion.div>
      </motion.div>
      
      {/* Message */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="text-center"
      >
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {message}
        </h3>
        
        {stage && (
          <p className="text-sm text-gray-600 mb-4">
            {stage}
          </p>
        )}
        
        {/* Progress Bar */}
        {progress !== undefined && (
          <div className="w-64 bg-gray-200 rounded-full h-2 mb-4">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
              className="bg-autocrate-500 h-2 rounded-full"
            />
          </div>
        )}
        
        {/* Calculation Steps */}
        <div className="flex items-center justify-center space-x-6 text-xs text-gray-500">
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="flex items-center space-x-1"
          >
            <Settings className="w-3 h-3" />
            <span>Analyzing dimensions</span>
          </motion.div>
          
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: 0.5 }}
            className="flex items-center space-x-1"
          >
            <Calculator className="w-3 h-3" />
            <span>ASTM calculations</span>
          </motion.div>
          
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: 1.0 }}
            className="flex items-center space-x-1"
          >
            <Loader2 className="w-3 h-3" />
            <span>Generating results</span>
          </motion.div>
        </div>
      </motion.div>
      
      {/* Background Animation */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        {[...Array(3)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 0.1, scale: 1 }}
            transition={{ delay: i * 0.3, duration: 2 }}
            className="absolute w-32 h-32 bg-autocrate-500 rounded-full blur-3xl"
            style={{
              left: `${20 + i * 30}%`,
              top: `${30 + i * 20}%`,
            }}
          />
        ))}
      </div>
    </div>
  );
}