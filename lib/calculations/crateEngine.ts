// Main Crate Calculation Engine - Ported from Python nx_expressions_generator.py
// Orchestrates all crate calculations and generates complete results

import { CrateInputs, CrateResults, PanelResult, MaterialSummary } from '@/types';
import { calculateSkidResults } from './skidLogic';
import { calculatePlywoodLayout } from './plywoodLayout';
import { calculateKlimpQuaternionOrientations, generateKlimpNXExpressions } from './klimpSystem';

/**
 * Main calculation function that generates complete crate design
 * This is the web equivalent of the Python generate_crate_expressions() function
 */
export function calculateCrateDesign(inputs: CrateInputs): CrateResults {
  
  // 1. Calculate initial crate dimensions
  const initialDimensions = calculateInitialCrateDimensions(inputs);
  
  // 2. Calculate skid requirements
  const skidResults = calculateSkidResults(
    initialDimensions.length,
    initialDimensions.width,
    inputs.productWeight
  );
  
  // 3. Calculate panel dimensions with iterative stabilization
  const panelDimensions = calculateStablePanelDimensions(inputs, initialDimensions);
  
  // 4. Calculate detailed panel components
  const frontPanel = calculatePanelComponents('front', panelDimensions.front, inputs);
  const backPanel = calculatePanelComponents('back', panelDimensions.back, inputs);
  const leftPanel = calculatePanelComponents('left', panelDimensions.left, inputs);
  const rightPanel = calculatePanelComponents('right', panelDimensions.right, inputs);
  const topPanel = calculatePanelComponents('top', panelDimensions.top, inputs);
  
  // 5. Calculate floorboard layout
  const floorboardResults = calculateFloorboardLayout(
    panelDimensions.front.width,
    panelDimensions.left.height,
    inputs.cleatMemberWidth
  );
  
  // 6. Calculate klimp system
  const klimpResults = calculateKlimpQuaternionOrientations(
    panelDimensions.front.width,
    panelDimensions.left.height,
    panelDimensions.left.width,
    inputs.cleatMemberWidth,
    inputs.cleatThickness,
    inputs.panelThickness
  );
  
  // 7. Generate material summary
  const materialSummary = calculateMaterialSummary(
    [frontPanel, backPanel, leftPanel, rightPanel, topPanel],
    skidResults,
    floorboardResults,
    klimpResults
  );
  
  // 8. Generate NX expressions
  const nxExpressions = generateAllNXExpressions(
    panelDimensions,
    skidResults,
    floorboardResults,
    klimpResults,
    inputs
  );
  
  return {
    overallLength: panelDimensions.overall.length,
    overallWidth: panelDimensions.overall.width,
    overallHeight: panelDimensions.overall.height,
    frontPanel,
    backPanel,
    leftPanel,
    rightPanel,
    topPanel,
    skidResults,
    floorboardResults,
    klimpResults,
    materialSummary,
    nxExpressions
  };
}

/**
 * Calculate initial crate dimensions based on product and clearances
 */
function calculateInitialCrateDimensions(inputs: CrateInputs) {
  return {
    length: inputs.productLength + (2 * inputs.clearanceAllSides),
    width: inputs.productWidth + (2 * inputs.clearanceAllSides),
    height: inputs.productHeight + inputs.clearanceTop + inputs.clearanceAllSides
  };
}

/**
 * Calculate stable panel dimensions with iterative adjustment
 * This implements the critical dimension stabilization logic from Python
 */
function calculateStablePanelDimensions(inputs: CrateInputs, initialDimensions: any) {
  let currentLength = initialDimensions.length;
  let currentWidth = initialDimensions.width;
  let currentHeight = initialDimensions.height;
  
  // Iterative stabilization (simplified for web version)
  // In production, this would need the full iterative logic from Python
  
  const panelThickness = inputs.panelThickness;
  const cleatThickness = inputs.cleatThickness;
  const cleatWidth = inputs.cleatMemberWidth;
  
  // Add material thickness adjustments
  const finalLength = currentLength + (2 * panelThickness) + (2 * cleatThickness);
  const finalWidth = currentWidth + (2 * panelThickness) + (2 * cleatThickness);
  const finalHeight = currentHeight + panelThickness + cleatThickness + cleatWidth;
  
  return {
    overall: {
      length: finalLength,
      width: finalWidth,
      height: finalHeight
    },
    front: {
      width: finalWidth - (2 * panelThickness),
      height: finalHeight - panelThickness - cleatThickness - cleatWidth
    },
    back: {
      width: finalWidth - (2 * panelThickness),
      height: finalHeight - panelThickness - cleatThickness - cleatWidth
    },
    left: {
      width: finalLength,
      height: finalHeight - panelThickness - cleatThickness - cleatWidth
    },
    right: {
      width: finalLength,
      height: finalHeight - panelThickness - cleatThickness - cleatWidth
    },
    top: {
      width: finalWidth - (2 * panelThickness),
      length: finalLength
    }
  };
}

