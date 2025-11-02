import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { LanguageProvider } from './contexts/LanguageContext';
import NewLayout from './components/layout/NewLayout';
import NewDashboard from './pages/NewDashboard';
import NewDownload from './pages/NewDownload';
import NewTraining from './pages/NewTraining';
import NewAnalysis from './pages/NewAnalysis';
import NewBacktest from './pages/NewBacktest';
import NewAdvancedChart from './pages/NewAdvancedChart';
import NewPortfolio from './pages/NewPortfolio';
import NewPDFLearning from './pages/NewPDFLearning';

function App() {
  return (
    <LanguageProvider>
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
            <Route path="/pdf-learning" element={<NewPDFLearning />} />
          </Routes>
        </NewLayout>
      </Router>
    </LanguageProvider>
  );
}

export default App;
