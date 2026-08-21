import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useAI } from '../../context/AIContext';
import { ApiKeyModal } from '../Common/ApiKeyModal';
import { 
  LayoutDashboard, 
  CalendarCheck, 
  FileText, 
  BrainCircuit, 
  BarChart3, 
  Calendar, 
  FolderKanban, 
  LogOut, 
  Key, 
  Menu, 
  X,
  Target
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const { user, isAdmin, signOut } = useAuth();
  const { preferredBanca, setPreferredBanca } = useAI();
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await signOut();
    navigate('/login');
  };

  const navItems = [
    { label: 'Visão Geral', path: '/', icon: LayoutDashboard },
    { label: 'Hoje (POD)', path: '/hoje', icon: CalendarCheck },
    { label: 'Modo Prova', path: '/modo-prova', icon: FileText },
    { label: 'Diagnóstico IA', path: '/diagnostico-ia', icon: BrainCircuit },
    { label: 'Radar do Edital', path: '/estatisticas', icon: BarChart3 },
    { label: 'Cronograma', path: '/cronograma', icon: Calendar },
    ...(isAdmin ? [{ label: 'Gerenciador', path: '/gerenciador', icon: FolderKanban }] : [])
  ];

  const bancas = ['CEBRASPE', 'CESGRANRIO', 'FCC', 'FGV', 'IBFC', 'VUNESP', 'Geral'];

  return (
    <>
      <aside style={{
        width: '260px',
        height: '100vh',
        position: 'fixed',
        left: isOpen ? '0' : '-260px',
        top: 0,
        background: 'var(--bg-card)',
        backdropFilter: 'blur(16px)',
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 100,
        transition: 'left 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        padding: '20px 16px'
      }}>
        {/* Header do Sidebar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #FF8C00 0%, #06f0a8 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#000',
              fontWeight: 900
            }}>
              <Target size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.1rem', margin: 0, lineHeight: 1.1 }}>AprovaTeck</h2>
              <span style={{ fontSize: '0.7rem', color: 'var(--cor-secundaria)', fontWeight: 600 }}>AMV 2.0</span>
            </div>
          </div>
          <button 
            onClick={onToggle}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--cor-texto-muted)',
              cursor: 'pointer',
              display: 'block'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Informação do Usuário */}
        <div style={{
          padding: '10px 12px',
          borderRadius: '10px',
          background: 'rgba(0, 0, 0, 0.2)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          marginBottom: '16px'
        }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Conectado como:</span>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--cor-texto)' }}>
            {user?.email?.split('@')[0]}
          </span>
        </div>

        {/* Seletor de Banca */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--cor-texto-muted)', marginBottom: '6px' }}>
            🎯 Banca Preferida (IA)
          </label>
          <select
            value={preferredBanca}
            onChange={e => setPreferredBanca(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 10px',
              borderRadius: '8px',
              background: 'rgba(0, 0, 0, 0.3)',
              border: '1px solid var(--border-color)',
              color: 'var(--cor-texto)',
              fontSize: '0.8rem',
              outline: 'none'
            }}
          >
            {bancas.map(b => (
              <option key={b} value={b} style={{ background: '#0e1117' }}>{b}</option>
            ))}
          </select>
        </div>

        {/* Links de Navegação */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, overflowY: 'auto' }}>
          {navItems.map(item => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  color: isActive ? '#ffffff' : 'var(--cor-texto-muted)',
                  background: isActive ? 'linear-gradient(90deg, rgba(6, 240, 168, 0.15) 0%, transparent 100%)' : 'transparent',
                  borderLeft: isActive ? '3px solid var(--cor-secundaria)' : '3px solid transparent',
                  textDecoration: 'none',
                  fontSize: '0.85rem',
                  fontWeight: isActive ? 600 : 500,
                  transition: 'all 0.2s'
                })}
              >
                <Icon size={18} style={{ flexShrink: 0 }} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Rodapé do Sidebar */}
        <div style={{ paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button
            onClick={() => setIsKeyModalOpen(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 12px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: 'rgba(255, 140, 0, 0.1)',
              color: 'var(--cor-primaria)',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <Key size={16} /> Configurar Chaves IA
          </button>

          <button
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 12px',
              borderRadius: '8px',
              border: 'none',
              background: 'rgba(239, 68, 68, 0.1)',
              color: '#f87171',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <LogOut size={16} /> Sair da Conta
          </button>
        </div>
      </aside>

      <ApiKeyModal isOpen={isKeyModalOpen} onClose={() => setIsKeyModalOpen(false)} />
    </>
  );
};