/**
 * Calculate components for a specific panel
 */
function calculatePanelComponents(
  panelType: 'front' | 'back' | 'left' | 'right' | 'top',
  dimensions: any,
  inputs: CrateInputs
): PanelResult {
  
  const panelWidth = dimensions.width || dimensions.length;
  const panelHeight = dimensions.height || 0;
  
  // Calculate plywood layout
  const plywoodLayout = calculatePlywoodLayout(panelWidth, panelHeight);
  
  // Calculate cleats (simplified for web version)
  const cleats = calculateBasicCleats(panelWidth, panelHeight, inputs);
  
  // Calculate splice positions
  const splicePositions = plywoodLayout.sheets.length > 1 
    ? calculateSplicePositionsFromSheets(plywoodLayout.sheets)
    : [];
  
  return {
    panelType,
    overallWidth: panelWidth,
    overallHeight: panelHeight,
    plywoodLayout: plywoodLayout.sheets,
    cleats,
    splicePositions
  };
}

/**
 * Calculate basic cleat configuration (simplified)
 */
function calculateBasicCleats(panelWidth: number, panelHeight: number, inputs: CrateInputs) {
  const cleats = [];
  
  // Edge cleats
  cleats.push({
    type: 'edge_vertical' as const,
    length: panelHeight,
    width: inputs.cleatMemberWidth,
    thickness: inputs.cleatThickness,
    positionX: 0,
    positionY: 0,
    count: 2 // Left and right edges
  });
  
  cleats.push({
    type: 'edge_horizontal' as const,
    length: panelWidth,
    width: inputs.cleatMemberWidth,
    thickness: inputs.cleatThickness,
    positionX: 0,
    positionY: 0,
    count: 2 // Top and bottom edges
  });
  
  // Intermediate cleats based on spacing requirements
  const maxSpacing = 24; // ASTM requirement
  if (panelWidth > maxSpacing) {
    const intermediateCount = Math.floor(panelWidth / maxSpacing);
    if (intermediateCount > 0) {
      cleats.push({
        type: 'intermediate_vertical' as const,
        length: panelHeight,
        width: inputs.cleatMemberWidth,
        thickness: inputs.cleatThickness,
        positionX: panelWidth / (intermediateCount + 1),
        positionY: 0,
        count: intermediateCount
      });
    }
  }
  
  return cleats;
}

/**
 * Calculate splice positions from plywood sheet layout
 */
function calculateSplicePositionsFromSheets(sheets: any[]): number[] {
  const splices: number[] = [];
  
  // Group sheets by row to find vertical splices
  const sheetsByRow = new Map<number, any[]>();
  sheets.forEach(sheet => {
    const row = sheet.positionY;
    if (!sheetsByRow.has(row)) {
      sheetsByRow.set(row, []);
    }
    sheetsByRow.get(row)!.push(sheet);
  });
  
  // Find splice positions
  sheetsByRow.forEach(rowSheets => {
    rowSheets.sort((a, b) => a.positionX - b.positionX);
    for (let i = 0; i < rowSheets.length - 1; i++) {
      const spliceX = rowSheets[i].positionX + rowSheets[i].width;
      if (!splices.includes(spliceX)) {
        splices.push(spliceX);
      }
    }
  });
  
  return splices.sort((a, b) => a - b);
}

/**
 * Calculate floorboard layout
 */
function calculateFloorboardLayout(
  floorWidth: number,
  floorLength: number,
  cleatWidth: number
) {
  // Standard lumber widths available
  const standardWidths = [11.25, 9.25, 7.25, 5.5, 3.5, 2.5, 1.5];
  const boards = [];
  let remainingWidth = floorWidth;
  let positionX = 0;
  
  // Greedy algorithm: use largest width that fits
  while (remainingWidth > 0.5) {
    const suitableWidth = standardWidths.find(w => w <= remainingWidth) || 1.5;
    
    boards.push({
      width: suitableWidth,
      length: floorLength,
      positionX,
      count: 1
    });
    
    remainingWidth -= suitableWidth;
    positionX += suitableWidth;
  }
  
  return {
    boards,
    totalWidth: floorWidth,
    centerGap: remainingWidth
  };
}

