import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../config/supabase';
import { montarPlanoDiario } from '../services/schedulerService';
import { 
  CalendarCheck, 
  FileText, 
  BrainCircuit, 
  BarChart3, 
  Calendar, 
  FolderKanban, 
  ArrowRight, 
  Sparkles,
  Zap,
  TrendingUp,
  Target
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalRespondidas: 0,
    taxaAcerto: 0,
    materiasAtivas: 0,
    itensParaHoje: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const { data: { user: currentUser } } = await supabase.auth.getUser();
        const activeUserId = currentUser?.id || user?.id;

        if (!activeUserId) {
          setLoading(false);
          return;
        }

        // 1. Respostas do usuário
        let totalResp = 0;
        let totalAcertos = 0;

        const { data: respData, error: respError } = await supabase
          .from('respostas')
          .select('id, acertou')
          .eq('user_id', activeUserId);

        if (!respError && respData && respData.length > 0) {
          totalResp = respData.length;
          totalAcertos = respData.filter((r: any) => r.acertou).length;
        }

        const taxa = totalResp > 0 ? (totalAcertos / totalResp) * 100 : 0;        
        
        // 2. Matérias do Usuário & Itens de Estudo
        let materiasCount = 0;

        const { data: userAprendizado, error: aprError } = await supabase
          .from('aprendizado_item')
          .select('id, itens_estudo(subgrupos(grupos(nome)))')
          .eq('user_id', activeUserId);

        if (!aprError && userAprendizado && userAprendizado.length > 0) {
          const gruposSet = new Set<string>();
          userAprendizado.forEach((it: any) => {
            const gNome = it.itens_estudo?.subgrupos?.grupos?.nome;
            if (gNome && !['FORA DO EDITAL', 'NÃO CLASSIFICADO', 'NAO CLASSIFICADO'].includes(gNome.toUpperCase())) {
              gruposSet.add(gNome);
            }
          });
          materiasCount = gruposSet.size;
        }

        // 3. Itens para Hoje (AMV 2.0: Novos + Revisões do dia)
        const { novos, revisoes } = await montarPlanoDiario(activeUserId);
        const itensHoje = (novos?.length || 0) + (revisoes?.length || 0);

        setStats({
          totalRespondidas: totalResp,
          taxaAcerto: Math.round(taxa),
          materiasAtivas: materiasCount,
          itensParaHoje: itensHoje
        });
      } catch (err) {
        console.error('Erro ao carregar resumo do dashboard:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchOverview();
  }, [user]);

  const modules = [
    {
      id: 'hoje',
      title: 'Hoje (POD)',
      subtitle: 'Plano de Operações Diárias',
      description: 'Apreensão de novos conteúdos e revisões AMV 2.0 agendadas por repetição espaçada.',
      icon: CalendarCheck,
      color: '#06f0a8',
      path: '/hoje',
      badge: stats.itensParaHoje > 0 ? `${stats.itensParaHoje} pendentes` : 'Em dia'
    },
    {
      id: 'modo-prova',
      title: 'Modo Prova',
      subtitle: 'Simulador de Questões',
      description: 'Treine com cronômetro, simulados adaptativos por banca e tire dúvidas com o Tutor IA.',
      icon: FileText,
      color: '#FF8C00',
      path: '/modo-prova',
      badge: 'Treino Prático'
    },
    {
      id: 'diagnostico-ia',
      title: 'Diagnóstico IA',
      subtitle: 'Conselho do Tutor',
      description: 'Análise aprofundada dos seus pontos cegos com plano de ação cirúrgico gerado por IA.',
      icon: BrainCircuit,
      color: '#ec4899',
      path: '/diagnostico-ia',
      badge: 'Inteligência'
    },
    {
      id: 'estatisticas',
      title: 'Radar do Edital',
      subtitle: 'Learning Analytics',
      description: 'Métricas de evolução, taxa de acerto por matéria e análise da curva de esquecimento.',
      icon: BarChart3,
      color: '#3b82f6',
      path: '/estatisticas',
      badge: `${stats.taxaAcerto}% acertos`
    },
    {
      id: 'cronograma',
      title: 'Cronograma',
      subtitle: 'Matérias do Perfil',
      description: 'Selecione e gerencie as matérias do edital que o algoritmo AMV deve orquestrar.',
      icon: Calendar,
      color: '#a855f7',
      path: '/cronograma',
      badge: `${stats.materiasAtivas} matérias`
    },
    ...(isAdmin ? [{
      id: 'gerenciador',
      title: 'Gerenciador',
      subtitle: 'Admin de Questões',
      description: 'Área de administração para busca, validação, edição de enunciados e limpeza de tópicos.',
      icon: FolderKanban,
      color: '#f59e0b',
      path: '/gerenciador',
      badge: 'Administrador'
    }] : [])
  ];

  return (
    <div>
      {/* Banner de Boas-Vindas */}
      <div className="glass-card" style={{
        padding: '32px',
        marginBottom: '32px',
        position: 'relative',
        overflow: 'hidden',
        border: '1px solid rgba(6, 240, 168, 0.25)'
      }}>
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Sparkles size={20} color="var(--cor-secundaria)" />
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--cor-secundaria)', textTransform: 'uppercase' }}>
              Motor de Aprendizagem AMV 2.0
            </span>
          </div>
          <h1 style={{ fontSize: '1.9rem', marginBottom: '10px' }}>
            Bem-vindo à Central AprovaTeck, {user?.email?.split('@')[0]} 🎯
          </h1>
          <p style={{ color: 'var(--cor-texto-muted)', maxWidth: '650px', fontSize: '0.95rem' }}>
            Selecione um módulo abaixo para começar seus estudos orientados a dados e inteligência artificial.
          </p>
        </div>

        {/* Mini Cards de Métricas */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '16px',
          marginTop: '24px'
        }}>
          <div style={{
            padding: '14px 18px',
            borderRadius: '12px',
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid rgba(255, 255, 255, 0.05)'
          }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Questões Respondidas</span>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FF8C00' }}>{stats.totalRespondidas}</span>
          </div>

          <div style={{
            padding: '14px 18px',
            borderRadius: '12px',
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid rgba(255, 255, 255, 0.05)'
          }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Taxa de Acerto Geral</span>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--cor-secundaria)' }}>{stats.taxaAcerto}%</span>
          </div>

          <div style={{
            padding: '14px 18px',
            borderRadius: '12px',
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid rgba(255, 255, 255, 0.05)'
          }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Matérias no Perfil</span>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#3b82f6' }}>{stats.materiasAtivas}</span>
          </div>

          <div style={{
            padding: '14px 18px',
            borderRadius: '12px',
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid rgba(255, 255, 255, 0.05)'
          }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Itens para Hoje</span>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ec4899' }}>{stats.itensParaHoje}</span>
          </div>
        </div>
      </div>

      {/* Grid de Cards dos Módulos */}
      <h2 style={{ fontSize: '1.3rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <Target size={22} color="var(--cor-primaria)" /> Módulos de Estudo e Gestão
      </h2>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '24px'
      }}>
        {modules.map(mod => {
          const Icon = mod.icon;
          return (
            <div
              key={mod.id}
              onClick={() => navigate(mod.path)}
              className="glass-card"
              style={{
                padding: '28px',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                position: 'relative'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '12px',
                    background: `${mod.color}15`,
                    border: `1px solid ${mod.color}40`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: mod.color
                  }}>
                    <Icon size={24} />
                  </div>

                  <span style={{
                    padding: '4px 10px',
                    borderRadius: '20px',
                    background: `${mod.color}20`,
                    color: mod.color,
                    fontSize: '0.75rem',
                    fontWeight: 700
                  }}>
                    {mod.badge}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.2rem', marginBottom: '4px' }}>{mod.title}</h3>
                <span style={{ fontSize: '0.8rem', color: mod.color, fontWeight: 600, display: 'block', marginBottom: '12px' }}>
                  {mod.subtitle}
                </span>
                <p style={{ fontSize: '0.85rem', color: 'var(--cor-texto-muted)', lineHeight: 1.5 }}>
                  {mod.description}
                </p>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                color: mod.color,
                fontSize: '0.85rem',
                fontWeight: 700,
                marginTop: '20px'
              }}>
                <span>Acessar Módulo</span>
                <ArrowRight size={16} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
