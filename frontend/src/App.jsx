import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ToastProvider } from './components/Toast';
import Layout from './components/Layout';
import NewProposal from './pages/NewProposal';
import Proposals from './pages/Proposals';
import PricingConfig from './pages/PricingConfig';
import Chat from './pages/Chat';
import Settings from './pages/Settings';

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<NewProposal />} />
            <Route path="/proposals" element={<Proposals />} />
            <Route path="/pricing-config" element={<PricingConfig />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ToastProvider>
  );
}

export default App;
