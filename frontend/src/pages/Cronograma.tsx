import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../config/supabase';
import { montarPlanoDiario, ItemEstudo } from '../services/schedulerService';
import { 
  Calendar, 
  CheckCircle2, 
  Plus, 
  Trash2, 
  RefreshCw, 
  Clock, 
  BookOpen, 
  CheckSquare, 
  Square,
  Sparkles,
  Database
} from 'lucide-react';

export const Cronograma: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const [todosGrupos, setTodosGrupos] = useState<string[]>([]);
  const [gruposUsuario, setGruposUsuario] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedGrupos, setSelectedGrupos] = useState<string[]>([]);

  // Agenda para Hoje
  const [agenda, setAgenda] = useState<{ horario: string; atividade: string; topico: string }[]>([]);
  const [loadingAgenda, setLoadingAgenda] = useState(false);

  // Admin Resumo de Questões no Banco
  const [adminResumoBanco, setAdminResumoBanco] = useState<{ grupo: string; total: number; validadas: number; naoValidadas: number }[]>([]);

  const carregarMateriasEAgenda = async () => {
    if (!user) return;
    setLoading(true);

    try {
      // 1. Grupos disponíveis
      const { data: gData } = await supabase.from('grupos').select('nome');
      const allG = gData ? gData.map((g: any) => g.nome).filter(Boolean) : [];
      setTodosGrupos(allG);

      // 2. Grupos atuais do usuário
      const { data: uData } = await supabase
        .from('aprendizado_item')
        .select('itens_estudo!inner(subgrupos!inner(grupos!inner(nome)))')
        .eq('user_id', user.id);

      const userGSet = new Set<string>();
      uData?.forEach((it: any) => {
        const nome = it.itens_estudo?.subgrupos?.grupos?.nome;
        if (nome) userGSet.add(nome);
      });

      const userGList = Array.from(userGSet);
      setGruposUsuario(userGList);
      setSelectedGrupos(userGList);

      // 3. Montar Agenda para Hoje
      setLoadingAgenda(true);
      const { novos, revisoes } = await montarPlanoDiario(user.id);
      
      const agendaList: { horario: string; atividade: string; topico: string }[] = [];
      let tStart = 8;

      novos.forEach(n => {
        agendaList.push({
          horario: `${String(tStart).padStart(2, '0')}:00`,
          atividade: 'Apreensão & Active Recall',
          topico: `${n.grupo_nome} ➔ ${n.item_nome}`
        });
        tStart++;
      });

      revisoes.forEach(r => {
        agendaList.push({
          horario: `${String(tStart).padStart(2, '0')}:00`,
          atividade: 'Revisão Espaçada (SRS)',
          topico: `${r.grupo_nome} ➔ ${r.item_nome}`
        });
        tStart++;
      });

      agendaList.push({
        horario: `${String(tStart).padStart(2, '0')}:00`,
        atividade: 'Modo Prova (Resistência)',
        topico: 'Simulado Misto Geral'
      });

      setAgenda(agendaList);
      setLoadingAgenda(false);

      // 4. Se Admin, buscar Resumo do Banco por Grupo
      if (isAdmin) {
        const { data: qData } = await supabase
          .from('questoes')
          .select('valida, itens_estudo!inner(subgrupos!inner(grupos(nome)))')
          .limit(1000);

        if (qData) {
          const resumoMap: { [key: string]: { grupo: string; total: number; validadas: number; naoValidadas: number } } = {};
          qData.forEach((q: any) => {
            const grp = q.itens_estudo?.subgrupos?.grupos?.nome || 'Geral';
            if (!resumoMap[grp]) {
              resumoMap[grp] = { grupo: grp, total: 0, validadas: 0, naoValidadas: 0 };
            }
            resumoMap[grp].total += 1;
            if (q.valida === 1) resumoMap[grp].validadas += 1;
            else resumoMap[grp].naoValidadas += 1;
          });
          setAdminResumoBanco(Object.values(resumoMap).sort((a, b) => b.total - a.total));
        }
      }
    } catch (err) {
      console.error('Erro ao carregar cronograma:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarMateriasEAgenda();
  }, [user, isAdmin]);

  const handleToggleGrupo = (grupo: string) => {
    if (selectedGrupos.includes(grupo)) {
      setSelectedGrupos(selectedGrupos.filter(g => g !== grupo));
    } else {
      setSelectedGrupos([...selectedGrupos, grupo]);
    }
  };

  const handleToggleAll = () => {
    if (selectedGrupos.length === todosGrupos.length) {
      // Se todos estiverem selecionados, remove todos
      setSelectedGrupos([]);
    } else {
      // Se pelo menos um não estiver selecionado, seleciona todos
      setSelectedGrupos([...todosGrupos]);
    }
  };

  const handleSalvar = async () => {
    if (!user) return;
    setSaving(true);

    try {
      const atuaisSet = new Set(gruposUsuario);
      const novosSet = new Set(selectedGrupos);

      const adicionar = selectedGrupos.filter(g => !atuaisSet.has(g));
      const remover = gruposUsuario.filter(g => !novosSet.has(g));

      // 1. Adicionar novos grupos
      if (adicionar.length > 0) {
        const { data: itensNovos } = await supabase
          .from('itens_estudo')
          .select('id, subgrupos!inner(grupos!inner(nome))')
          .in('subgrupos.grupos.nome', adicionar);

        if (itensNovos && itensNovos.length > 0) {
          const insertPayload = itensNovos.map((it: any) => ({
            user_id: user.id,
            item_id: it.id,
            status: 'NOVO'
          }));

          for (let i = 0; i < insertPayload.length; i += 50) {
            await supabase.from('aprendizado_item').insert(insertPayload.slice(i, i + 50));
          }
        }
      }

      // 2. Remover grupos desmarcados
      if (remover.length > 0) {
        const { data: itensRemover } = await supabase
          .from('itens_estudo')
          .select('id, subgrupos!inner(grupos!inner(nome))')
          .in('subgrupos.grupos.nome', remover);

        if (itensRemover && itensRemover.length > 0) {
          const idsRemover = itensRemover.map((i: any) => i.id);
          for (let i = 0; i < idsRemover.length; i += 100) {
            await supabase
              .from('aprendizado_item')
              .delete()
              .eq('user_id', user.id)
              .in('item_id', idsRemover.slice(i, i + 100));
          }
        }
      }

      await carregarMateriasEAgenda();
      alert('Matérias do seu perfil atualizadas com sucesso no Motor AMV 2.0!');
    } catch (err) {
      console.error('Erro ao salvar cronograma:', err);
      alert('Erro ao atualizar matérias.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px' }}>
        <RefreshCw className="animate-spin" size={32} color="var(--cor-secundaria)" />
        <p style={{ marginTop: '16px', color: 'var(--cor-texto-muted)' }}>Carregando Cronograma de Batalha (Motor AMV 2.0)...</p>
      </div>
    );
  }

  const allSelected = todosGrupos.length > 0 && selectedGrupos.length === todosGrupos.length;

  return (
    <div style={{ paddingBottom: '40px' }}>
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.6rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Calendar size={26} color="var(--cor-primaria)" /> Cronograma de Batalha 📅 (Motor AMV 2.0)
        </h1>
        <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.9rem' }}>
          Esqueça tabelas rígidas! A Inteligência Artificial monta o seu cronograma diário com base na sua <strong>curva de esquecimento</strong> (Spaced Repetition).
        </p>
      </div>

      {/* 1. SUA AGENDA PARA HOJE (POSICIONADO NO TOPO) */}
      <div className="glass-card" style={{ padding: '24px', marginBottom: '32px' }}>
        <h3 style={{ fontSize: '1.2rem', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Clock size={20} color="var(--cor-primaria)" /> Sua Agenda para Hoje ⏰
        </h3>
        <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.85rem', marginBottom: '18px' }}>
          Itens priorizados pelo algoritmo AMV 2.0 para estudo ativo e repetição espaçada hoje.
        </p>

        {agenda.length === 0 ? (
          <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.85rem' }}>Sua agenda para hoje está vazia. Vincule matérias ao seu perfil abaixo para começar!</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--cor-texto-muted)' }}>
                  <th style={{ textAlign: 'center', padding: '10px', width: '90px' }}>Horário</th>
                  <th style={{ textAlign: 'left', padding: '10px', width: '220px' }}>Atividade</th>
                  <th style={{ textAlign: 'left', padding: '10px' }}>Tópico / Matéria</th>
                </tr>
              </thead>
              <tbody>
                {agenda.map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ textAlign: 'center', padding: '12px 10px', fontWeight: 700, color: 'var(--cor-primaria)' }}>
                      {row.horario}
                    </td>
                    <td style={{ padding: '12px 10px' }}>
                      <span style={{
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        background: row.atividade.includes('Apreensão') 
                          ? 'rgba(6, 240, 168, 0.15)' 
                          : row.atividade.includes('Revisão') 
                          ? 'rgba(255, 107, 0, 0.15)' 
                          : 'rgba(59, 130, 246, 0.15)',
                        color: row.atividade.includes('Apreensão') 
                          ? 'var(--cor-secundaria)' 
                          : row.atividade.includes('Revisão') 
                          ? 'var(--cor-primaria)' 
                          : '#60a5fa'
                      }}>
                        {row.atividade}
                      </span>
                    </td>
                    <td style={{ padding: '12px 10px', fontWeight: 600 }}>{row.topico}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 2. SELEÇÃO DE MATÉRIAS DO PERFIL */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BookOpen size={20} color="var(--cor-secundaria)" /> Seleção de Matérias do Seu Perfil 📚
            </h3>
            <span style={{ fontSize: '0.85rem', color: selectedGrupos.length > 0 ? 'var(--cor-secundaria)' : '#ef4444', fontWeight: 600 }}>
              {selectedGrupos.length} de {todosGrupos.length} matérias selecionadas
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Botão Dinâmico: Remover Todas ou Selecionar Todas */}
            <button
              type="button"
              onClick={handleToggleAll}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: '8px',
                background: allSelected ? 'rgba(239, 68, 68, 0.15)' : 'rgba(6, 240, 168, 0.15)',
                border: allSelected ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(6, 240, 168, 0.4)',
                color: allSelected ? '#ef4444' : 'var(--cor-secundaria)',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              {allSelected ? (
                <>
                  <Trash2 size={16} /> Remover Todas
                </>
              ) : (
                <>
                  <CheckSquare size={16} /> Selecionar Todas
                </>
              )}
            </button>

            <button
              onClick={handleSalvar}
              disabled={saving}
              className="btn-sovereign btn-primary"
              style={{ fontSize: '0.85rem', padding: '8px 18px' }}
            >
              {saving ? 'Salvando no Banco...' : 'Atualizar Matérias do Perfil'}
            </button>
          </div>
        </div>

        {/* Grid de Seleção de Matérias */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: '12px'
        }}>
          {todosGrupos.map(g => {
            const isSelected = selectedGrupos.includes(g);
            return (
              <div
                key={g}
                onClick={() => handleToggleGrupo(g)}
                style={{
                  padding: '14px 18px',
                  borderRadius: '10px',
                  background: isSelected ? 'rgba(6, 240, 168, 0.12)' : 'rgba(0, 0, 0, 0.25)',
                  border: isSelected ? '1px solid var(--cor-secundaria)' : '1px solid rgba(255, 255, 255, 0.08)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.15s ease'
                }}
              >
                <span style={{ fontWeight: 600, fontSize: '0.85rem', color: isSelected ? '#ffffff' : 'var(--cor-texto-muted)' }}>
                  {g}
                </span>
                <div style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '6px',
                  border: isSelected ? 'none' : '2px solid rgba(255, 255, 255, 0.2)',
                  background: isSelected ? 'var(--cor-secundaria)' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#000'
                }}>
                  {isSelected && <CheckCircle2 size={15} />}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

