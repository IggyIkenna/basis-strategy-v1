# Frontend Build Guide for Cursor Background Agents

## Overview
The frontend packages have been removed from git tracking to reduce repository size. This guide explains how background agents can build the frontend on demand.

## Quick Setup for Background Agents

### Automatic Setup (Recommended)
```bash
# Run the setup script from project root
./scripts/setup_frontend_for_agents.sh
```

### Manual Setup
```bash
# 1. Install Node.js (if not installed)
brew install node

# 2. Navigate to frontend directory
cd frontend

# 3. Install dependencies
npm install

# 4. Build the frontend
npm run build
```

## Available Commands

### Development
```bash
cd frontend
npm run dev          # Start development server
npm run preview      # Preview production build
```

### Production
```bash
cd frontend
npm run build        # Build for production
```

### Testing & Quality
```bash
cd frontend
npm run lint         # Run ESLint
npm run test         # Run tests
npm run test:ui      # Run tests with UI
```

## Dependencies

### Key Dependencies
- **React 19.1.1** - UI framework
- **Vite 5.3.1** - Build tool and dev server
- **TypeScript 5.2.2** - Type safety
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **TanStack Query** - Data fetching
- **Recharts** - Data visualization

### Development Dependencies
- **ESLint** - Code linting
- **Vitest** - Testing framework
- **Testing Library** - React testing utilities

## File Structure
```
frontend/
├── src/
│   ├── components/     # React components
│   ├── contexts/       # React contexts
│   ├── services/       # API services
│   ├── types/          # TypeScript types
│   └── utils/          # Utility functions
├── public/             # Static assets
├── package.json        # Dependencies and scripts
├── vite.config.ts      # Vite configuration
├── tsconfig.json       # TypeScript configuration
└── tailwind.config.js  # Tailwind CSS configuration
```

## Background Agent Integration

### Prerequisites Check
Background agents should verify:
1. Node.js is installed (`node --version`)
2. npm is available (`npm --version`)
3. Frontend directory exists

### Build Process
1. Run `./scripts/setup_frontend_for_agents.sh` for automatic setup
2. Or manually run `cd frontend && npm install && npm run build`
3. Verify build success by checking `frontend/dist/` directory

### Error Handling
- If Node.js is missing, install via Homebrew: `brew install node`
- If npm install fails, clear cache: `npm cache clean --force`
- If build fails, check for TypeScript errors: `npm run lint`

## Performance Notes
- Initial `npm install` may take 2-3 minutes
- Subsequent builds are much faster (30-60 seconds)
- Dependencies are cached in `node_modules/` (excluded from git)
- Build output goes to `frontend/dist/` (excluded from git)

## Troubleshooting

### Common Issues
1. **Node.js not found**: Install via Homebrew
2. **Permission errors**: Run `chmod +x scripts/setup_frontend_for_agents.sh`
3. **Build failures**: Check TypeScript errors with `npm run lint`
4. **Missing dependencies**: Run `npm install` in frontend directory

### Verification
```bash
# Check if everything is working
cd frontend
npm run build
ls -la dist/  # Should show built files
```

## Repository Size Impact
- **Before**: 939MB (including 355MB node_modules)
- **After**: ~584MB (node_modules excluded)
- **Savings**: 355MB reduction for background agents
