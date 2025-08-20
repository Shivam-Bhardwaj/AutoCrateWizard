// Plywood Layout Logic - Ported from Python plywood_layout_generator.py
// Optimizes plywood sheet layout to minimize waste

import { PlywoodSheet } from '@/types';

interface PlywoodLayoutResult {
  sheets: PlywoodSheet[];
  totalSheetsUsed: number;
  wastePercentage: number;
  totalArea: number;
  orientation: 'standard' | 'rotated';
}

interface LayoutOption {
  orientation: 'standard' | 'rotated';
  sheetsWide: number;
  sheetsHigh: number;
  totalSheets: number;
  horizontalSplices: number;
  verticalSplices: number;
  wasteArea: number;
}

// Standard plywood sheet dimensions
const STANDARD_SHEET = {
  width: 48,   // 4 feet
  height: 96   // 8 feet
};

/**
 * Calculate optimal plywood layout for a given panel size
 * Minimizes sheet count and considers splice placement
 */
export function calculatePlywoodLayout(
  panelWidth: number,
  panelHeight: number
): PlywoodLayoutResult {
  
  // Calculate both orientations
  const standardLayout = calculateLayoutOption(panelWidth, panelHeight, 'standard');
  const rotatedLayout = calculateLayoutOption(panelWidth, panelHeight, 'rotated');
  
  // Choose the better option based on multiple criteria
  const selectedLayout = chooseBestLayout(standardLayout, rotatedLayout);
  
  // Generate sheet positioning
  const sheets = generateSheetPositions(
    panelWidth,
    panelHeight,
    selectedLayout
  );
  
  const totalArea = sheets.length * STANDARD_SHEET.width * STANDARD_SHEET.height;
  const panelArea = panelWidth * panelHeight;
  const wastePercentage = ((totalArea - panelArea) / totalArea) * 100;
  
  return {
    sheets,
    totalSheetsUsed: selectedLayout.totalSheets,
    wastePercentage,
    totalArea,
    orientation: selectedLayout.orientation
  };
}

/**
 * Calculate layout option for a specific orientation
 */
function calculateLayoutOption(
  panelWidth: number,
  panelHeight: number,
  orientation: 'standard' | 'rotated'
): LayoutOption {
  
  let sheetW = STANDARD_SHEET.width;
  let sheetH = STANDARD_SHEET.height;
  
  if (orientation === 'rotated') {
    [sheetW, sheetH] = [sheetH, sheetW]; // Swap dimensions
  }
  
  // Calculate sheets needed in each direction
  const sheetsWide = Math.ceil(panelWidth / sheetW);
  const sheetsHigh = Math.ceil(panelHeight / sheetH);
  const totalSheets = sheetsWide * sheetsHigh;
  
  // Calculate splice counts
  const verticalSplices = Math.max(0, sheetsWide - 1);
  const horizontalSplices = Math.max(0, sheetsHigh - 1);
  
  // Calculate waste area
  const coveredWidth = sheetsWide * sheetW;
  const coveredHeight = sheetsHigh * sheetH;
  const totalCoveredArea = coveredWidth * coveredHeight;
  const panelArea = panelWidth * panelHeight;
  const wasteArea = totalCoveredArea - panelArea;
  
  return {
    orientation,
    sheetsWide,
    sheetsHigh,
    totalSheets,
    horizontalSplices,
    verticalSplices,
    wasteArea
  };
}

/**
 * Choose the best layout option based on multiple criteria
 */
function chooseBestLayout(
  standardLayout: LayoutOption,
  rotatedLayout: LayoutOption
): LayoutOption {
  
  // Primary criterion: fewer sheets
  if (standardLayout.totalSheets !== rotatedLayout.totalSheets) {
    return standardLayout.totalSheets < rotatedLayout.totalSheets 
      ? standardLayout 
      : rotatedLayout;
  }
  
  // Secondary criterion: fewer horizontal splices (structurally preferred)
  if (standardLayout.horizontalSplices !== rotatedLayout.horizontalSplices) {
    return standardLayout.horizontalSplices < rotatedLayout.horizontalSplices
      ? standardLayout
      : rotatedLayout;
  }
  
  // Tertiary criterion: less waste
  if (Math.abs(standardLayout.wasteArea - rotatedLayout.wasteArea) > 0.1) {
    return standardLayout.wasteArea < rotatedLayout.wasteArea
      ? standardLayout
      : rotatedLayout;
  }
  
  // Default to standard orientation
  return standardLayout;
}

