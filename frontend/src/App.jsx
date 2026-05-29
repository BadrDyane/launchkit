// launchkit/frontend/src/App.jsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext.jsx'
import { OrgProvider } from './context/OrgContext.jsx'

import Login from './pages/auth/Login.jsx'
import Signup from './pages/auth/Signup.jsx'
import ForgotPassword from './pages/auth/ForgotPassword.jsx'
import Dashboard from './pages/dashboard/Dashboard.jsx'
import Summarize from './pages/ai/Summarize.jsx'
import Billing from './pages/settings/Billing.jsx'
import Members from './pages/settings/Members.jsx'
import Profile from './pages/settings/Profile.jsx'
import AdminDashboard from './pages/admin/AdminDashboard.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <OrgProvider>
          <style>{`
            @keyframes spin { to { transform: rotate(360deg); } }
            * { box-sizing: border-box; }
            select option { background: #1A1A24; }
          `}</style>
          <Routes>
            {/* Auth */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />

            {/* App */}
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/ai" element={<Summarize />} />
            <Route path="/settings/billing" element={<Billing />} />
            <Route path="/settings/members" element={<Members />} />
            <Route path="/settings/profile" element={<Profile />} />

            {/* Admin */}
            <Route path="/admin" element={<AdminDashboard />} />

            {/* Default */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </OrgProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}