// Klimp System Logic - Ported from Python klimp_quaternion_integration.py
// Calculates L-bracket positions and orientations for structural reinforcement

import { KlimpResult } from '@/types';

interface Quaternion {
  w: number;
  x: number;
  y: number;
  z: number;
}

interface Vector3 {
  x: number;
  y: number;
  z: number;
}

interface KlimpPlacement {
  positionX: number;
  positionY: number;
  positionZ?: number;
  rotation: number;
}

interface KlimpPanelGroup {
  topKlimps: KlimpPlacement[];
  leftKlimps: KlimpPlacement[];
  rightKlimps: KlimpPlacement[];
}

// Constants for klimp placement
const MIN_SPACING_FROM_CLEAT = 0.25;
const MIN_KLIMP_SPACING = 16.0;
const MAX_KLIMP_SPACING = 24.0;
const TARGET_KLIMP_SPACING = 20.0;
const KLIMP_WIDTH = 1.0;

/**
 * Calculate all klimp placements for a crate design
 */
export function calculateAllKlimpPlacements(
  panelWidth: number,
  panelLength: number,
  panelHeight: number,
  cleatMemberWidth: number = 3.5,
  cleatThickness: number = 2.0,
  panelThickness: number = 0.25,
  intermediateVerticalCleats: number[] = [],
  horizontalSplicePositions: number[] = []
): KlimpPanelGroup {
  
  // Calculate klimps for each panel
  const topKlimps = calculateTopKlimps(
    panelWidth,
    cleatMemberWidth,
    intermediateVerticalCleats
  );
  
  const leftKlimps = calculateSideKlimps(
    panelLength,
    panelHeight,
    cleatMemberWidth,
    horizontalSplicePositions,
    'left'
  );
  
  const rightKlimps = calculateSideKlimps(
    panelLength,
    panelHeight,
    cleatMemberWidth,
    horizontalSplicePositions,
    'right'
  );
  
  return {
    topKlimps: topKlimps.slice(0, 10), // Limit to 10 klimps per panel
    leftKlimps: leftKlimps.slice(0, 10),
    rightKlimps: rightKlimps.slice(0, 10)
  };
}

/**
 * Calculate klimp positions for top panel
 */
function calculateTopKlimps(
  panelWidth: number,
  cleatMemberWidth: number,
  intermediateVerticalCleats: number[]
): KlimpPlacement[] {
  
  const klimps: KlimpPlacement[] = [];
  const cleatHalfWidth = cleatMemberWidth / 2.0;
  
  // Define cleat centerlines
  const leftCleatCenterline = cleatHalfWidth;
  const rightCleatCenterline = panelWidth - cleatHalfWidth;
  
  // Add intermediate cleat centerlines
  const allCleatCenterlines = [
    leftCleatCenterline,
    ...intermediateVerticalCleats,
    rightCleatCenterline
  ].sort((a, b) => a - b);
  
  // Calculate klimp positions between cleats
  for (let i = 0; i < allCleatCenterlines.length - 1; i++) {
    const leftEdge = allCleatCenterlines[i] + cleatHalfWidth + MIN_SPACING_FROM_CLEAT;
    const rightEdge = allCleatCenterlines[i + 1] - cleatHalfWidth - MIN_SPACING_FROM_CLEAT;
    const availableWidth = rightEdge - leftEdge;
    
    if (availableWidth > KLIMP_WIDTH) {
      // Calculate number of klimps needed for this span
      const spanLength = rightEdge - leftEdge;
      const klimpsNeeded = Math.max(1, Math.ceil(spanLength / TARGET_KLIMP_SPACING));
      
      // Position klimps evenly in the available space
      if (klimpsNeeded === 1) {
        klimps.push({
          positionX: (leftEdge + rightEdge) / 2,
          positionY: 0,
          rotation: 0
        });
      } else {
        const spacing = spanLength / (klimpsNeeded - 1);
        for (let j = 0; j < klimpsNeeded; j++) {
          klimps.push({
            positionX: leftEdge + (j * spacing),
            positionY: 0,
            rotation: 0
          });
        }
      }
    }
  }
  
  return klimps;
}

/**
 * Calculate klimp positions for side panels (left/right)
 */
