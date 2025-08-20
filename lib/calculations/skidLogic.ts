// Skid Logic - Ported from Python skid_logic.py
// Calculates skid lumber properties and layout based on product weight

import { SkidResult } from '@/types';

interface SkidLumberProperties {
  lumberSize: string;
  maxSpacing: number;
}

interface SkidLayoutResult {
  skidCount: number;
  skidSpacing: number;
  firstSkidPosition: number;
}

/**
 * Calculate skid lumber size and maximum spacing based on product weight
 * Based on ASTM standards and structural engineering principles
 */
export function calculateSkidLumberProperties(productWeight: number): SkidLumberProperties {
  // Weight thresholds based on load capacity and deflection limits
  if (productWeight <= 500) {
    return {
      lumberSize: "2x4",
      maxSpacing: 48.0  // 4 feet maximum spacing for light loads
    };
  } else if (productWeight <= 1000) {
    return {
      lumberSize: "2x6", 
      maxSpacing: 36.0  // 3 feet spacing for medium loads
    };
  } else if (productWeight <= 2000) {
    return {
      lumberSize: "4x4",
      maxSpacing: 30.0  // 2.5 feet spacing for heavier loads
    };
  } else if (productWeight <= 4000) {
    return {
      lumberSize: "4x6",
      maxSpacing: 24.0  // 2 feet spacing for heavy loads
    };
  } else if (productWeight <= 6000) {
    return {
      lumberSize: "6x6",
      maxSpacing: 20.0  // Closer spacing for very heavy loads
    };
  } else {
    return {
      lumberSize: "8x8",
      maxSpacing: 16.0  // Maximum structural support for extreme loads
    };
  }
}

/**
 * Calculate optimal skid layout for given crate width and weight
 */
export function calculateSkidLayout(
  crateWidth: number,
  productWeight: number
): SkidLayoutResult {
  const skidProperties = calculateSkidLumberProperties(productWeight);
  const maxSpacing = skidProperties.maxSpacing;
  
  // Calculate minimum number of skids needed
  // Always need at least 2 skids, add more based on spacing requirements
  let skidCount = 2;
  
  // Calculate spacing with 2 skids first
  let currentSpacing = crateWidth;
  
  // Add skids until spacing is within limits
  while (currentSpacing > maxSpacing && skidCount < 10) {
    skidCount++;
    // Spacing between skids = total width / (count - 1)
    currentSpacing = crateWidth / (skidCount - 1);
  }
  
  // Calculate actual spacing and positioning
  const actualSpacing = crateWidth / (skidCount - 1);
  
  // First skid starts at edge, last skid ends at edge
  const firstSkidPosition = 0;
  
  return {
    skidCount,
    skidSpacing: actualSpacing,
    firstSkidPosition
  };
}

/**
 * Calculate complete skid results for given crate dimensions and weight
 */
export function calculateSkidResults(
  crateLength: number,
  crateWidth: number, 
  productWeight: number
): SkidResult {
  const skidProperties = calculateSkidLumberProperties(productWeight);
  const skidLayout = calculateSkidLayout(crateWidth, productWeight);
  
  return {
    lumberSize: skidProperties.lumberSize,
    lumberCount: skidLayout.skidCount,
    skidSpacing: skidLayout.skidSpacing,
    skidLength: crateLength,
    firstSkidPosition: skidLayout.firstSkidPosition
  };
}

/**
 * Get lumber dimensions for standard sizes
 */
export function getLumberDimensions(lumberSize: string): { width: number; height: number } {
  const dimensions: Record<string, { width: number; height: number }> = {
    "2x4": { width: 1.5, height: 3.5 },
    "2x6": { width: 1.5, height: 5.5 },
    "4x4": { width: 3.5, height: 3.5 },
    "4x6": { width: 3.5, height: 5.5 },
    "6x6": { width: 5.5, height: 5.5 },
    "8x8": { width: 7.25, height: 7.25 }
  };
  
  return dimensions[lumberSize] || { width: 3.5, height: 3.5 };
}

/**
 * Calculate linear feet of lumber needed for skids
 */
export function calculateSkidLinearFeet(skidResult: SkidResult): number {
  return skidResult.lumberCount * skidResult.skidLength;
}

/**
 * Validate skid design meets structural requirements
 */
export function validateSkidDesign(
  skidResult: SkidResult,
  productWeight: number
): { valid: boolean; warnings: string[] } {
  const warnings: string[] = [];
  let valid = true;
  
  // Check if skid spacing is reasonable
  if (skidResult.skidSpacing > 48) {
    warnings.push(`Skid spacing (${skidResult.skidSpacing.toFixed(1)}") exceeds recommended maximum of 48"`);
    valid = false;
  }
  
  // Check if enough skids for the weight
  const recommendedProperties = calculateSkidLumberProperties(productWeight);
  if (skidResult.skidSpacing > recommendedProperties.maxSpacing) {
    warnings.push(`Skid spacing exceeds recommended maximum for ${productWeight} lb load`);
    valid = false;
  }
  
  // Check minimum skid count
  if (skidResult.lumberCount < 2) {
    warnings.push("At least 2 skids are required for structural stability");
    valid = false;
  }
  
  return { valid, warnings };
}