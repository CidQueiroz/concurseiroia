import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../config/supabase';
import { 
  BarChart3, 
  TrendingUp, 
  CheckCircle2, 
  Clock, 
  Award, 
  RefreshCw, 
  Database, 
  Brain, 
  Layers,
  Search,
  CheckCircle,
  HelpCircle,
  Trash2,
  BookOpen,
  PieChart as PieIcon
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell,
  LineChart,
  Line,
  CartesianGrid,
  Legend,
  ReferenceLine
} from 'recharts';

export const Estatisticas: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const [loading, setLoading] = useState(true);

  // 1. Dados Admin (Banco de Questões Global com contagens exatas)
  const [adminBancoStats, setAdminBancoStats] = useState({
    validadas: 0,
    aguardando: 0,
    removidas: 0,
    distribuicao: [] as { grupo: string; subgrupo: string; qtd: number }[]
  });

  // 2. Métricas Gerais do Usuário
  const [statsGerais, setStatsGerais] = useState({
    totalRespondidas: 0,
    acertos: 0,
    erros: 0,
    taxa: 0
  });

  // 3. Desempenho por Matéria / Disciplina
  const [statsMaterias, setStatsMaterias] = useState<any[]>([]);

  // 4. Evolução Temporal (Dia a Dia e Acumulado formatado dd/mm)
  const [evolucaoTemporal, setEvolucaoTemporal] = useState<any[]>([]);

  // 5. Motor de Aprendizagem AMV 2.0
  const [amvMetrics, setAmvMetrics] = useState({
    dominados: 0,
    emAprendizagem: 0,
    reconhecimento: 0,
    lista: [] as any[]
  });

  // 6. Raio-X por Tópico (Subgrupo ➔ Item)
  const [raioXTopicos, setRaioXTopicos] = useState<any[]>([]);
  const [filtroRaioX, setFiltroRaioX] = useState('');

  useEffect(() => {
    if (!user) return;

    const fetchAllData = async () => {
      setLoading(true);
      try {
        // --- A. ADMIN: CONTAGEM EXATA DO BANCO (HEAD QUERIES IDÊNTICAS AO STREAMLIT) ---
        if (isAdmin) {
          try {
            const [valRes, aguardRes, remRes, allQRes] = await Promise.all([
              supabase.from('questoes').select('id', { count: 'exact', head: true }).eq('valida', 1),
              supabase.from('questoes').select('id', { count: 'exact', head: true }).eq('valida', 0),
              supabase.from('questoes').select('id', { count: 'exact', head: true }).eq('valida', -1),
              supabase.from('questoes').select('id, itens_estudo(nome, subgrupos(nome, grupos(nome)))').limit(1000)
            ]);

            const valCount = valRes.count || 0;
            const aguardCount = aguardRes.count || 0;
            const remCount = remRes.count || 0;

            const distMap: { [key: string]: number } = {};
            if (allQRes.data) {
              allQRes.data.forEach((q: any) => {
                const g = q.itens_estudo?.subgrupos?.grupos?.nome || 'Geral';
                const s = q.itens_estudo?.subgrupos?.nome || 'Geral';
                const k = `${g} | ${s}`;
                distMap[k] = (distMap[k] || 0) + 1;
              });
            }

            const distList = Object.entries(distMap).map(([k, qtd]) => {
              const [grupo, subgrupo] = k.split(' | ');
              return { grupo, subgrupo, qtd };
            }).sort((a, b) => b.qtd - a.qtd);

            setAdminBancoStats({
              validadas: valCount,
              aguardando: aguardCount,
              removidas: remCount,
              distribuicao: distList
            });
          } catch (errAdmin) {
            console.error('Erro ao buscar estatísticas de Admin do banco:', errAdmin);
          }
        }

        // --- B. RESPOSTAS DO USUÁRIO ---
        const { data: resp } = await supabase
          .from('respostas')
          .select('id, questao_id, acertou, tempo_segundos, data, questoes(itens_estudo(nome, subgrupos(nome, grupos(nome))))')
          .eq('user_id', user.id)
          .order('data', { ascending: true });

        if (resp && resp.length > 0) {
          const validResp: any[] = [];
          resp.forEach((r: any) => {
            const gNome = r.questoes?.itens_estudo?.subgrupos?.grupos?.nome;
            const sNome = r.questoes?.itens_estudo?.subgrupos?.nome;
            const iNome = r.questoes?.itens_estudo?.nome;

            if (gNome && !['FORA DO EDITAL', 'NÃO CLASSIFICADO', 'NAO CLASSIFICADO'].includes(gNome.toUpperCase())) {
              // Formatação de data segura YYYY-MM-DD
              const dataStr = r.data ? r.data.split('T')[0] : 'Hoje';
              validResp.push({
                ...r,
                grupo_nome: gNome,
                subgrupo_nome: sNome || 'Geral',
                item_nome: iNome || 'Geral',
                data_dia: dataStr
              });
            }
          });

          const total = validResp.length;
          const acertos = validResp.filter((r: any) => r.acertou).length;
          const erros = total - acertos;
          const taxa = total > 0 ? Math.round((acertos / total) * 100) : 0;
          setStatsGerais({ totalRespondidas: total, acertos, erros, taxa });

          // Desempenho por Matéria
          const porMat: { [key: string]: { materia: string; acertos: number; total: number } } = {};
          validResp.forEach((r: any) => {
            const m = r.grupo_nome;
            if (!porMat[m]) porMat[m] = { materia: m, acertos: 0, total: 0 };
            porMat[m].total += 1;
            if (r.acertou) porMat[m].acertos += 1;
          });

          const matList = Object.values(porMat).map(d => ({
            ...d,
            erros: d.total - d.acertos,
            taxa: Math.round((d.acertos / d.total) * 100)
          })).sort((a, b) => b.total - a.total);
          setStatsMaterias(matList);

          // Evolução Temporal (Formato Brasileiro DD/MM)
          const diasMap: { [key: string]: { data: string; total: number; acertos: number } } = {};
          validResp.forEach((r: any) => {
            const d = r.data_dia;
            if (!diasMap[d]) diasMap[d] = { data: d, total: 0, acertos: 0 };
            diasMap[d].total += 1;
            if (r.acertou) diasMap[d].acertos += 1;
          });

          let acumTotal = 0;
          let acumAcertos = 0;
          const evolucaoList = Object.values(diasMap).map(d => {
            acumTotal += d.total;
            acumAcertos += d.acertos;
            const taxaDia = Math.round((d.acertos / d.total) * 100);
            const taxaAcum = Math.round((acumAcertos / acumTotal) * 100);

            // Converter '2026-07-04' para '04/07'
            let dataFormatada = d.data;
            if (d.data.includes('-')) {
              const parts = d.data.split('-');
              if (parts.length === 3) {
                dataFormatada = `${parts[2]}/${parts[1]}`;
              }
            }

            return {
              data: dataFormatada,
              taxaDia,
              taxaAcum,
              totalDia: d.total
            };
          });
          setEvolucaoTemporal(evolucaoList);

          // Raio-X por Tópico (Subgrupo ➔ Item)
          const topicosMap: { [key: string]: { topico: string; grupo: string; subgrupo: string; item: string; total: number; acertos: number } } = {};
          validResp.forEach((r: any) => {
            const k = `${r.subgrupo_nome} ➔ ${r.item_nome}`;
            if (!topicosMap[k]) topicosMap[k] = { topico: k, grupo: r.grupo_nome, subgrupo: r.subgrupo_nome, item: r.item_nome, total: 0, acertos: 0 };
            topicosMap[k].total += 1;
            if (r.acertou) topicosMap[k].acertos += 1;
          });

          const raioXList = Object.values(topicosMap).map(t => ({
            ...t,
            taxa: Math.round((t.acertos / t.total) * 100)
          })).sort((a, b) => b.total - a.total);
          setRaioXTopicos(raioXList);
        }

        // --- C. MOTOR DE DOMÍNIO AMV 2.0 ---
        const { data: amv } = await supabase
          .from('aprendizado_item')
          .select('*, itens_estudo(nome, subgrupos(nome, grupos(nome)))')
          .eq('user_id', user.id);

        if (amv && amv.length > 0) {
          const validAmv = amv.filter((a: any) => a.status !== 'NOVO');
          let dom = 0;
          let emApr = 0;
          let rec = 0;

          const amvItems = validAmv.map((a: any) => {
            if (a.status === 'DOMINADO') dom++;
            else if (['RETENCAO_INICIAL', 'REVISAO_1', 'REVISAO_2', 'REVISAO_3'].includes(a.status)) emApr++;
            else if (a.status === 'RECONHECIMENTO') rec++;

            const getClasse = (acc: number) => {
              if (acc >= 95) return 'Dominado';
              if (acc >= 80) return 'Especialista';
              if (acc >= 60) return 'Avançado';
              if (acc >= 40) return 'Intermediário';
              if (acc >= 20) return 'Aprendiz';
              return 'Iniciante';
            };

            const domPerc = a.nivel_dominio || 0;

            return {
              id: a.id,
              topico: a.itens_estudo?.nome || 'Geral',
              materia: a.itens_estudo?.subgrupos?.grupos?.nome || 'Geral',
              dominioPerc: domPerc,
              nivel: getClasse(domPerc),
              taxaAcerto: a.taxa_acerto || 0,
              questoes: a.questoes_respondidas || 0,
              revisoes: a.numero_revisoes || 0,
              status: a.status
            };
          }).sort((a: any, b: any) => b.dominioPerc - a.dominioPerc);

          setAmvMetrics({
            dominados: dom,
            emAprendizagem: emApr,
            reconhecimento: rec,
            lista: amvItems
          });
        }
      } catch (err) {
        console.error('Erro ao carregar estatísticas completas:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
  }, [user, isAdmin]);

  const pieData = [
    { name: 'Acertos', value: statsGerais.acertos, color: '#06f0a8' },
    { name: 'Erros', value: statsGerais.erros, color: '#ef4444' }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px' }}>
        <RefreshCw className="animate-spin" size={32} color="var(--cor-secundaria)" />
        <p style={{ marginTop: '16px', color: 'var(--cor-texto-muted)' }}>Gerando diagnóstico e learning analytics avançado...</p>
      </div>
    );
  }

  const raioXFiltrado = raioXTopicos.filter(t => 
    t.topico.toLowerCase().includes(filtroRaioX.toLowerCase()) || 
    t.grupo.toLowerCase().includes(filtroRaioX.toLowerCase())
  );

  return (
    <div style={{ paddingBottom: '40px' }}>
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.6rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <BarChart3 size={26} color="var(--cor-primaria)" /> Radar do Edital: Learning Analytics 📊
        </h1>
        <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.9rem' }}>
          Métricas consolidadas de aproveitamento, curva de retenção temporal, motor AMV 2.0 e raio-x detalhado.
        </p>
      </div>

      {/* 1. SEÇÃO EXCLUSIVA ADMIN: PROGRESSO E DISTRIBUIÇÃO GLOBAL DO BANCO */}
      {isAdmin && (
        <div style={{ marginBottom: '36px', padding: '24px', borderRadius: '14px', background: 'rgba(255, 107, 0, 0.05)', border: '1px solid rgba(255, 107, 0, 0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Database size={20} color="var(--cor-primaria)" />
            <h2 style={{ fontSize: '1.2rem', color: 'var(--cor-primaria)' }}>Progresso do Banco de Questões (Admin) 🗃️</h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div className="glass-card" style={{ padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#22c55e', fontSize: '0.85rem', fontWeight: 600 }}>
                <CheckCircle size={16} /> Validadas ✅
              </div>
              <span style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '4px', display: 'block' }}>
                {adminBancoStats.validadas.toLocaleString('pt-BR')}
              </span>
            </div>

            <div className="glass-card" style={{ padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#eab308', fontSize: '0.85rem', fontWeight: 600 }}>
                <HelpCircle size={16} /> Aguardando Validação ⏳
              </div>
              <span style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '4px', display: 'block' }}>
                {adminBancoStats.aguardando.toLocaleString('pt-BR')}
              </span>
            </div>

            <div className="glass-card" style={{ padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444', fontSize: '0.85rem', fontWeight: 600 }}>
                <Trash2 size={16} /> Removidas 🗑️
              </div>
              <span style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '4px', display: 'block' }}>
                {adminBancoStats.removidas.toLocaleString('pt-BR')}
              </span>
            </div>
          </div>

          {/* Quadro: Distribuição do Banco de Questões 📚 */}
          <div className="glass-card" style={{ padding: '18px' }}>
            <h3 style={{ fontSize: '1.05rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--cor-texto-primario)' }}>
              <BookOpen size={18} color="var(--cor-secundaria)" /> Distribuição do Banco de Questões 📚
            </h3>
            {adminBancoStats.distribuicao.length === 0 ? (
              <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.85rem' }}>Nenhuma distribuição disponível.</p>
            ) : (
              <div style={{ maxHeight: '240px', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--cor-texto-muted)' }}>
                      <th style={{ textAlign: 'left', padding: '8px' }}>Grupo / Matéria</th>
                      <th style={{ textAlign: 'left', padding: '8px' }}>Subgrupo</th>
                      <th style={{ textAlign: 'center', padding: '8px' }}>Quantidade</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminBancoStats.distribuicao.map((d, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '8px', fontWeight: 600 }}>{d.grupo}</td>
                        <td style={{ padding: '8px' }}>{d.subgrupo}</td>
                        <td style={{ textAlign: 'center', padding: '8px', fontWeight: 700, color: 'var(--cor-secundaria)' }}>{d.qtd}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 2. CARDS DE MÉTRICAS GERAIS DO USUÁRIO */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '18px',
        marginBottom: '32px'
      }}>
        <div className="glass-card" style={{ padding: '22px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Total de Questões</span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800 }}>{statsGerais.totalRespondidas}</span>
        </div>

        <div className="glass-card" style={{ padding: '22px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Total de Acertos</span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--cor-secundaria)' }}>{statsGerais.acertos}</span>
        </div>

        <div className="glass-card" style={{ padding: '22px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Total de Erros</span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: '#ef4444' }}>{statsGerais.erros}</span>
        </div>

        <div className="glass-card" style={{ padding: '22px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Taxa Geral de Retenção</span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: statsGerais.taxa >= 75 ? 'var(--cor-secundaria)' : '#FF8C00' }}>
            {statsGerais.taxa}%
          </span>
        </div>
      </div>

      {/* 3. MÉTRICAS DE DESEMPENHO POR MATÉRIA (TABELA + GRÁFICO HORIZONTAL PERFEITAMENTE ALINHADOS) */}
      <div style={{ marginBottom: '36px' }}>
        <h2 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={20} color="var(--cor-secundaria)" /> Métricas de Desempenho por Matéria 📊
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '24px', alignItems: 'stretch' }}>
          {/* Tabela de Matérias */}
          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '100%', minHeight: '480px' }}>
            <h3 style={{ fontSize: '1.05rem', marginBottom: '14px', color: 'var(--cor-texto-primario)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BookOpen size={18} color="var(--cor-secundaria)" /> Métricas Consolidadas por Disciplina
            </h3>
            {statsMaterias.length === 0 ? (
              <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.85rem' }}>Nenhuma resposta registrada.</p>
            ) : (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--cor-texto-muted)' }}>
                      <th style={{ textAlign: 'left', padding: '10px 8px' }}>Disciplina</th>
                      <th style={{ textAlign: 'center', padding: '10px 8px' }}>Respondidas</th>
                      <th style={{ textAlign: 'center', padding: '10px 8px' }}>Acertos</th>
                      <th style={{ textAlign: 'center', padding: '10px 8px' }}>% Acerto</th>
                    </tr>
                  </thead>
                  <tbody>
                    {statsMaterias.map((m, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '9px 8px', fontWeight: 600, maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {m.materia}
                        </td>
                        <td style={{ textAlign: 'center', padding: '9px 8px' }}>{m.total}</td>
                        <td style={{ textAlign: 'center', padding: '9px 8px', color: 'var(--cor-secundaria)' }}>{m.acertos}</td>
                        <td style={{ textAlign: 'center', padding: '9px 8px', fontWeight: 700, color: m.taxa >= 75 ? 'var(--cor-secundaria)' : m.taxa >= 50 ? 'var(--cor-primaria)' : '#ef4444' }}>
                          {m.taxa}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* Linha de Total Destacada no Fim da Tabela */}
                <div style={{
                  marginTop: '12px',
                  padding: '12px 14px',
                  borderRadius: '8px',
                  background: 'rgba(255, 107, 0, 0.08)',
                  border: '1px solid rgba(255, 107, 0, 0.25)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontWeight: 800,
                  fontSize: '0.85rem'
                }}>
                  <span style={{ color: 'var(--cor-primaria)' }}>TOTAL (Média Geral):</span>
                  <div style={{ display: 'flex', gap: '20px' }}>
                    <span>Resp: <strong>{statsGerais.totalRespondidas}</strong></span>
                    <span style={{ color: 'var(--cor-secundaria)' }}>Acertos: <strong>{statsGerais.acertos}</strong></span>
                    <span style={{ color: 'var(--cor-secundaria)' }}>Taxa: <strong>{statsGerais.taxa}%</strong></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Gráfico Horizontal de Barras (Mesma Altura e Tamanho da Tabela) */}
          <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '100%', minHeight: '480px' }}>
            <h3 style={{ fontSize: '1.05rem', marginBottom: '14px', color: 'var(--cor-texto-primario)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart3 size={18} color="var(--cor-primaria)" /> Gráfico de Aproveitamento por Disciplina (%)
            </h3>
            
            <div style={{ flex: 1, width: '100%', minHeight: '360px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={statsMaterias}
                  layout="vertical"
                  margin={{ top: 10, right: 30, left: 10, bottom: 0 }}
                >
                  <XAxis type="number" domain={[0, 100]} stroke="var(--cor-texto-muted)" fontSize={11} unit="%" />
                  <YAxis
                    dataKey="materia"
                    type="category"
                    stroke="var(--cor-texto-muted)"
                    fontSize={10}
                    width={160}
                    tick={(props: any) => {
                      const { x, y, payload } = props;
                      const text = payload.value.length > 24 ? `${payload.value.slice(0, 24)}...` : payload.value;
                      return (
                        <text
                          x={15}
                          y={y}
                          dy={4}
                          textAnchor="start"
                          fill="var(--cor-texto-muted)"
                          fontSize={10}
                          fontWeight={500}
                        >
                          {text}
                        </text>
                      );
                    }}
                  />
                  <Tooltip
                    contentStyle={{ background: '#0d1527', border: '1px solid var(--cor-borda)', borderRadius: '8px' }}
                    formatter={(val: any) => [`${val}%`, 'Taxa de Acerto']}
                  />
                  <Bar dataKey="taxa" fill="var(--cor-secundaria)" radius={[0, 6, 6, 0]}>
                    {statsMaterias.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.taxa >= 75 ? 'var(--cor-secundaria)' : entry.taxa >= 50 ? 'var(--cor-primaria)' : '#ef4444'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Rodapé do Card: Resumo Geral */}
            <div style={{
              marginTop: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-around',
              background: 'rgba(0,0,0,0.35)',
              padding: '10px',
              borderRadius: '8px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--cor-secundaria)' }}></span>
                <span>Acertos: <strong>{statsGerais.acertos}</strong></span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }}></span>
                <span>Erros: <strong>{statsGerais.erros}</strong></span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--cor-primaria)' }}></span>
                <span>Retenção Geral: <strong>{statsGerais.taxa}%</strong></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. EVOLUÇÃO TEMPORAL (DD/MM E LINHA DE META DE 80%) */}
      <div style={{ marginBottom: '36px' }}>
        <h2 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={20} color="var(--cor-primaria)" /> Evolução Temporal 📈
        </h2>

        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--cor-texto-muted)' }}>
              Comparativo entre a Taxa do Dia (DD/MM) vs Taxa Geral Acumulada (Meta de corte em 80%):
            </span>
          </div>

          {evolucaoTemporal.length === 0 ? (
            <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.85rem' }}>Responda mais questões para visualizar seu gráfico de evolução temporal.</p>
          ) : (
            <div style={{ width: '100%', height: '320px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={evolucaoTemporal} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="data" stroke="var(--cor-texto-muted)" fontSize={11} />
                  <YAxis domain={[0, 100]} stroke="var(--cor-texto-muted)" fontSize={11} />
                  <Tooltip contentStyle={{ background: '#0d1527', border: '1px solid var(--cor-borda)', borderRadius: '8px' }} />
                  <Legend />
                  <ReferenceLine y={80} stroke="#ef4444" strokeDasharray="5 5" label={{ value: 'Meta (80%)', fill: '#ef4444', fontSize: 11 }} />
                  <Line type="monotone" dataKey="taxaDia" name="Acerto Dia (%)" stroke="var(--cor-secundaria)" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="taxaAcum" name="Acerto Geral (%)" stroke="var(--cor-primaria)" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* 5. ÍNDICE DE DOMÍNIO (AMV 2.0) */}
      <div style={{ marginBottom: '36px' }}>
        <h2 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Brain size={20} color="var(--cor-secundaria)" /> Índice de Domínio (AMV 2.0) 🧠
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
          <div className="glass-card" style={{ padding: '18px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Subgrupos Dominados 🏆</span>
            <span style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--cor-secundaria)' }}>{amvMetrics.dominados}</span>
          </div>

          <div className="glass-card" style={{ padding: '18px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Em Aprendizagem 📈</span>
            <span style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--cor-primaria)' }}>{amvMetrics.emAprendizagem}</span>
          </div>

          <div className="glass-card" style={{ padding: '18px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)', display: 'block' }}>Reconhecimento Inic 🔍</span>
            <span style={{ fontSize: '1.6rem', fontWeight: 800, color: '#eab308' }}>{amvMetrics.reconhecimento}</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px', overflowX: 'auto' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '14px', color: 'var(--cor-texto-muted)' }}>Classificação por Nível de Domínio Cognitivo</h3>
          {amvMetrics.lista.length === 0 ? (
            <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.85rem' }}>Ainda não há dados no motor de aprendizagem. Comece a estudar no módulo Hoje!</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--cor-texto-muted)' }}>
                  <th style={{ textAlign: 'left', padding: '8px' }}>Tópico</th>
                  <th style={{ textAlign: 'center', padding: '8px' }}>Nível</th>
                  <th style={{ textAlign: 'center', padding: '8px' }}>Índice</th>
                  <th style={{ textAlign: 'center', padding: '8px' }}>Acertos</th>
                  <th style={{ textAlign: 'center', padding: '8px' }}>Questões</th>
                  <th style={{ textAlign: 'center', padding: '8px' }}>Revisões</th>
                  <th style={{ textAlign: 'center', padding: '8px' }}>Status AMV</th>
                </tr>
              </thead>
              <tbody>
                {amvMetrics.lista.slice(0, 15).map(it => (
                  <tr key={it.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '8px', fontWeight: 600 }}>{it.topico}</td>
                    <td style={{ textAlign: 'center', padding: '8px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        background: it.nivel === 'Dominado' ? 'rgba(6, 240, 168, 0.2)' : 'rgba(255, 107, 0, 0.2)',
                        color: it.nivel === 'Dominado' ? 'var(--cor-secundaria)' : 'var(--cor-primaria)'
                      }}>
                        {it.nivel}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center', padding: '8px', fontWeight: 700 }}>{it.dominioPerc}%</td>
                    <td style={{ textAlign: 'center', padding: '8px', color: 'var(--cor-secundaria)' }}>{it.taxaAcerto}%</td>
                    <td style={{ textAlign: 'center', padding: '8px' }}>{it.questoes}</td>
                    <td style={{ textAlign: 'center', padding: '8px' }}>{it.revisoes}</td>
                    <td style={{ textAlign: 'center', padding: '8px', color: 'var(--cor-texto-muted)', fontSize: '0.8rem' }}>{it.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* 6. DESEMPENHO POR TÓPICO (RAIO-X CIRÚRGICO COM QUANTIDADE E TAXA) */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <h2 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Award size={20} color="var(--cor-primaria)" /> Desempenho por Tópico (Raio-X) 🔬
          </h2>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(0,0,0,0.3)', padding: '6px 12px', borderRadius: '8px', border: '1px solid var(--cor-borda)' }}>
            <Search size={16} color="var(--cor-texto-muted)" />
            <input
              type="text"
              placeholder="Buscar tópico ou matéria..."
              value={filtroRaioX}
              onChange={e => setFiltroRaioX(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: '#fff', fontSize: '0.85rem', outline: 'none' }}
            />
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px', overflowX: 'auto' }}>
          {raioXFiltrado.length === 0 ? (
            <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.85rem' }}>Nenhum tópico encontrado.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--cor-texto-muted)' }}>
                  <th style={{ textAlign: 'left', padding: '8px' }}>Tópico (Subgrupo ➔ Item)</th>
                  <th style={{ textAlign: 'center', padding: '8px' }}>Questões</th>
                  <th style={{ textAlign: 'center', padding: '8px' }}>Acertos</th>
                  <th style={{ textAlign: 'left', padding: '8px', minWidth: '220px' }}>Taxa de Acerto (%)</th>
                </tr>
              </thead>
              <tbody>
                {raioXFiltrado.map((t, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '10px 8px', fontWeight: 600 }}>{t.topico}</td>
                    <td style={{ textAlign: 'center', padding: '10px 8px', fontWeight: 700 }}>{t.total}</td>
                    <td style={{ textAlign: 'center', padding: '10px 8px', color: 'var(--cor-secundaria)' }}>{t.acertos}</td>
                    <td style={{ padding: '10px 8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{ flex: 1, height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{
                            width: `${t.taxa}%`,
                            height: '100%',
                            background: t.taxa >= 75 ? 'var(--cor-secundaria)' : t.taxa >= 50 ? 'var(--cor-primaria)' : '#ef4444'
                          }} />
                        </div>
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, minWidth: '45px' }}>{t.taxa}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