function calculateSideKlimps(
  panelLength: number,
  panelHeight: number,
  cleatMemberWidth: number,
  horizontalSplicePositions: number[],
  side: 'left' | 'right'
): KlimpPlacement[] {
  
  const klimps: KlimpPlacement[] = [];
  const rotation = side === 'left' ? -90 : 90;
  
  // For side panels, we place klimps along the panel length (Y direction)
  // avoiding horizontal cleats
  
  const cleatHalfWidth = cleatMemberWidth / 2.0;
  const topCleatPosition = panelHeight - cleatHalfWidth;
  const bottomCleatPosition = cleatHalfWidth;
  
  // Create zones between horizontal elements
  const horizontalElements = [
    bottomCleatPosition,
    ...horizontalSplicePositions,
    topCleatPosition
  ].sort((a, b) => a - b);
  
  // Calculate klimp positions in each zone
  for (let i = 0; i < horizontalElements.length - 1; i++) {
    const bottomEdge = horizontalElements[i] + cleatHalfWidth + MIN_SPACING_FROM_CLEAT;
    const topEdge = horizontalElements[i + 1] - cleatHalfWidth - MIN_SPACING_FROM_CLEAT;
    const availableHeight = topEdge - bottomEdge;
    
    if (availableHeight > KLIMP_WIDTH) {
      // Place klimps along the panel length at this height
      const klimpsNeeded = Math.max(1, Math.ceil(panelLength / TARGET_KLIMP_SPACING));
      const spacing = panelLength / (klimpsNeeded + 1);
      
      for (let j = 0; j < klimpsNeeded; j++) {
        klimps.push({
          positionY: spacing * (j + 1),
          positionZ: (bottomEdge + topEdge) / 2,
          positionX: 0, // Will be set based on panel position
          rotation
        });
      }
    }
  }
  
  return klimps;
}

/**
 * Generate complete klimp orientations with quaternions and direction vectors
 */
export function calculateKlimpQuaternionOrientations(
  panelWidth: number,
  panelLength: number,
  panelHeight: number,
  cleatMemberWidth: number = 3.5,
  cleatThickness: number = 2.0,
  panelThickness: number = 0.25,
  crateeCenterX: number = 0,
  crateCenterY: number = 0,
  groundLevelZ: number = 0
): KlimpResult[] {
  
  const placements = calculateAllKlimpPlacements(
    panelWidth,
    panelLength,
    panelHeight,
    cleatMemberWidth,
    cleatThickness,
    panelThickness
  );
  
  const orientations: KlimpResult[] = [];
  
  // Calculate absolute positioning parameters
  const halfWidth = panelWidth / 2.0;
  const halfLength = panelLength / 2.0;
  const topZ = groundLevelZ + panelHeight + panelThickness + cleatThickness + cleatMemberWidth;
  const leftX = crateeCenterX - halfWidth - panelThickness - cleatThickness;
  const rightX = crateeCenterX + halfWidth + panelThickness + cleatThickness;
  
  // Process top klimps (KL_1 to KL_10)
  for (let i = 0; i < 10; i++) {
    if (i < placements.topKlimps.length) {
      const klimp = placements.topKlimps[i];
      const absX = crateeCenterX + klimp.positionX - halfWidth;
      const absY = crateCenterY + klimp.positionY;
      const absZ = topZ;
      
      orientations.push(createTopPanelKlimp(i + 1, absX, absY, absZ));
    } else {
      // Suppressed klimp
      orientations.push(createSuppressedKlimp(i + 1, 'top'));
    }
  }
  
  // Process left klimps (KL_11 to KL_20)
  for (let i = 0; i < 10; i++) {
    if (i < placements.leftKlimps.length) {
      const klimp = placements.leftKlimps[i];
      const absX = leftX;
      const absY = crateCenterY + klimp.positionY;
      const absZ = groundLevelZ + (klimp.positionZ || 0);
      
      orientations.push(createLeftPanelKlimp(i + 11, absX, absY, absZ));
    } else {
      orientations.push(createSuppressedKlimp(i + 11, 'left'));
    }
  }
  
  // Process right klimps (KL_21 to KL_30)
  for (let i = 0; i < 10; i++) {
    if (i < placements.rightKlimps.length) {
      const klimp = placements.rightKlimps[i];
      const absX = rightX;
      const absY = crateCenterY + klimp.positionY;
      const absZ = groundLevelZ + (klimp.positionZ || 0);
      
      orientations.push(createRightPanelKlimp(i + 21, absX, absY, absZ));
    } else {
      orientations.push(createSuppressedKlimp(i + 21, 'right'));
    }
  }
  
  return orientations;
}

/**
 * Create top panel klimp orientation (standard orientation)
 */
function createTopPanelKlimp(id: number, x: number, y: number, z: number): KlimpResult {
  return {
    id,
    panel: 'top',
    positionX: x,
    positionY: y,
    positionZ: z,
    quaternion: { w: 1.0, x: 0.0, y: 0.0, z: 0.0 }, // Identity quaternion
    directionVectors: {
      x: [1, 0, 0], // Width spans sideways
      y: [0, 1, 0], // Short side extends away
      z: [0, 0, -1] // Long side extends down into crate
    },
    eulerAngles: { rx: 0, ry: 0, rz: 0 },
    suppress: false
  };
}

/**
 * Create left panel klimp orientation (-90° rotation about Z)
 */
function createLeftPanelKlimp(id: number, x: number, y: number, z: number): KlimpResult {
  // -90° rotation about Z axis
  const angle = -Math.PI / 2;
  const qz = Math.sin(angle / 2);
  const qw = Math.cos(angle / 2);
  
  return {
    id,
    panel: 'left',
    positionX: x,
    positionY: y,
    positionZ: z,
    quaternion: { w: qw, x: 0.0, y: 0.0, z: qz },
    directionVectors: {
      x: [0, -1, 0], // Short side extends inward
      y: [1, 0, 0],  // Long side extends away
      z: [0, 0, 1]   // Width spans vertically
    },
    eulerAngles: { rx: 0, ry: 0, rz: -90 },
    suppress: false
  };
}

