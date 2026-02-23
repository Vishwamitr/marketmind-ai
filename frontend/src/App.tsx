import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import AnalysisPage from './pages/AnalysisPage';
import BacktestPage from './pages/BacktestPage';
import PortfolioPage from './pages/PortfolioPage';
import ModelMonitorPage from './pages/ModelMonitorPage';
import NewsPage from './pages/NewsPage';
import AdminPage from './pages/AdminPage';
import WatchlistPage from './pages/WatchlistPage';
import RecommendationsPage from './pages/RecommendationsPage';
import MutualFundsPage from './pages/MutualFundsPage';
import OptionsPage from './pages/OptionsPage';
import ScreenerPage from './pages/ScreenerPage';
import AlertsPage from './pages/AlertsPage';
import HeatmapPage from './pages/HeatmapPage';
import ComparePage from './pages/ComparePage';
import PositionCalcPage from './pages/PositionCalcPage';

function App() {
  return (
    <Router>
      <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--gradient-bg)' }}>
        <Sidebar />
        <main className="page-container">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analysis/:symbol" element={<AnalysisPage />} />
            <Route path="/backtest" element={<BacktestPage />} />
            <Route path="/portfolio" element={<PortfolioPage />} />
            <Route path="/monitor" element={<ModelMonitorPage />} />
            <Route path="/news" element={<NewsPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/watchlist" element={<WatchlistPage />} />
            <Route path="/recommendations" element={<RecommendationsPage />} />
            <Route path="/mutual-funds" element={<MutualFundsPage />} />
            <Route path="/options" element={<OptionsPage />} />
            <Route path="/screener" element={<ScreenerPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/heatmap" element={<HeatmapPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/position-calc" element={<PositionCalcPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

