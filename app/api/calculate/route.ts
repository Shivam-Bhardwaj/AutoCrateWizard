import { NextRequest, NextResponse } from 'next/server';
import { calculateCrateDesign, validateInputs } from '@/lib/calculations/crateEngine';
import { CrateInputs, ApiResponse, CrateResults } from '@/types';

export async function POST(request: NextRequest) {
  const startTime = Date.now();
  
  try {
    // Parse request body
    const inputs: CrateInputs = await request.json();
    
    // Validate inputs
    const validation = validateInputs(inputs);
    if (!validation.valid) {
      return NextResponse.json({
        success: false,
        error: `Invalid inputs: ${validation.errors.join(', ')}`,
        executionTime: Date.now() - startTime
      } as ApiResponse<never>);
    }
    
    // Perform calculations
    const results = calculateCrateDesign(inputs);
    
    // Return successful response
    return NextResponse.json({
      success: true,
      data: results,
      executionTime: Date.now() - startTime
    } as ApiResponse<CrateResults>);
    
  } catch (error) {
    console.error('Calculation error:', error);
    
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown calculation error',
      executionTime: Date.now() - startTime
    } as ApiResponse<never>, {
      status: 500
    });
  }
}

// Handle OPTIONS for CORS
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}