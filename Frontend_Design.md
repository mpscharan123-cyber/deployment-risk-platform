# Frontend UI Design: AI-Based Deployment Risk Prediction Platform

## 1. Design System & Theme

- **Theme**: Dark Mode Default (DevOps-style aesthetic). Backgrounds use deep slate (`#0f172a`), with neon accents for status indicators.
- **Typography**: `Inter` or `Roboto Mono` for metrics and code blocks, `Outfit` for modern headers.
- **Color Palette**:
  - **Success / Low Risk**: Neon Green (`#10b981`)
  - **Warning / Medium Risk**: Amber (`#f59e0b`)
  - **Danger / High Risk**: Crimson Red (`#ef4444`)
  - **Primary Action**: Bright Indigo (`#6366f1`)
- **Technology Stack**: React.js (Vite), Tailwind CSS (for rapid utility styling), Recharts/Chart.js (for dynamic risk graphs and timelines).

---

## 2. Component Structure

The frontend leverages a component-based architecture for maximum reusability.

```text
src/
├── components/
│   ├── layout/
│   │   ├── Sidebar.jsx           # Global navigation
│   │   ├── Topbar.jsx            # User profile, notifications, breadcrumbs
│   │   └── LayoutWrapper.jsx     # Main container handling responsive margins
│   ├── shared/
│   │   ├── RiskBadge.jsx         # Reusable pill (Low/Med/High) with colored glow
│   │   ├── StatCard.jsx          # KPI display (e.g., "Total Deployments")
│   │   ├── CodeDiffViewer.jsx    # Visualizes lines added/deleted
│   │   └── Modal.jsx             # Popups for manual overrides
│   └── charts/
│       ├── RiskTrendChart.jsx    # Line chart showing risk scores over time
│       ├── OutagePieChart.jsx    # Pie chart of historical outage severity
│       └── TimelineGraph.jsx     # CI/CD steps progression
├── pages/
│   ├── Login.jsx                 # JWT Authentication gateway
│   ├── Dashboard.jsx             # Overview of all active deployments
│   ├── DeploymentAnalysis.jsx    # Detailed view of a single commit
│   ├── RiskPrediction.jsx        # ML reasoning and SHAP value graphs
│   ├── ApprovalRecommendation.jsx# Actionable view for Release Managers
│   └── Analytics.jsx             # System-wide reporting (MTTR, Success Rates)
├── context/
│   └── AuthContext.jsx           # Manages JWT and RBAC state
└── services/
    └── api.js                    # Axios instance to communicate with FastAPI backend
```

---

## 3. Navigation Flow

1. **Unauthenticated User** -> `Login Page`.
2. **Authenticated Dev/Admin** -> Redirected to `Dashboard` (Home).
3. **From Dashboard** -> User clicks on a specific active deployment in the table -> Routes to `Deployment Analysis Page` (`/deployments/:id`).
4. **Within Deployment View**:
   - Tab 1: **Code Analysis** -> View lines modified, files touched.
   - Tab 2: **Risk Prediction** -> View ML Score, SHAP breakdown, and Anomaly status.
   - Tab 3: **Approval Matrix** -> Final recommendation, override buttons.
5. **Sidebar Navigation**:
   - `[Home]` -> Dashboard
   - `[Deployments]` -> Paginated list of all historical deployments
   - `[Analytics]` -> System-wide charts and KPIs
   - `[Settings]` (Admin only) -> Rules Engine threshold configuration

---

## 4. UI Wireframe Descriptions

### 4.1 Login Page
- **Layout**: Centered glassmorphism card over a dark, subtly animated gradient background.
- **Elements**: 
  - Platform Logo (Shield or Brain icon).
  - Username & Password inputs with floating labels.
  - "Sign In" button with loading spinner state.
  - "Forgot Password" link.

### 4.2 Dashboard (The Command Center)
- **Layout**: Sidebar on the left, Topbar on top, scrollable main content area.
- **Top Row (Stat Cards)**: 
  - Deployments Today (Number + Trend arrow).
  - Average Risk Score (Gauge chart).
  - Pending Approvals (Highlighted in amber if > 0).
- **Middle Row (Charts)**:
  - Line chart showing deployment volume vs. risk scores over the last 7 days.
- **Bottom Row (Data Table)**:
  - "Recent Deployments" table. Columns: `Commit Hash`, `Author`, `Time`, `Risk Level` (RiskBadge), `Status`, `Action` (View Button).

### 4.3 Deployment Analysis Page
- **Layout**: Split pane.
- **Left Pane (Context)**: 
  - Commit details, author avatar, repository name.
  - `CodeDiffViewer` showing file tree and `+ additions` / `- deletions`.
- **Right Pane (CI/CD Timeline)**: 
  - Vertical stepper component mapping pipeline stages (e.g., Build -> Unit Tests -> ML Risk Analysis -> Approval Gate).
  - Green checkmarks for passed steps, spinning loaders for active steps.

### 4.4 Risk Prediction Page (Tab/Section)
- **Layout**: Focuses entirely on Explainable AI (XAI).
- **Hero Section**: Large circular gauge showing the Risk Score (0-100). If score > 80, the gauge pulses red.
- **Reasoning Section**: 
  - A horizontal bar chart (Chart.js) representing SHAP values. 
  - Red bars pushing the score higher (e.g., "1500 lines modified", "Previous outage history: 2").
  - Green bars pushing the score lower (e.g., "Senior Developer", "95% Test Coverage").
- **Anomaly Banner**: If the Isolation Forest flags it, a prominent warning banner appears: "⚠️ Out-of-Distribution Deployment Pattern Detected".

### 4.5 Approval Recommendation Page
- **Layout**: Action-oriented form.
- **System Recommendation Box**: Displays text like "Senior Staff Approval Required".
- **Action Buttons**: 
  - `[✅ Approve & Merge]` (Green)
  - `[❌ Reject & Block]` (Red)
  - `[💬 Request Code Review]` (Gray)
- **Justification Input**: A required text area for managers to type *why* they are overriding a high-risk system recommendation before the "Approve" button unlocks.

### 4.6 Analytics Page
- **Layout**: Grid of reporting widgets.
- **Visuals**:
  - Risk Distribution (Pie Chart: 70% Low, 20% Med, 10% High).
  - Developer Risk Index (Table ranking teams by average risk score, anonymized if necessary).
  - Outage Correlation (Scatter plot showing Risk Score vs. Actual post-deployment downtime).
