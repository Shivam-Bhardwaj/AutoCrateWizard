import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { expressions } = await request.json();
    
    if (!expressions || !Array.isArray(expressions)) {
      return NextResponse.json({
        success: false,
        error: 'Invalid expressions data'
      }, { status: 400 });
    }
    
    // Generate filename with timestamp
    const timestamp = new Date().toISOString()
      .replace(/[:.]/g, '-')
      .split('T')[0] + '_' + 
      new Date().toTimeString().slice(0, 8).replace(/:/g, '');
    
    const filename = `AutoCrate_Web_${timestamp}_ASTM.exp`;
    
    // Create file content
    const fileContent = [
      '// AutoCrate Web - NX Expressions File',
      `// Generated: ${new Date().toISOString()}`,
      '// AI-Enhanced Automated Crate Design System v12.1.4-web',
      '// ASTM Compliant Structural Calculations',
      '',
      ...expressions,
      '',
      '// End of AutoCrate Web Expressions',
      `// Total variables: ${expressions.length}`,
      '// Visit: https://autocrate-web.vercel.app for more designs'
    ].join('\n');
    
    // Return file as downloadable blob
    return new NextResponse(fileContent, {
      status: 200,
      headers: {
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Content-Length': fileContent.length.toString(),
      },
    });
    
  } catch (error) {
    console.error('Download error:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Failed to generate download file'
    }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}