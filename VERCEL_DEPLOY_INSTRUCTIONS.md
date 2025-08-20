# AutoCrate Web - Vercel Deployment Instructions

## 🚀 One-Click Deployment (Recommended)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-org/autocrate-web)

1. Click the "Deploy with Vercel" button above
2. Connect your GitHub account
3. Clone the repository to your GitHub
4. Vercel will automatically build and deploy
5. Your app will be live at `https://your-app-name.vercel.app`

## 📋 Manual Deployment Steps

### Step 1: Prepare Repository

```bash
# Navigate to the AutoCrate-Web directory
cd AutoCrate-Web

# Initialize git repository
git init

# Add all files
git add .

# Initial commit
git commit -m "feat: AutoCrate Web - Complete Next.js application with ASTM calculations"

# Add GitHub remote (replace with your repository)
git remote add origin https://github.com/your-username/autocrate-web.git

# Push to GitHub
git push -u origin main
```

### Step 2: Deploy to Vercel

#### Option A: Vercel Dashboard
1. Visit [vercel.com](https://vercel.com) and sign in
2. Click "Add New Project"
3. Import from GitHub
4. Select your `autocrate-web` repository
5. Click "Deploy"
6. Wait 2-3 minutes for build completion
7. Access your live app at the provided URL

#### Option B: Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy to development
vercel

# Deploy to production  
vercel --prod
```

### Step 3: Configure Custom Domain (Optional)

1. **In Vercel Dashboard:**
   - Go to your project settings
   - Click "Domains"
   - Add your custom domain
   - Follow DNS configuration instructions

2. **DNS Configuration:**
   ```
   Type: CNAME
   Name: autocrate (or www)
   Value: cname.vercel-dns.com
   TTL: Auto
   ```

3. **SSL Certificate:**
   - Automatically provisioned by Vercel
   - No additional configuration needed

## ⚙️ Environment Configuration

### Required Environment Variables
Set these in Vercel dashboard under Settings → Environment Variables:

```bash
NEXT_PUBLIC_APP_NAME="AutoCrate Web"
NEXT_PUBLIC_APP_VERSION="12.1.4-web"
NEXT_PUBLIC_ENABLE_KLIMP_SYSTEM=true
NEXT_PUBLIC_ENABLE_MATERIAL_OPTIMIZATION=true
NEXT_PUBLIC_ENABLE_COST_ESTIMATION=true
```

### Optional Variables
```bash
NEXT_PUBLIC_DEBUG_MODE=false
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_API_TIMEOUT=30000
NEXT_PUBLIC_MAX_CALCULATION_TIME=10000
```

## 🔧 Build Configuration

### Automatic Vercel Settings
Vercel automatically detects Next.js and configures:
- **Framework**: Next.js
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`
- **Node.js Version**: 18.x

### Custom Configuration
The included `vercel.json` configures:
- API function timeouts (30 seconds)
- CORS headers for API access
- Environment variables
- Performance optimizations

## 📊 Performance Expectations

### Build Time
- **Initial Build**: 2-3 minutes
- **Subsequent Builds**: 30-60 seconds (incremental)
- **Cold Start**: < 1 second (Edge Functions)

### Runtime Performance
- **Page Load**: < 2 seconds globally
- **Calculation Time**: < 5 seconds for typical crates
- **File Download**: < 1 second for .exp files
- **Global Latency**: < 100ms via Edge Network

## 🔍 Verification Steps

After deployment, verify these features work:

### ✅ Core Functionality
1. **Form Validation**: Enter invalid dimensions, check error messages
2. **Calculation**: Submit valid inputs, verify results appear
3. **Quick Tests**: Click quick test buttons, verify pre-filled values
4. **Results Display**: Check all tabs (Overview, Klimps, Materials, Expressions)

### ✅ File Operations
1. **Download .exp**: Click download button, verify file downloads
2. **File Content**: Open downloaded file, verify NX expressions format
3. **Filename**: Check timestamp and proper naming convention

### ✅ Responsive Design
1. **Desktop**: Test on large screens (1920x1080+)
2. **Tablet**: Test on iPad/tablet sizes (768x1024)
3. **Mobile**: Test on phone sizes (375x667)
4. **Orientation**: Test both portrait and landscape

### ✅ Performance
1. **Loading Speed**: Page should load in < 2 seconds
2. **Calculation Speed**: Results should appear in < 5 seconds
3. **Smooth Animations**: All transitions should be 60fps
4. **Memory Usage**: Monitor browser memory consumption

## 🐛 Troubleshooting

### Common Deployment Issues

**Build Failures:**
```bash
# Check TypeScript errors
npm run type-check

# Check dependencies
npm install --force

# Check build locally
npm run build
```

**API Errors:**
- Verify all calculation files are included
- Check import paths use relative imports
- Ensure all types are properly exported

**Performance Issues:**
- Check Vercel function logs
- Monitor build output size
- Verify Edge Function optimization

### Support Resources
- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Next.js Docs**: [nextjs.org/docs](https://nextjs.org/docs)
- **GitHub Issues**: Report problems in repository

## 🎉 Success Indicators

Your deployment is successful when:

✅ **Vercel Build Completes**: No errors in build logs
✅ **Application Loads**: Homepage appears with AutoCrate branding
✅ **Form Works**: Can enter dimensions and submit
✅ **Calculations Work**: Results appear after form submission
✅ **Download Works**: Can download .exp files
✅ **Mobile Responsive**: Works on phone browsers
✅ **Performance Good**: < 2 second page loads globally

## 📞 Post-Deployment

### Monitoring
- Check Vercel Analytics for performance metrics
- Monitor function execution times
- Review error rates and user feedback

### Updates
```bash
# Deploy updates
git add .
git commit -m "Update: Description of changes"
git push origin main
# Vercel automatically redeploys
```

### Scaling
- Vercel automatically handles traffic scaling
- No additional configuration needed for growth
- Monitor usage in Vercel dashboard

---

**AutoCrate Web is ready for global deployment!**

*From development to production in under 5 minutes with Vercel's powerful platform.*