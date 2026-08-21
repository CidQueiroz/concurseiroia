import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { AppShell } from '@cidqueiroz/cdkteck-ui';
import { useAuth } from '../../context/AuthContext';
import { useAI } from '../../context/AIContext';
import { supabase } from '../../config/supabase';
import { ApiKeyModal } from '../Common/ApiKeyModal';
import {
  LayoutDashboard,
  CalendarCheck,
  FileText,
  BrainCircuit,
  BarChart3,
  Calendar,
  FolderKanban,
  Key
} from 'lucide-react';

import packageJson from '../../../package.json';

export const Shell: React.FC = () => {
  const { user, isAdmin, signOut } = useAuth();
  const { preferredBanca, setPreferredBanca } = useAI();
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await signOut();
    navigate('/login');
  };

  const currentVersion = `v${packageJson.version} - Inteligência para Concursos`;
  const userPlanBadge = isAdmin ? 'Acesso Master (Admin)' : (user?.user_metadata?.plan || 'Nível Gratuito');

  const navItems = [
    { label: 'Visão Geral', path: '/', icon: <LayoutDashboard size={18} /> },
    { label: 'Hoje (POD)', path: '/hoje', icon: <CalendarCheck size={18} /> },
    { label: 'Modo Prova', path: '/modo-prova', icon: <FileText size={18} /> },
    { label: 'Diagnóstico IA', path: '/diagnostico-ia', icon: <BrainCircuit size={18} /> },
    { label: 'Radar do Edital', path: '/estatisticas', icon: <BarChart3 size={18} /> },
    { label: 'Cronograma', path: '/cronograma', icon: <Calendar size={18} /> },
    ...(isAdmin ? [{ label: 'Gerenciador', path: '/gerenciador', icon: <FolderKanban size={18} /> }] : [])
  ];

  const DEFAULT_BANCAS = ['FGV', 'CEBRASPE', 'CESGRANRIO', 'FCC', 'IBFC', 'VUNESP'];
  
  const [bancas, setBancas] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('aprovateck_bancas_list');
      if (saved) {
        const parsed = JSON.parse(saved);
        return Array.from(new Set([...DEFAULT_BANCAS, ...parsed])).filter(b => b && b !== 'Geral' && b !== 'IA' && b !== 'N/A');
      }
    } catch {}
    return DEFAULT_BANCAS;
  });

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isAddingBanca, setIsAddingBanca] = useState(false);
  const [newBancaName, setNewBancaName] = useState('');
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  // Fechar dropdown ao clicar fora
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
        setIsAddingBanca(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  // Carregar bancas únicas diretamente do Supabase (para todos os usuários verem o mesmo ecossistema)
  React.useEffect(() => {
    const fetchBancasSupabase = async () => {
      try {
        const { data: qData } = await supabase
          .from('questoes')
          .select('banca')
          .limit(1000);

        if (qData && qData.length > 0) {
          const distinct = qData
            .map((q: any) => q.banca?.trim().toUpperCase())
            .filter((b: any) => b && !['GERAL', 'N/A', 'IA', 'IA-GERADA'].includes(b));

          setBancas(prev => {
            const combinadas = Array.from(new Set([...DEFAULT_BANCAS, ...prev, ...distinct]));
            localStorage.setItem('aprovateck_bancas_list', JSON.stringify(combinadas));
            return combinadas;
          });
        }
      } catch (err) {
        console.error('Erro ao sincronizar bancas do Supabase:', err);
      }
    };

    fetchBancasSupabase();
  }, []);

  const handleSalvarNovaBanca = () => {
    const limpa = newBancaName.trim().toUpperCase();
    if (limpa && limpa !== 'GERAL') {
      if (!bancas.includes(limpa)) {
        const atualizadas = [...bancas, limpa];
        setBancas(atualizadas);
        localStorage.setItem('aprovateck_bancas_list', JSON.stringify(atualizadas));
      }
      setPreferredBanca(limpa);
    }
    setNewBancaName('');
    setIsAddingBanca(false);
    setIsDropdownOpen(false);
  };

  const handleLimparBancaSelecionada = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPreferredBanca('Geral');
  };

  return (
    <>
      <AppShell
        appName="AprovaTeck"
        appVersion={currentVersion}
        userEmail={user?.email || undefined}
        userBadge={userPlanBadge}
        navItems={navItems}
        activePath={location.pathname}
        onNavigate={(path: string) => navigate(path)}
        onLogout={handleLogout}
        headerCenterContent={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', position: 'relative' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--cor-texto-primario)', fontWeight: 600 }}>🎯 Banca:</span>

            {/* Custom Picklist Dropdown */}
            <div ref={dropdownRef} style={{ position: 'relative' }}>
              <button
                type="button"
                onClick={() => {
                  setIsDropdownOpen(prev => !prev);
                  setIsAddingBanca(false);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 14px',
                  borderRadius: '8px',
                  background: 'rgba(0, 0, 0, 0.4)',
                  border: '1px solid var(--cor-borda)',
                  color: preferredBanca === 'Geral' ? 'var(--cor-texto-primario)' : 'var(--cor-hover)',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  outline: 'none'
                }}
              >
                <span>{preferredBanca === 'Geral' ? 'Geral (Padrão)' : preferredBanca}</span>
                
                {/* Botão de limpar/remover seleção apenas se houver banca escolhida */}
                {preferredBanca !== 'Geral' && (
                  <span
                    title="Remover filtro e voltar para Geral"
                    onClick={handleLimparBancaSelecionada}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '18px',
                      height: '18px',
                      borderRadius: '50%',
                      background: 'rgba(239, 68, 68, 0.2)',
                      color: '#ef4444',
                      fontSize: '0.75rem',
                      fontWeight: 800,
                      marginLeft: '4px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(239, 68, 68, 0.4)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)')}
                  >
                    ✕
                  </span>
                )}
                <span style={{ fontSize: '0.7rem', opacity: 0.8 }}>▼</span>
              </button>

              {/* Menu Suspenso Customizado */}
              {isDropdownOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: 'calc(100% + 6px)',
                    left: 0,
                    minWidth: '220px',
                    background: '#0d1527',
                    border: '1px solid rgba(6, 240, 168, 0.3)',
                    borderRadius: '10px',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
                    zIndex: 1000,
                    padding: '6px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '2px'
                  }}
                >
                  {/* Lista de Bancas Existentes */}
                  {bancas.map((b) => {
                    const isSelected = preferredBanca === b;
                    return (
                      <div
                        key={b}
                        onClick={() => {
                          setPreferredBanca(b);
                          setIsDropdownOpen(false);
                        }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '8px 12px',
                          borderRadius: '6px',
                          background: isSelected ? 'rgba(6, 240, 168, 0.15)' : 'transparent',
                          color: isSelected ? 'var(--cor-secundaria)' : '#ffffff',
                          fontSize: '0.85rem',
                          fontWeight: isSelected ? 700 : 500,
                          cursor: 'pointer',
                          transition: 'all 0.15s ease'
                        }}
                      >
                        <span>{b}</span>
                        {isSelected && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--cor-secundaria)' }}>✓</span>
                            <span
                              title="Limpar seleção e voltar para Geral"
                              onClick={handleLimparBancaSelecionada}
                              style={{
                                color: '#ef4444',
                                fontSize: '0.8rem',
                                fontWeight: 800,
                                padding: '2px 6px',
                                borderRadius: '4px',
                                cursor: 'pointer'
                              }}
                            >
                              ✕
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {/* Opção Adicionar Nova Banca (Disponível para todos os usuários) */}
                  <div style={{ height: '1px', background: 'rgba(255,255,255,0.08)', margin: '4px 0' }} />
                  {isAddingBanca ? (
                    <div style={{ padding: '6px 4px', display: 'flex', gap: '4px' }}>
                      <input
                        type="text"
                        placeholder="Nome da Banca..."
                        value={newBancaName}
                        onChange={(e) => setNewBancaName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSalvarNovaBanca();
                          if (e.key === 'Escape') setIsAddingBanca(false);
                        }}
                        autoFocus
                        style={{
                          flex: 1,
                          padding: '6px 8px',
                          borderRadius: '6px',
                          background: 'rgba(0, 0, 0, 0.5)',
                          border: '1px solid var(--cor-secundaria)',
                          color: '#ffffff',
                          fontSize: '0.8rem',
                          outline: 'none'
                        }}
                      />
                      <button
                        type="button"
                        onClick={handleSalvarNovaBanca}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '6px',
                          background: 'var(--cor-secundaria)',
                          border: 'none',
                          color: '#000000',
                          fontWeight: 700,
                          fontSize: '0.75rem',
                          cursor: 'pointer'
                        }}
                      >
                        OK
                      </button>
                    </div>
                  ) : (
                    <div
                      onClick={() => setIsAddingBanca(true)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '6px',
                        color: 'var(--cor-primaria)',
                        fontSize: '0.85rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <span>➕ Adicionar Outra Banca...</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        }
        actions={[
          {
            label: 'Configurar IA',
            icon: <Key size={16} />,
            onClick: () => setIsKeyModalOpen(true),
            variant: 'secondary'
          }
        ]}
      >
        <Outlet />
      </AppShell>

      <ApiKeyModal isOpen={isKeyModalOpen} onClose={() => setIsKeyModalOpen(false)} />
    </>
  );
};

