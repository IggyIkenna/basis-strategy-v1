# 🚀 Frontend (Minimal Tabs UI)

This frontend serves as a minimal, reliable shell that exposes two working tools as tabs:

-   **Backtest tab**: Embeds `public/test-backtest.html`, which provides a full-featured interface for creating backtests, viewing merged configurations, and building YAML overrides.
-   **Charts tab**: Embeds `public/charts-test.html`, allowing users to view and export charts and event logs for completed backtests.

Both pages communicate directly with the backend API and are designed to be simple, static, and robust.

## 🧭 How to Run

```bash
cd frontend
npm install
npm run dev
# The UI will be available at http://localhost:5173
```
Ensure the backend API is running and that its CORS policy allows requests from `http://localhost:5173`.

## 📁 Project Structure

The project has been intentionally simplified to the following core files:

```
frontend/
├── public/
│   ├── test-backtest.html  # The UI for running backtests
│   └── charts-test.html    # The UI for viewing results
├── src/
│   ├── App.tsx             # A minimal 2-tab React shell to host the iframes
│   ├── main.tsx            # Application entry point
│   └── index.css           # Minimal global styles
├── index.html              # Vite entry point
└── package.json            # Scripts and minimal dependencies
```

All other files and directories related to a larger React SPA (components, hooks, services, pages) have been removed to eliminate dead code and focus on the current functional UI.

## 🛠️ How to Build for Production

```bash
npm run build
npm run preview
```
This command builds the static assets and serves them, replicating the production environment.
