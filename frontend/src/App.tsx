import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NewLayout from './components/layout/NewLayout';
import NewDashboard from './pages/NewDashboard';
import NewDownload from './pages/NewDownload';
import NewTraining from './pages/NewTraining';
import NewAnalysis from './pages/NewAnalysis';
import NewBacktest from './pages/NewBacktest';
import NewAdvancedChart from './pages/NewAdvancedChart';
import NewPortfolio from './pages/NewPortfolio';

function App() {
  return (
    <Router>
      <NewLayout>
        <Routes>
          <Route path="/" element={<NewDashboard />} />
          <Route path="/download" element={<NewDownload />} />
          <Route path="/training" element={<NewTraining />} />
          <Route path="/analysis" element={<NewAnalysis />} />
          <Route path="/backtest" element={<NewBacktest />} />
          <Route path="/advanced-chart" element={<NewAdvancedChart />} />
          <Route path="/portfolio" element={<NewPortfolio />} />
        </Routes>
      </NewLayout>
    </Router>
  );
}

export default App;
