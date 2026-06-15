import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';

// Pages
import LoginPage from './pages/Auth/LoginPage';
import RegisterPage from './pages/Auth/RegisterPage';
import LandingPage from './pages/Landing/LandingPage';
import DashboardPage from './pages/Dashboard/DashboardPage';
import GroupsPage from './pages/Groups/GroupsPage';
import GroupDetailPage from './pages/Groups/GroupDetailPage';
import ExpenseCreatePage from './pages/Expenses/ExpenseCreatePage';
import BalanceExplorerPage from './pages/Balances/BalanceExplorerPage';
import SettlementPage from './pages/Settlements/SettlementPage';
import ImportCenterPage from './pages/Import/ImportCenterPage';
import AnomalyReviewPage from './pages/Import/AnomalyReviewPage';
import AuditHistoryPage from './pages/Audit/AuditHistoryPage';
import AppLayout from './components/Layout/AppLayout';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes */}
          <Route
            element={
              <RequireAuth>
                <AppLayout />
              </RequireAuth>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/groups" element={<GroupsPage />} />
            <Route path="/groups/:groupId" element={<GroupDetailPage />} />
            <Route path="/groups/:groupId/expenses/new" element={<ExpenseCreatePage />} />
            <Route path="/groups/:groupId/balances" element={<BalanceExplorerPage />} />
            <Route path="/groups/:groupId/settle" element={<SettlementPage />} />
            <Route path="/import" element={<ImportCenterPage />} />
            <Route path="/import/:jobId/review" element={<AnomalyReviewPage />} />
            <Route path="/audit" element={<AuditHistoryPage />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}


export default App;