/**
 * Calculate material summary and cost estimates
 */
function calculateMaterialSummary(
  panels: PanelResult[],
  skidResults: any,
  floorboardResults: any,
  klimpResults: KlimpResult[]
): MaterialSummary {
  
  // Calculate plywood usage
  const totalSheets = panels.reduce((sum, panel) => sum + panel.plywoodLayout.length, 0);
  const totalPlywoodArea = totalSheets * 48 * 96; // Standard sheet area
  const actualPanelArea = panels.reduce((sum, panel) => 
    sum + (panel.overallWidth * panel.overallHeight), 0);
  const wastePercentage = ((totalPlywoodArea - actualPanelArea) / totalPlywoodArea) * 100;
  
  // Calculate lumber usage
  const cleatLinearFeet = panels.reduce((sum, panel) => 
    sum + panel.cleats.reduce((cleatSum, cleat) => 
      cleatSum + (cleat.length * cleat.count / 12), 0), 0);
  
  const skidLinearFeet = (skidResults.lumberCount * skidResults.skidLength) / 12;
  const floorboardLinearFeet = floorboardResults.boards.reduce((sum: number, board: any) => 
    sum + (board.length * board.count / 12), 0);
  
  // Calculate klimp usage
  const klimpsUsed = klimpResults.filter(k => !k.suppress).length;
  
  // Rough cost estimates
  const materialCost = (totalSheets * 50) + (cleatLinearFeet * 2) + (klimpsUsed * 5);
  const laborCost = materialCost * 0.3; // 30% of material cost
  
  return {
    plywood: {
      sheetsUsed: totalSheets,
      totalArea: totalPlywoodArea,
      wastePercentage
    },
    lumber: {
      cleatLinearFeet,
      skidLinearFeet,
      floorboardLinearFeet,
      totalLinearFeet: cleatLinearFeet + skidLinearFeet + floorboardLinearFeet
    },
    hardware: {
      klimpsUsed,
      estimatedScrews: klimpsUsed * 4, // 4 screws per klimp
      estimatedNails: Math.round(cleatLinearFeet * 8) // 8 nails per linear foot
    },
    estimatedCost: {
      materials: materialCost,
      labor: laborCost,
      total: materialCost + laborCost
    }
  };
}

/**
 * Generate all NX expressions for the complete crate design
 */
