import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { ScanResults } from './pages/ScanResults';
import { History } from './pages/History';
import { Settings } from './pages/Settings';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="results" element={<ScanResults />} />
        <Route path="history" element={<History />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={
          <div className="flex flex-col items-center justify-center h-[50vh] text-center">
            <h1 className="text-4xl font-bold mb-4 text-[var(--primary)]">404</h1>
            <p className="text-xl">Page non trouvée</p>
          </div>
        } />
      </Route>
    </Routes>
  );
}

export default App;
