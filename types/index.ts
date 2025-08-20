// AutoCrate Web Types - Complete type definitions for web application

export interface CrateInputs {
  // Product dimensions
  productLength: number;
  productWidth: number;
  productHeight: number;
  productWeight: number;
  
  // Clearances
  clearanceAllSides: number;
  clearanceTop: number;
  
  // Material specifications
  panelThickness: number;
  cleatThickness: number;
  cleatMemberWidth: number;
  
  // Advanced options
  enableQuickTest?: boolean;
  enableSpliceOptimization?: boolean;
}

export interface CrateResults {
  // Overall dimensions
  overallLength: number;
  overallWidth: number;
  overallHeight: number;
  
  // Panel results
  frontPanel: PanelResult;
  backPanel: PanelResult;
  leftPanel: PanelResult;
  rightPanel: PanelResult;
  topPanel: PanelResult;
  
  // Skid and floorboard results
  skidResults: SkidResult;
  floorboardResults: FloorboardResult;
  
  // Klimp results
  klimpResults: KlimpResult[];
  
  // Material summary
  materialSummary: MaterialSummary;
  
  // NX expressions
  nxExpressions: string[];
}

export interface PanelResult {
  panelType: 'front' | 'back' | 'left' | 'right' | 'top';
  overallWidth: number;
  overallHeight: number;
  plywoodLayout: PlywoodSheet[];
  cleats: CleatResult[];
  splicePositions: number[];
}

export interface PlywoodSheet {
  id: number;
  width: number;
  height: number;
  positionX: number;
  positionY: number;
  orientation: 'standard' | 'rotated';
}

export interface CleatResult {
  type: 'edge_vertical' | 'edge_horizontal' | 'intermediate_vertical' | 'intermediate_horizontal';
  length: number;
  width: number;
  thickness: number;
  positionX: number;
  positionY: number;
  count: number;
}

export interface SkidResult {
  lumberSize: string; // e.g., "4x4", "4x6"
  lumberCount: number;
  skidSpacing: number;
  skidLength: number;
  firstSkidPosition: number;
}

export interface FloorboardResult {
  boards: FloorboardInfo[];
  totalWidth: number;
  centerGap: number;
}

export interface FloorboardInfo {
  width: number;
  length: number;
  positionX: number;
  count: number;
}

export interface KlimpResult {
  id: number; // KL_1 to KL_30
  panel: 'top' | 'left' | 'right';
  positionX: number;
  positionY: number;
  positionZ: number;
  
  // Quaternion orientation
  quaternion: {
    w: number;
    x: number;
    y: number;
    z: number;
  };
  
  // Direction vectors for NX
  directionVectors: {
    x: [number, number, number];
    y: [number, number, number];
    z: [number, number, number];
  };
  
  // Legacy orientation for compatibility
  eulerAngles: {
    rx: number;
    ry: number;
    rz: number;
  };
  
  // Control flags
  suppress: boolean; // true = hide, false = show
}

export interface MaterialSummary {
  plywood: {
    sheetsUsed: number;
    totalArea: number;
    wastePercentage: number;
  };
  lumber: {
    cleatLinearFeet: number;
    skidLinearFeet: number;
    floorboardLinearFeet: number;
    totalLinearFeet: number;
  };
  hardware: {
    klimpsUsed: number;
    estimatedScrews: number;
    estimatedNails: number;
  };
  estimatedCost: {
    materials: number;
    labor: number;
    total: number;
  };
}

export interface CalculationProgress {
  stage: string;
  progress: number;
  message: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface CalculationOptions {
  includeKlimps: boolean;
  optimizePlywood: boolean;
  generateNXExpressions: boolean;
  validateASTM: boolean;
  detailedLogging: boolean;
}

// Utility types for API responses
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  warnings?: string[];
  executionTime?: number;
}

export interface ExpressionFile {
  filename: string;
  content: string;
  timestamp: string;
  parameters: CrateInputs;
}

// Constants and enums
export const PANEL_THICKNESS_OPTIONS = [0.25, 0.5, 0.75] as const;
export const CLEAT_THICKNESS_OPTIONS = [0.75, 1.5, 2.0] as const;
export const CLEAT_WIDTH_OPTIONS = [1.5, 2.5, 3.5] as const;

export type PanelThickness = typeof PANEL_THICKNESS_OPTIONS[number];
export type CleatThickness = typeof CLEAT_THICKNESS_OPTIONS[number];
export type CleatWidth = typeof CLEAT_WIDTH_OPTIONS[number];

// Validation constraints
export const VALIDATION_LIMITS = {
  productLength: { min: 12, max: 130 },
  productWidth: { min: 12, max: 130 },
  productHeight: { min: 6, max: 120 },
  productWeight: { min: 50, max: 10000 },
  clearanceAllSides: { min: 0.5, max: 6 },
  clearanceTop: { min: 0.5, max: 6 },
} as const;