/**
 * Generate actual sheet positions for the selected layout
 */
function generateSheetPositions(
  panelWidth: number,
  panelHeight: number,
  layout: LayoutOption
): PlywoodSheet[] {
  
  const sheets: PlywoodSheet[] = [];
  let sheetId = 1;
  
  let sheetW = STANDARD_SHEET.width;
  let sheetH = STANDARD_SHEET.height;
  
  if (layout.orientation === 'rotated') {
    [sheetW, sheetH] = [sheetH, sheetW];
  }
  
  // Generate sheets in row-major order
  for (let row = 0; row < layout.sheetsHigh; row++) {
    for (let col = 0; col < layout.sheetsWide; col++) {
      const positionX = col * sheetW;
      const positionY = row * sheetH;
      
      // Calculate actual sheet dimensions (may be clipped at edges)
      const actualWidth = Math.min(sheetW, panelWidth - positionX);
      const actualHeight = Math.min(sheetH, panelHeight - positionY);
      
      sheets.push({
        id: sheetId++,
        width: actualWidth,
        height: actualHeight,
        positionX,
        positionY,
        orientation: layout.orientation
      });
    }
  }
  
  return sheets;
}

/**
 * Calculate splice positions for a panel layout
 */
export function calculateSplicePositions(
  panelWidth: number,
  panelHeight: number,
  layout: PlywoodLayoutResult
): { vertical: number[]; horizontal: number[] } {
  
  const vertical: number[] = [];
  const horizontal: number[] = [];
  
  let sheetW = STANDARD_SHEET.width;
  let sheetH = STANDARD_SHEET.height;
  
  if (layout.orientation === 'rotated') {
    [sheetW, sheetH] = [sheetH, sheetW];
  }
  
  // Calculate vertical splice positions
  for (let col = 1; col * sheetW < panelWidth; col++) {
    vertical.push(col * sheetW);
  }
  
  // Calculate horizontal splice positions  
  for (let row = 1; row * sheetH < panelHeight; row++) {
    horizontal.push(row * sheetH);
  }
  
  return { vertical, horizontal };
}

/**
 * Calculate material efficiency metrics
 */
export function calculateMaterialEfficiency(
  layouts: PlywoodLayoutResult[]
): {
  totalSheets: number;
  totalWaste: number;
  averageEfficiency: number;
  costEstimate: number;
} {
  
  const totalSheets = layouts.reduce((sum, layout) => sum + layout.totalSheetsUsed, 0);
  const totalArea = layouts.reduce((sum, layout) => sum + layout.totalArea, 0);
  const wasteArea = layouts.reduce((sum, layout) => 
    sum + (layout.totalArea * layout.wastePercentage / 100), 0);
  
  const averageEfficiency = ((totalArea - wasteArea) / totalArea) * 100;
  
  // Rough cost estimate (assuming $50 per 4x8 sheet)
  const costEstimate = totalSheets * 50;
  
  return {
    totalSheets,
    totalWaste: wasteArea,
    averageEfficiency,
    costEstimate
  };
}

/**
 * Validate plywood layout meets practical constraints
 */
export function validatePlywoodLayout(
  layout: PlywoodLayoutResult,
  panelWidth: number,
  panelHeight: number
): { valid: boolean; warnings: string[] } {
  
  const warnings: string[] = [];
  let valid = true;
  
  // Check for excessive waste
  if (layout.wastePercentage > 50) {
    warnings.push(`High material waste: ${layout.wastePercentage.toFixed(1)}%`);
  }
  
  // Check for too many splices
  const splices = calculateSplicePositions(panelWidth, panelHeight, layout);
  if (splices.horizontal.length > 2) {
    warnings.push(`Many horizontal splices (${splices.horizontal.length}) may reduce strength`);
  }
  
  // Check for very small edge pieces
  const minPieceSize = 6; // inches
  layout.sheets.forEach(sheet => {
    if (sheet.width < minPieceSize || sheet.height < minPieceSize) {
      warnings.push(`Small edge piece: ${sheet.width}" x ${sheet.height}"`);
    }
  });
  
  return { valid, warnings };
}