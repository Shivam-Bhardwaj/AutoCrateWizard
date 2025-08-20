# AutoCrate Web

**AI-Enhanced Automated Crate Design System - Web Edition**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-org/autocrate-web)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)](https://typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-38bdf8.svg)](https://tailwindcss.com)

A modern web application version of AutoCrate, providing the same powerful crate design capabilities through a responsive web interface. Built with Next.js, TypeScript, and Tailwind CSS for optimal performance and user experience.

## 🚀 Features

- **Real-time Calculations**: Instant crate design with ASTM-compliant engineering
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Klimp System**: Full 30-klimp L-bracket positioning with 6DOF control
- **Material Optimization**: Intelligent plywood layout algorithms minimize waste
- **NX Integration**: Direct export of .exp files for Siemens NX import
- **Cost Estimation**: Real-time material and labor cost calculations
- **Modern UI**: Clean, professional interface with smooth animations

## 🛠 Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS with custom engineering theme
- **Icons**: Lucide React for consistent iconography
- **Animations**: Framer Motion for smooth transitions
- **Forms**: React Hook Form with Zod validation
- **Deployment**: Optimized for Vercel Edge Functions

## 🏗 Architecture

```
AutoCrate-Web/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # Root layout with metadata
│   ├── page.tsx             # Main application page
│   ├── globals.css          # Global styles and animations
│   └── api/                 # API routes
│       ├── calculate/       # Main calculation endpoint
│       └── download-expressions/  # File download endpoint
├── components/              # React components
│   ├── CrateForm.tsx       # Input form with validation
│   ├── ResultsDisplay.tsx  # Results visualization
│   └── LoadingSpinner.tsx  # Loading states
├── lib/                    # Core business logic
│   └── calculations/       # Calculation engines
│       ├── crateEngine.ts  # Main orchestration
│       ├── skidLogic.ts    # Skid calculations
│       ├── plywoodLayout.ts # Material optimization
│       └── klimpSystem.ts  # L-bracket positioning
├── types/                  # TypeScript definitions
│   └── index.ts           # All type definitions
└── vercel.json            # Vercel deployment config
```

## 🚀 Quick Start

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/your-org/autocrate-web.git
cd autocrate-web

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev

# 4. Open browser
open http://localhost:3000
```

### Vercel Deployment

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-org/autocrate-web)

Or manually:

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy to Vercel
vercel

# 3. Production deployment
vercel --prod
```

## 📊 Core Capabilities

### Engineering Calculations
- **ASTM Compliant**: All structural calculations follow industry standards
- **Load Analysis**: Automatic skid sizing based on product weight
- **Material Optimization**: Intelligent plywood layout reduces waste by 15-25%
- **Dimensional Stability**: Iterative calculations ensure manufacturable designs

### Klimp System
- **30 L-Brackets**: KL_1-10 (top), KL_11-20 (left), KL_21-30 (right)
- **6DOF Orientation**: Quaternion-based orientation with direction vectors
- **Smart Placement**: Automatic positioning avoiding cleat interference
- **NX Variables**: Complete set of parametric variables for CAD integration

### Web-Specific Features
- **Instant Feedback**: Real-time validation and calculation
- **Progressive Enhancement**: Works without JavaScript for basic functionality
- **Responsive Design**: Optimized for all screen sizes
- **Offline Capability**: Service worker for offline calculations (future)

## 🔧 API Endpoints

### POST /api/calculate
Calculate complete crate design from input specifications.

**Request:**
```json
{
  "productLength": 48,
  "productWidth": 36,
  "productHeight": 24,
  "productWeight": 150,
  "clearanceAllSides": 2.0,
  "clearanceTop": 2.0,
  "panelThickness": 0.25,
  "cleatThickness": 0.75,
  "cleatMemberWidth": 3.5
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overallLength": 52.5,
    "overallWidth": 40.5,
    "overallHeight": 29.75,
    "klimpResults": [...],
    "materialSummary": {...},
    "nxExpressions": [...]
  },
  "executionTime": 245
}
```

### POST /api/download-expressions
Generate and download NX expressions file.

**Request:**
```json
{
  "expressions": ["[Inch]KL_1_X = -21.250", ...]
}
```

**Response:** Binary .exp file download

## 🎨 Customization

### Styling
The application uses a custom Tailwind theme optimized for engineering applications:

```css
/* Custom colors for engineering applications */
.text-autocrate-600 { color: #0284c7; }
.bg-engineering-50 { background-color: #f8fafc; }

/* Engineering-specific components */
.engineering-input { @apply font-mono text-right; }
.metric-card { @apply bg-white rounded-xl shadow-sm; }
```

### Configuration
Modify environment variables in `.env.local`:

```bash
NEXT_PUBLIC_ENABLE_KLIMP_SYSTEM=true
NEXT_PUBLIC_ENABLE_MATERIAL_OPTIMIZATION=true
NEXT_PUBLIC_MAX_CALCULATION_TIME=10000
```

## 🧪 Testing

```bash
# Run type checking
npm run type-check

# Run linting
npm run lint

# Build for production
npm run build

# Test production build locally
npm run start
```

## 📚 Documentation

- **API Reference**: Complete endpoint documentation
- **Type Definitions**: Full TypeScript interfaces in `/types`
- **Calculation Logic**: Detailed algorithm documentation
- **Deployment Guide**: Step-by-step Vercel setup

## 🔒 Security

- **Input Validation**: Comprehensive Zod schema validation
- **Type Safety**: Full TypeScript coverage prevents runtime errors
- **CORS Configuration**: Secure cross-origin resource sharing
- **Environment Variables**: Secure configuration management

## 📈 Performance

- **Edge Functions**: Vercel Edge Runtime for global low-latency
- **Static Generation**: Pre-built pages for instant loading
- **Code Splitting**: Automatic bundle optimization
- **Image Optimization**: Next.js automatic image optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Desktop Version**: Based on AutoCrate v12.1.4 desktop application
- **AI Development**: Enhanced through AI-assisted development techniques
- **ASTM Standards**: Engineering calculations based on industry standards
- **Open Source**: Built with modern open-source technologies

## 📞 Support

For support and questions:

1. **GitHub Issues**: [Report bugs or request features](https://github.com/your-org/autocrate-web/issues)
2. **Documentation**: [Complete API docs](https://autocrate-web.vercel.app/docs)
3. **Desktop Version**: [AutoCrate Desktop](https://github.com/your-org/autocrate)

---

**AutoCrate Web v12.1.4** - Bringing professional crate design to the web with modern technologies and AI enhancement.

*Built with Next.js, powered by algorithms, enhanced by AI.*