function generateAllNXExpressions(
  panelDimensions: any,
  skidResults: any,
  floorboardResults: any,
  klimpResults: KlimpResult[],
  inputs: CrateInputs
): string[] {
  
  const expressions: string[] = [];
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  
  // Header comment
  expressions.push(`// AutoCrate NX Expressions - Generated ${timestamp}`);
  expressions.push(`// Product: ${inputs.productLength}x${inputs.productWidth}x${inputs.productHeight}, Weight: ${inputs.productWeight}lbs`);
  expressions.push(`// Materials: ${inputs.panelThickness}" panels, ${inputs.cleatThickness}" cleats`);
  expressions.push('');
  
  // Overall crate dimensions
  expressions.push(`[Inch]CRATE_Overall_Length = ${panelDimensions.overall.length.toFixed(3)}`);
  expressions.push(`[Inch]CRATE_Overall_Width = ${panelDimensions.overall.width.toFixed(3)}`);
  expressions.push(`[Inch]CRATE_Overall_Height = ${panelDimensions.overall.height.toFixed(3)}`);
  expressions.push('');
  
  // Panel assembly dimensions
  expressions.push(`[Inch]PANEL_Front_Assy_Overall_Width = ${panelDimensions.front.width.toFixed(3)}`);
  expressions.push(`[Inch]PANEL_Front_Assy_Overall_Height = ${panelDimensions.front.height.toFixed(3)}`);
  expressions.push(`[Inch]PANEL_Back_Assy_Overall_Width = ${panelDimensions.back.width.toFixed(3)}`);
  expressions.push(`[Inch]PANEL_Back_Assy_Overall_Height = ${panelDimensions.back.height.toFixed(3)}`);
  expressions.push(`[Inch]PANEL_End_Assy_Overall_Length_Face = ${panelDimensions.left.width.toFixed(3)} // For Left & Right End Panels`);
  expressions.push(`[Inch]PANEL_End_Assy_Overall_Height = ${panelDimensions.left.height.toFixed(3)}`);
  expressions.push(`[Inch]PANEL_Top_Assy_Overall_Width = ${panelDimensions.top.width.toFixed(3)}`);
  expressions.push(`[Inch]PANEL_Top_Assy_Overall_Length = ${panelDimensions.top.length.toFixed(3)}`);
  expressions.push('');
  
  // Skid variables
  expressions.push(`SKID_Count = ${skidResults.lumberCount}`);
  expressions.push(`[Inch]SKID_Spacing = ${skidResults.skidSpacing.toFixed(3)}`);
  expressions.push(`[Inch]SKID_Length = ${skidResults.skidLength.toFixed(3)}`);
  expressions.push(`SKID_Lumber_Size = "${skidResults.lumberSize}"`);
  expressions.push('');
  
  // Floorboard variables
  floorboardResults.boards.forEach((board: any, index: number) => {
    expressions.push(`[Inch]FB_Width_${index + 1} = ${board.width.toFixed(3)}`);
    expressions.push(`[Inch]FB_Length_${index + 1} = ${board.length.toFixed(3)}`);
    expressions.push(`[Inch]FB_Position_X_${index + 1} = ${board.positionX.toFixed(3)}`);
  });
  expressions.push(`FB_Board_Count = ${floorboardResults.boards.length}`);
  expressions.push('');
  
  // Material specifications
  expressions.push(`[Inch]Panel_Thickness = ${inputs.panelThickness.toFixed(3)}`);
  expressions.push(`[Inch]Cleat_Thickness = ${inputs.cleatThickness.toFixed(3)}`);
  expressions.push(`[Inch]Cleat_Member_Width = ${inputs.cleatMemberWidth.toFixed(3)}`);
  expressions.push('');
  
  // Klimp system expressions
  const klimpExpressions = generateKlimpNXExpressions(klimpResults);
  expressions.push('// === KLIMP SYSTEM VARIABLES ===');
  expressions.push(...klimpExpressions);
  
  // Critical KL_1_Z variable for total crate height
  const kl1Z = panelDimensions.front.height + inputs.panelThickness + inputs.cleatThickness + inputs.cleatMemberWidth;
  expressions.push('');
  expressions.push(`// Critical height measurement`);
  expressions.push(`[Inch]KL_1_Z = ${kl1Z.toFixed(3)} // Total crate height including top assembly`);
  
  return expressions;
}

/**
 * Validate inputs meet engineering constraints
 */
export function validateInputs(inputs: CrateInputs): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Dimension validations
  if (inputs.productLength < 12 || inputs.productLength > 130) {
    errors.push('Product length must be between 12" and 130"');
  }
  if (inputs.productWidth < 12 || inputs.productWidth > 130) {
    errors.push('Product width must be between 12" and 130"');
  }
  if (inputs.productHeight < 6 || inputs.productHeight > 120) {
    errors.push('Product height must be between 6" and 120"');
  }
  if (inputs.productWeight < 50 || inputs.productWeight > 10000) {
    errors.push('Product weight must be between 50 and 10,000 lbs');
  }
  
  // Material validations
  if (inputs.clearanceAllSides < 0.5 || inputs.clearanceAllSides > 6) {
    errors.push('Clearance must be between 0.5" and 6"');
  }
  if (inputs.panelThickness < 0.25 || inputs.panelThickness > 0.75) {
    errors.push('Panel thickness must be between 0.25" and 0.75"');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Quick test validation - generates test cases for verification
 */
export function generateQuickTestCases(): CrateInputs[] {
  return [
    {
      productLength: 20, productWidth: 20, productHeight: 100, productWeight: 1000,
      clearanceAllSides: 1.0, clearanceTop: 1.0,
      panelThickness: 0.25, cleatThickness: 0.75, cleatMemberWidth: 1.5
    },
    {
      productLength: 96, productWidth: 48, productHeight: 30, productWeight: 500,
      clearanceAllSides: 2.0, clearanceTop: 2.0,
      panelThickness: 0.25, cleatThickness: 0.75, cleatMemberWidth: 3.5
    },
    {
      productLength: 48, productWidth: 48, productHeight: 48, productWeight: 300,
      clearanceAllSides: 1.0, clearanceTop: 1.0,
      panelThickness: 0.25, cleatThickness: 0.75, cleatMemberWidth: 3.5
    }
  ];
}