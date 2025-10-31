import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Dashboard from './pages/Dashboard';
import Download from './pages/Download';
import Training from './pages/Training';
import Analysis from './pages/Analysis';
import Backtest from './pages/Backtest';
import Portfolio from './pages/Portfolio';
import AdvancedChart from './pages/AdvancedChart';
import Layout from './components/layout/Layout';

const lightTheme = createTheme({
  palette: {
    mode: 'light',  // LIGHT mode - siyah yazı
    primary: {
      main: '#00BFA6',
    },
    secondary: {
      main: '#FF6B6B',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={lightTheme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/download" element={<Download />} />
            <Route path="/training" element={<Training />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/backtest" element={<Backtest />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/advanced-chart" element={<AdvancedChart />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
