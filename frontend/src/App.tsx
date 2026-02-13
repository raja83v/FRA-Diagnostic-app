import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import TransformersPage from './pages/TransformersPage';
import TransformerDetail from './pages/TransformerDetail';
import ImportPage from './pages/ImportPage';
import AnalysisPage from './pages/AnalysisPage';
import RecommendationsPage from './pages/RecommendationsPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/transformers" element={<TransformersPage />} />
          <Route path="/transformers/:id" element={<TransformerDetail />} />
          <Route path="/import" element={<ImportPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
