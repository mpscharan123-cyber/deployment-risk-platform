# Frontend Technical Report: Deployment Risk Platform

## 1. Architecture Overview
The frontend is built as a Single Page Application (SPA) utilizing **React 18** and **Vite** for rapid bundling and hot module replacement (HMR). The application interfaces directly with the FastAPI backend via REST endpoints to display real-time machine learning predictions regarding deployment risks.

- **Entry Point**: `src/main.jsx`
- **Core Logic & Routing**: `src/App.jsx`
- **Global Styling**: `src/index.css`

---

## 2. Component Structure
To reduce fragmentation in this lightweight application, the entire component tree is housed within `App.jsx`, split logically into reusable parts:

### 2.1 Layout Components
- **`App` (Main Container)**: Handles the top-level React Router (`BrowserRouter`), orchestrates the JWT authentication state (`isAuthenticated`), and defines the main `<Routes>` map.
- **`Sidebar`**: The primary navigation menu. It displays the currently logged-in user (extracting initials for the avatar) and utilizes `lucide-react` icons for clear visual routing mapping.

### 2.2 Core Views / Pages
- **`Login`**: The gateway component. It securely captures the username/password and hits the `/api/auth/token` endpoint. On success, it stashes the Bearer token in `localStorage` and triggers a top-level state update.
- **`Dashboard`**: The "Global Overview" command center. 
  - **State**: Fetches `/api/analytics` and `/api/deployments`.
  - **UI**: Displays four primary `stat-box` components (Total Releases, Approval Rate, Avg Risk Score, and Pending Reviews). It incorporates a `Recharts` PieChart for risk distribution and lists the 5 most recent deployments.
- **`Analysis`**: A robust form-driven view that allows manual ad-hoc commit analysis.
  - **Flow**: Takes a GitHub Owner, Repo, and Commit SHA -> Fetches raw git deltas -> Submits the deltas to the ML Engine (`/api/predict-risk`) -> Renders the resulting SHAP reasoning and risk gauge.
- **`Reports`**: A simple, tabular data-grid view fetching the historical ledger of all ML risk scores (`/api/risk-history`).
- **`Approval`**: The actionable queue for Release Managers. It filters all deployments down to those requiring manual intervention (`status === 'pending_review'`).

---

## 3. State Management & Data Fetching
- **Local State**: The app relies strictly on React Hooks (`useState`, `useEffect`). No complex global state managers (like Redux or Zustand) are required due to the relatively shallow component tree.
- **Authentication**: JWT tokens are managed in `localStorage`. The `App` component runs an effect on mount to silently re-hydrate the user session if a valid token exists.
- **Data Fetching**: Native `fetch` API is used across the board. Every secured API call dynamically attaches the `Authorization: Bearer <token>` header.

---

## 4. UI/UX and Styling Engine
The styling is completely bespoke and managed via **Vanilla CSS** (`index.css`), avoiding heavy CSS frameworks like Bootstrap while delivering a highly modern, "DevOps-aesthetic".

### 4.1 Design System Tokens
- **Backgrounds**: Deep slate (`#0f172a`) with a futuristic, subtle double radial-gradient to give the UI depth.
- **Glassmorphism**: The `.glass-card` class applies `backdrop-filter: blur(12px)` over a semi-transparent panel background, creating a premium floating effect.
- **Status Indicators**:
  - `Low Risk`: `#10b981` (Green)
  - `Medium Risk`: `#f59e0b` (Amber)
  - `High Risk`: `#ef4444` (Crimson)

### 4.2 Animations & Responsiveness
- **Micro-interactions**: Hovering over sidebar links or action buttons yields a subtle background shift or vertical translation.
- **Mount Animations**: Every page component employs the `.animate-slide` keyframe, ensuring smooth, fluid transitions as users click through the dashboard.
- **CSS Grid**: Core layouts utilize `.grid-cols-4`, `.grid-cols-3`, and `.grid-cols-2`. A global `@media` query cleanly collapses these multi-column displays into single-column vertical stacks on screens smaller than 1024px.

---

## 5. Dependencies
- **`react-router-dom`**: For client-side routing.
- **`lucide-react`**: For lightweight, sharp SVG iconography.
- **`recharts`**: For data visualization (Pie charts, stat displays).
