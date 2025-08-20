# AutoCrate Web Deployment Guide

## Quick Deploy to Vercel (Recommended)

### One-Click Deployment
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-org/autocrate-web)

### Manual Deployment

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   # Development deployment
   vercel
   
   # Production deployment
   vercel --prod
   ```

## Environment Setup

### Required Environment Variables
```bash
NEXT_PUBLIC_APP_NAME="AutoCrate Web"
NEXT_PUBLIC_APP_VERSION="12.1.4-web"
NEXT_PUBLIC_ENABLE_KLIMP_SYSTEM=true
```

### Optional Configuration
```bash
NEXT_PUBLIC_DEBUG_MODE=false
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_API_TIMEOUT=30000
```

## Build Configuration

### Local Build
```bash
# Install dependencies
npm install

# Type check
npm run type-check

# Build for production
npm run build

# Test production build
npm run start
```

### Vercel Build Settings
- **Framework Preset**: Next.js
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`
- **Development Command**: `npm run dev`

## Performance Optimization

### Vercel Edge Functions
- API routes automatically deployed as Edge Functions
- Global distribution for low latency
- Automatic scaling based on demand

### Next.js Optimizations
- **Static Generation**: Pre-built pages for instant loading
- **Code Splitting**: Automatic bundle optimization
- **Image Optimization**: Automatic WebP conversion and sizing
- **Font Optimization**: Automatic font loading optimization

## Domain Configuration

### Custom Domain
1. Add domain in Vercel dashboard
2. Configure DNS records:
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```
3. Enable HTTPS (automatic)

### Subdomain Setup
```
autocrate.yourdomain.com → Vercel app
```

## Monitoring & Analytics

### Built-in Vercel Analytics
- **Core Web Vitals**: Automatic performance monitoring
- **Function Metrics**: API endpoint performance tracking
- **Error Tracking**: Automatic error detection and alerts

### Custom Analytics (Optional)
```bash
# Enable in environment variables
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

## Security Configuration

### CORS Setup
Configured in `vercel.json`:
```json
{
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "*"
        }
      ]
    }
  ]
}
```

### Content Security Policy
```bash
# Add to environment if needed
NEXT_PUBLIC_CSP_ENABLED=true
```

## Troubleshooting

### Common Build Issues

**TypeScript Errors:**
```bash
npm run type-check
```

**Missing Dependencies:**
```bash
npm install --force
npm run build
```

**API Timeout Issues:**
```bash
# Increase timeout in vercel.json
"functions": {
  "app/api/**/*.ts": {
    "maxDuration": 30
  }
}
```

### Runtime Issues

**Calculation Errors:**
- Check input validation
- Verify calculation logic
- Monitor Vercel function logs

**Performance Issues:**
- Check Vercel Analytics
- Optimize calculation algorithms
- Enable Edge Function caching

## Maintenance

### Updates
```bash
# Update dependencies
npm update

# Security audit
npm audit fix

# Deploy updates
vercel --prod
```

### Monitoring
- Monitor Vercel dashboard for performance
- Check function execution times
- Review error rates and user feedback

## Support

- **GitHub Issues**: [Report problems](https://github.com/your-org/autocrate-web/issues)
- **Vercel Docs**: [Deployment help](https://vercel.com/docs)
- **Next.js Docs**: [Framework documentation](https://nextjs.org/docs)

---

**AutoCrate Web** - Professional crate design automation accessible from any device, anywhere in the world.