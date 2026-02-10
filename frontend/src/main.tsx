import React from 'react';
import ReactDOM from 'react-dom/client';
import '@fontsource/inter/400.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/800.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/500.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { SolverPage } from './pages/Solver';
import { PapersPage } from './pages/Papers';
import { HistoryPage } from './pages/History';
import { SettingsPage } from './pages/Settings';
import { SelfEvolutionPage } from './pages/SelfEvolution';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<SolverPage />} />
          <Route path="/papers" element={<PapersPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/evolution" element={<SelfEvolutionPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </React.StrictMode>,
);
