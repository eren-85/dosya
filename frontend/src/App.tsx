import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import Backtest from './pages/Backtest';
import Portfolio from './pages/Portfolio';
import AdvancedChart from './pages/AdvancedChart';
import Layout from './components/layout/Layout';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00BFA6',
    },
    secondary: {
      main: '#FF6B6B',
    },
    background: {
      default: '#0A0E27',
      paper: '#151B3D',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
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
