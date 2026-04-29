import { useDashboardStore } from './store/dashboard';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { StacksPage } from './pages/StacksPage';
import { VulnerabilitiesPage } from './pages/VulnerabilitiesPage';
import { ChainsPage } from './pages/ChainsPage';
import { CompliancePage } from './pages/CompliancePage';
import { SimulationsPage } from './pages/SimulationsPage';
import { HumanRiskPage } from './pages/HumanRiskPage';
import { SandboxPage } from './pages/SandboxPage';

function App() {
  const { currentPage } = useDashboardStore();

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardPage />;
      case 'stacks':
        return <StacksPage />;
      case 'vulnerabilities':
        return <VulnerabilitiesPage />;
      case 'chains':
        return <ChainsPage />;
      case 'compliance':
        return <CompliancePage />;
      case 'simulations':
        return <SimulationsPage />;
      case 'human-risk':
        return <HumanRiskPage />;
      case 'sandbox':
        return <SandboxPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden text-slate-100">
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(77,214,194,0.18),_transparent_32%),radial-gradient(circle_at_top_right,_rgba(227,140,43,0.18),_transparent_28%),linear-gradient(180deg,_rgba(4,8,22,1)_0%,_rgba(7,17,31,1)_48%,_rgba(3,8,16,1)_100%)]" />
      <div className="fixed left-1/2 top-0 h-80 w-80 -translate-x-1/2 rounded-full bg-aurora-500/10 blur-3xl" />

      <Sidebar />
      <Header />
      
      <div className="relative z-10">
        {renderPage()}
      </div>
    </main>
  );
}

export default App;
