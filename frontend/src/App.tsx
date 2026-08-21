import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AIProvider } from './context/AIContext';
import { Shell } from './components/Layout/Shell';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Hoje } from './pages/Hoje';
import { ModoProva } from './pages/ModoProva';
import { Cronograma } from './pages/Cronograma';
import { DiagnosticoIA } from './pages/DiagnosticoIA';
import { Estatisticas } from './pages/Estatisticas';
import { Gerenciador } from './pages/Gerenciador';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-principal)',
        color: 'var(--cor-secundaria)'
      }}>
        Carregando AprovaTeck...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isAdmin, loading } = useAuth();

  if (loading) {
    return null;
  }

  if (!user || !isAdmin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

import { ThemeProvider } from '@cidqueiroz/cdkteck-ui';

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AIProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Shell />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="hoje" element={<Hoje />} />
              <Route path="modo-prova" element={<ModoProva />} />
              <Route path="cronograma" element={<Cronograma />} />
              <Route path="diagnostico-ia" element={<DiagnosticoIA />} />
              <Route path="estatisticas" element={<Estatisticas />} />
              <Route
                path="gerenciador"
                element={
                  <AdminRoute>
                    <Gerenciador />
                  </AdminRoute>
                }
              />
            </Route>

          </Routes>
        </BrowserRouter>
      </AIProvider>
    </AuthProvider>
  </ThemeProvider>
  );
};

export default App;