/**
 * Create right panel klimp orientation (+90° rotation about Z)
 */
function createRightPanelKlimp(id: number, x: number, y: number, z: number): KlimpResult {
  // +90° rotation about Z axis
  const angle = Math.PI / 2;
  const qz = Math.sin(angle / 2);
  const qw = Math.cos(angle / 2);
  
  return {
    id,
    panel: 'right',
    positionX: x,
    positionY: y,
    positionZ: z,
    quaternion: { w: qw, x: 0.0, y: 0.0, z: qz },
    directionVectors: {
      x: [0, 1, 0],  // Short side extends inward
      y: [-1, 0, 0], // Long side extends away
      z: [0, 0, 1]   // Width spans vertically
    },
    eulerAngles: { rx: 0, ry: 0, rz: 90 },
    suppress: false
  };
}

/**
 * Create suppressed (hidden) klimp
 */
function createSuppressedKlimp(id: number, panel: 'top' | 'left' | 'right'): KlimpResult {
  return {
    id,
    panel,
    positionX: 0,
    positionY: 0,
    positionZ: 0,
    quaternion: { w: 1.0, x: 0.0, y: 0.0, z: 0.0 },
    directionVectors: {
      x: [1, 0, 0],
      y: [0, 1, 0],
      z: [0, 0, 1]
    },
    eulerAngles: { rx: 0, ry: 0, rz: 0 },
    suppress: true
  };
}

/**
 * Generate NX expression strings for klimp system
 */
export function generateKlimpNXExpressions(klimps: KlimpResult[]): string[] {
  const expressions: string[] = [];
  
  klimps.forEach(klimp => {
    const id = klimp.id;
    
    // Position variables
    expressions.push(`[Inch]KL_${id}_X = ${klimp.positionX.toFixed(3)} // Position X coordinate`);
    expressions.push(`[Inch]KL_${id}_Y = ${klimp.positionY.toFixed(3)} // Position Y coordinate`);
    expressions.push(`[Inch]KL_${id}_Z = ${klimp.positionZ.toFixed(3)} // Position Z coordinate`);
    
    // Quaternion variables
    expressions.push(`KL_${id}_Q_W = ${klimp.quaternion.w.toFixed(6)} // Quaternion W (scalar) component`);
    expressions.push(`KL_${id}_Q_X = ${klimp.quaternion.x.toFixed(6)} // Quaternion X (i) component`);
    expressions.push(`KL_${id}_Q_Y = ${klimp.quaternion.y.toFixed(6)} // Quaternion Y (j) component`);
    expressions.push(`KL_${id}_Q_Z = ${klimp.quaternion.z.toFixed(6)} // Quaternion Z (k) component`);
    
    // Direction vectors
    expressions.push(`KL_${id}_X_DIR_X = ${klimp.directionVectors.x[0].toFixed(6)} // X-axis direction X component`);
    expressions.push(`KL_${id}_X_DIR_Y = ${klimp.directionVectors.x[1].toFixed(6)} // X-axis direction Y component`);
    expressions.push(`KL_${id}_X_DIR_Z = ${klimp.directionVectors.x[2].toFixed(6)} // X-axis direction Z component`);
    
    expressions.push(`KL_${id}_Y_DIR_X = ${klimp.directionVectors.y[0].toFixed(6)} // Y-axis direction X component`);
    expressions.push(`KL_${id}_Y_DIR_Y = ${klimp.directionVectors.y[1].toFixed(6)} // Y-axis direction Y component`);
    expressions.push(`KL_${id}_Y_DIR_Z = ${klimp.directionVectors.y[2].toFixed(6)} // Y-axis direction Z component`);
    
    expressions.push(`KL_${id}_Z_DIR_X = ${klimp.directionVectors.z[0].toFixed(6)} // Z-axis direction X component`);
    expressions.push(`KL_${id}_Z_DIR_Y = ${klimp.directionVectors.z[1].toFixed(6)} // Z-axis direction Y component`);
    expressions.push(`KL_${id}_Z_DIR_Z = ${klimp.directionVectors.z[2].toFixed(6)} // Z-axis direction Z component`);
    
    // Legacy Euler angles for compatibility
    expressions.push(`KL_${id}_RX = ${klimp.eulerAngles.rx.toFixed(3)} // Legacy Euler angle X rotation (degrees)`);
    expressions.push(`KL_${id}_RY = ${klimp.eulerAngles.ry.toFixed(3)} // Legacy Euler angle Y rotation (degrees)`);
    expressions.push(`KL_${id}_RZ = ${klimp.eulerAngles.rz.toFixed(3)} // Legacy Euler angle Z rotation (degrees)`);
    
    // Control flags
    expressions.push(`KL_${id}_SUPPRESS = ${klimp.suppress ? 1 : 0} // Suppress flag (0=hide, 1=show)`);
  });
  
  return expressions;
}