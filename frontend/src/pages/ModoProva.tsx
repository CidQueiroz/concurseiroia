import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useAI } from '../context/AIContext';
import { supabase } from '../config/supabase';
import { generateAIAnswer } from '../services/aiService';
import { FileText, Play, CheckCircle2, XCircle, Clock, Sparkles, MessageSquare, RefreshCw } from 'lucide-react';

export const ModoProva: React.FC = () => {
  const { user } = useAuth();
  const { keys, preferredBanca } = useAI();
  const [questoes, setQuestoes] = useState<any[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [emAndamento, setEmAndamento] = useState(false);
  const [loading, setLoading] = useState(false);
  const [gerandoIA, setGerandoIA] = useState(false);

  // Filtros em cascata (Grupo -> Subgrupo -> Item de Estudo)
  const [temasDisponiveis, setTemasDisponiveis] = useState<string[]>([]);
  const [temasSelecionados, setTemasSelecionados] = useState<string[]>([]);

  const [subgruposDisponiveis, setSubgruposDisponiveis] = useState<string[]>([]);
  const [subgruposSelecionados, setSubgruposSelecionados] = useState<string[]>([]);

  const [itensDisponiveis, setItensDisponiveis] = useState<string[]>([]);
  const [itensSelecionados, setItensSelecionados] = useState<string[]>([]);

  const [apenasIneditas, setApenasIneditas] = useState(true);
  const [qtdQuestoes, setQtdQuestoes] = useState<number>(20);

  // Estado da questão atual
  const [respostaDada, setRespostaDada] = useState<string | null>(null);
  const [acertou, setAcertou] = useState<boolean | null>(null);
  const [tempoSegundos, setTempoSegundos] = useState(0);
  const [score, setScore] = useState({ basic: 0, esp: 0, totalAcertos: 0 });

  // Chat com o Tutor IA
  const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'assistant'; text: string }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // 1. Carregar Temas (Grupos) disponíveis
  useEffect(() => {
    if (!user) return;
    const carregarGrupos = async () => {
      try {
        const { data: aprData } = await supabase
          .from('aprendizado_item')
          .select('itens_estudo(subgrupos(grupos(nome)))')
          .eq('user_id', user.id);

        const gruposSet = new Set<string>();
        aprData?.forEach((it: any) => {
          const gNome = it.itens_estudo?.subgrupos?.grupos?.nome;
          if (gNome && !['FORA DO EDITAL', 'NÃO CLASSIFICADO', 'NAO CLASSIFICADO'].includes(gNome.toUpperCase())) {
            gruposSet.add(gNome);
          }
        });

        const listaTemas = Array.from(gruposSet).sort();
        setTemasDisponiveis(listaTemas);
      } catch (err) {
        console.error('Erro ao carregar temas do simulado:', err);
      }
    };
    carregarGrupos();
  }, [user]);

  // 2. Quando seleciona exatamente 1 Grupo, carregar os Subgrupos correspondentes
  useEffect(() => {
    if (temasSelecionados.length === 1) {
      const carregarSubgrupos = async () => {
        try {
          const { data: subData } = await supabase
            .from('subgrupos')
            .select('nome, grupos!inner(nome)')
            .eq('grupos.nome', temasSelecionados[0]);

          const subs = subData ? subData.map((s: any) => s.nome) : [];
          setSubgruposDisponiveis(subs);
          setSubgruposSelecionados([]);
          setItensDisponiveis([]);
          setItensSelecionados([]);
        } catch (err) {
          console.error('Erro ao carregar subgrupos:', err);
        }
      };
      carregarSubgrupos();
    } else {
      // Se selecionou mais de 1 ou nenhum, limpa os níveis filhos
      setSubgruposDisponiveis([]);
      setSubgruposSelecionados([]);
      setItensDisponiveis([]);
      setItensSelecionados([]);
    }
  }, [temasSelecionados]);

  // 3. Quando seleciona exatamente 1 Subgrupo, carregar os Itens de Estudo correspondentes
  useEffect(() => {
    if (subgruposSelecionados.length === 1) {
      const carregarItens = async () => {
        try {
          const { data: itemData } = await supabase
            .from('itens_estudo')
            .select('nome, subgrupos!inner(nome)')
            .eq('subgrupos.nome', subgruposSelecionados[0]);

          const its = itemData ? itemData.map((i: any) => i.nome) : [];
          setItensDisponiveis(its);
          setItensSelecionados([]);
        } catch (err) {
          console.error('Erro ao carregar itens de estudo:', err);
        }
      };
      carregarItens();
    } else {
      // Se selecionou mais de 1 subgrupo ou nenhum, limpa itens
      setItensDisponiveis([]);
      setItensSelecionados([]);
    }
  }, [subgruposSelecionados]);

  // Timer
  useEffect(() => {
    let timer: any;
    if (emAndamento) {
      timer = setInterval(() => {
        setTempoSegundos(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [emAndamento]);

  const iniciarSimulado = async () => {
    if (!user) return;
    setLoading(true);

    try {
      let query = supabase
        .from('questoes')
        .select('*, itens_estudo!inner(nome, subgrupos!inner(nome, grupos!inner(nome)))')
        .gte('valida', 0);

      // Hierarquia em cascata:
      // A) Se selecionou itens específicos:
      if (itensSelecionados.length > 0) {
        query = query.in('itens_estudo.nome', itensSelecionados);
      }
      // B) Se selecionou subgrupos:
      else if (subgruposSelecionados.length > 0) {
        query = query.in('itens_estudo.subgrupos.nome', subgruposSelecionados);
      }
      // C) Se selecionou grupos/temas:
      else if (temasSelecionados.length > 0) {
        query = query.in('itens_estudo.subgrupos.grupos.nome', temasSelecionados);
      }

      const { data: qData, error: qErr } = await query.limit(200);

      if (qErr || !qData || qData.length === 0) {
        alert('Nenhuma questão encontrada para a combinação de filtros selecionada. Experimente gerar uma questão inédita com IA abaixo!');
        setLoading(false);
        return;
      }

      let filtradas = qData;

      // Filtrar apenas inéditas se marcado
      if (apenasIneditas) {
        const { data: respHist } = await supabase
          .from('respostas')
          .select('questao_id')
          .eq('user_id', user.id);

        const respSet = new Set(respHist?.map((r: any) => r.questao_id) || []);
        const ineditas = qData.filter((q: any) => !respSet.has(q.id));

        if (ineditas.length > 0) {
          filtradas = ineditas;
        }
      }

      // Shuffle e limita à quantidade selecionada
      const shuffled = [...filtradas].sort(() => 0.5 - Math.random()).slice(0, qtdQuestoes);
      setQuestoes(shuffled);
      setCurrentIndex(0);
      setEmAndamento(true);
      setRespostaDada(null);
      setAcertou(null);
      setTempoSegundos(0);
      setScore({ basic: 0, esp: 0, totalAcertos: 0 });
      setChatHistory([]);
    } catch (err) {
      console.error('Erro ao iniciar simulado:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGerarQuestaoIA = async () => {
    if (temasSelecionados.length === 0) {
      alert('Selecione ao menos um tema/grupo primeiro.');
      return;
    }
    setGerandoIA(true);

    try {
      const temaAlvo = temasSelecionados[0];
      const subAlvo = subgruposSelecionados.length > 0 ? subgruposSelecionados[0] : (subgruposDisponiveis[0] || 'Geral');
      const itemAlvo = itensSelecionados.length > 0 ? itensSelecionados[0] : (itensDisponiveis[0] || '');
      const escopo = itemAlvo ? `${temaAlvo} ➔ ${subAlvo} ➔ ${itemAlvo}` : `${temaAlvo} ➔ ${subAlvo}`;

      // 1. Obter item_id válido para vincular a questão no Supabase
      let item_id: number | null = null;
      if (itemAlvo) {
        const { data: itData } = await supabase
          .from('itens_estudo')
          .select('id')
          .eq('nome', itemAlvo)
          .limit(1);
        if (itData && itData.length > 0) item_id = itData[0].id;
      } else {
        const { data: itData } = await supabase
          .from('itens_estudo')
          .select('id, subgrupos!inner(nome)')
          .eq('subgrupos.nome', subAlvo)
          .limit(1);
        if (itData && itData.length > 0) item_id = itData[0].id;
      }

      const prompt = `Gere 1 questão inédita de concurso público no estilo da banca ${preferredBanca || 'FGV/Cebraspe'} sobre: "${escopo}".
      Responda ESTRITAMENTE em formato JSON com a seguinte estrutura:
      {
        "enunciado": "texto claro e contextualizado do enunciado",
        "a": "texto da alternativa A",
        "b": "texto da alternativa B",
        "c": "texto da alternativa C",
        "d": "texto da alternativa D",
        "e": "texto da alternativa E",
        "gabarito": "A",
        "explicacao": "justificativa do gabarito"
      }`;

      const res = await generateAIAnswer(keys, prompt, 'Você é uma banca examinadora de elite gerando questões técnicas de alto nível para concurso público.');
      if (res.content) {
        const match = res.content.match(/\{[\s\S]*\}/);
        if (match) {
          const qJson = JSON.parse(match[0]);
          
          const { error: insErr } = await supabase.from('questoes').insert({
            item_id: item_id,
            banca: preferredBanca || 'IA-Gerada',
            enunciado: qJson.enunciado,
            alternativa_a: qJson.a,
            alternativa_b: qJson.b,
            alternativa_c: qJson.c,
            alternativa_d: qJson.d,
            alternativa_e: qJson.e,
            gabarito: qJson.gabarito || 'A',
            valida: 1
          });

          if (insErr) {
            console.error('Erro Supabase ao salvar questão:', insErr);
            alert(`Erro ao salvar no banco: ${insErr.message}`);
          } else {
            alert(`✨ Questão gerada e salva com sucesso no banco para ${escopo}!\n\nClique em "Iniciar Novo Simulado" para respondê-la.`);
          }
        } else {
          alert('A IA gerou a resposta mas não no formato JSON esperado.');
        }
      } else {
        alert(res.error || 'Erro ao gerar questão. Verifique suas chaves de API em Configurar IA.');
      }
    } catch (err: any) {
      console.error('Erro ao gerar questão com IA:', err);
      alert(`Falha ao gerar questão por IA: ${err?.message || 'Verifique o console'}`);
    } finally {
      setGerandoIA(false);
    }
  };

  const handleResponder = async (alt: string) => {
    if (!user || respostaDada) return;
    const qAtual = questoes[currentIndex];
    const isCorreta = alt.toUpperCase().trim() === qAtual.gabarito.toUpperCase().trim();

    setRespostaDada(alt);
    setAcertou(isCorreta);

    const isEspecial = qAtual.itens_estudo?.subgrupos?.grupos?.nome?.includes('Específicos');
    const peso = isEspecial ? 2.0 : 1.0;
    const scoreAdd = isCorreta ? peso : -peso;

    setScore(prev => ({
      basic: isEspecial ? prev.basic : prev.basic + scoreAdd,
      esp: isEspecial ? prev.esp + scoreAdd : prev.esp,
      totalAcertos: prev.totalAcertos + (isCorreta ? 1 : 0)
    }));

    // Registrar no Supabase
    await supabase.from('respostas').insert({
      user_id: user.id,
      questao_id: qAtual.id,
      resposta_usuario: alt,
      acertou: isCorreta,
      tempo_segundos: tempoSegundos,
      data: new Date().toISOString()
    });
  };

  const handleProximaQuestao = () => {
    if (currentIndex < questoes.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setRespostaDada(null);
      setAcertou(null);
      setChatHistory([]);
    } else {
      alert('Simulado finalizado! Parabéns pelo seu treino!');
      setEmAndamento(false);
    }
  };

  const handleEnviarDuvidaIA = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const qAtual = questoes[currentIndex];
    const userMsg = chatInput.trim();
    setChatInput('');
    setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setChatLoading(true);

    const prompt = `Questão: "${qAtual.enunciado}"\nGabarito Oficial: ${qAtual.gabarito}\nMinha Dúvida: ${userMsg}\n\nExplique de forma objetiva o porquê do gabarito e tire minha dúvida com clareza.`;
    const res = await generateAIAnswer(keys, prompt, `Você é o Tutor IA do AprovaTeck, especialista na banca ${preferredBanca}.`);

    if (res.content) {
      setChatHistory(prev => [...prev, { role: 'assistant', text: res.content }]);
    } else {
      setChatHistory(prev => [...prev, { role: 'assistant', text: res.error || 'Erro ao consultar Tutor IA.' }]);
    }
    setChatLoading(false);
  };

  const formatTempo = (sec: number) => {
    const min = Math.floor(sec / 60);
    const s = sec % 60;
    return `${min.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const qAtual = questoes[currentIndex];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.6rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FileText size={26} color="var(--cor-primaria)" /> Modo Prova 📝
        </h1>
        <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.9rem' }}>
          Treino em condições reais de prova com pontuação líquida (+/-) e Tutor IA tira-dúvidas.
        </p>
      </div>

      {!emAndamento ? (
        <div className="glass-card" style={{ padding: '36px', maxWidth: '750px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '1.3rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={20} color="var(--cor-secundaria)" /> Configurar Simulado
          </h2>

          {/* 1. Seleção de Grupos / Temas (Multi-Select) */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--cor-texto)' }}>
                1. Selecione os Grupos / Matérias ({temasSelecionados.length} selecionados):
              </label>
              <button
                type="button"
                onClick={() => {
                  if (temasSelecionados.length === temasDisponiveis.length) {
                    setTemasSelecionados([]);
                  } else {
                    setTemasSelecionados([...temasDisponiveis]);
                  }
                }}
                style={{ background: 'transparent', border: 'none', color: 'var(--cor-primaria)', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 600 }}
              >
                {temasSelecionados.length === temasDisponiveis.length ? 'Desmarcar Todos' : 'Selecionar Todos'}
              </button>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {temasDisponiveis.map(t => {
                const isSelected = temasSelecionados.includes(t);
                return (
                  <button
                    key={t}
                    type="button"
                    onClick={() => {
                      if (isSelected) {
                        setTemasSelecionados(prev => prev.filter(item => item !== t));
                      } else {
                        setTemasSelecionados(prev => [...prev, t]);
                      }
                    }}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '8px',
                      border: isSelected ? '1px solid var(--cor-primaria)' : '1px solid rgba(255, 255, 255, 0.1)',
                      background: isSelected ? 'rgba(255, 107, 0, 0.2)' : 'rgba(0, 0, 0, 0.25)',
                      color: isSelected ? 'var(--cor-primaria)' : 'var(--cor-texto)',
                      fontSize: '0.85rem',
                      fontWeight: isSelected ? 700 : 400,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {t}
                  </button>
                );
              })}
            </div>
            {temasSelecionados.length > 1 && (
              <p style={{ fontSize: '0.78rem', color: 'var(--cor-secundaria)', marginTop: '6px' }}>
                💡 Você selecionou múltiplos grupos. Todos os subgrupos e itens correspondentes serão incluídos no simulado.
              </p>
            )}
          </div>

          {/* 2. Seleção de Subgrupos (Aparece quando exatamente 1 Grupo está selecionado) */}
          {temasSelecionados.length === 1 && (
            <div style={{ marginBottom: '20px', padding: '16px', borderRadius: '10px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--cor-texto)' }}>
                  2. Subtópicos de "{temasSelecionados[0]}" (Opcional):
                </label>
                {subgruposDisponiveis.length > 0 && (
                  <span style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)' }}>
                    {subgruposSelecionados.length === 0 ? 'Todos incluídos' : `${subgruposSelecionados.length} selecionado(s)`}
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {subgruposDisponiveis.map(sub => {
                  const isSelected = subgruposSelecionados.includes(sub);
                  return (
                    <button
                      key={sub}
                      type="button"
                      onClick={() => {
                        if (isSelected) {
                          setSubgruposSelecionados(prev => prev.filter(s => s !== sub));
                        } else {
                          setSubgruposSelecionados(prev => [...prev, sub]);
                        }
                      }}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        border: isSelected ? '1px solid var(--cor-secundaria)' : '1px solid rgba(255, 255, 255, 0.1)',
                        background: isSelected ? 'rgba(6, 240, 168, 0.15)' : 'rgba(0, 0, 0, 0.25)',
                        color: isSelected ? 'var(--cor-secundaria)' : 'var(--cor-texto)',
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      {sub}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* 3. Seleção de Itens Específicos (Aparece quando exatamente 1 Subgrupo está selecionado) */}
          {subgruposSelecionados.length === 1 && (
            <div style={{ marginBottom: '20px', padding: '16px', borderRadius: '10px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <label style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--cor-texto)' }}>
                  3. Itens de Estudo de "{subgruposSelecionados[0]}" (Opcional):
                </label>
                {itensDisponiveis.length > 0 && (
                  <span style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)' }}>
                    {itensSelecionados.length === 0 ? 'Todos incluídos' : `${itensSelecionados.length} selecionado(s)`}
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {itensDisponiveis.map(it => {
                  const isSelected = itensSelecionados.includes(it);
                  return (
                    <button
                      key={it}
                      type="button"
                      onClick={() => {
                        if (isSelected) {
                          setItensSelecionados(prev => prev.filter(i => i !== it));
                        } else {
                          setItensSelecionados(prev => [...prev, it]);
                        }
                      }}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        border: isSelected ? '1px solid var(--cor-primaria)' : '1px solid rgba(255, 255, 255, 0.1)',
                        background: isSelected ? 'rgba(255, 107, 0, 0.2)' : 'rgba(0, 0, 0, 0.25)',
                        color: isSelected ? 'var(--cor-primaria)' : 'var(--cor-texto)',
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      {it}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* 4. Somente Inéditas & Quantidade */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '24px', padding: '14px', borderRadius: '8px', background: 'rgba(0,0,0,0.2)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.9rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={apenasIneditas}
                onChange={e => setApenasIneditas(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: 'var(--cor-primaria)' }}
              />
              <span>Somente questões inéditas (ainda não respondidas)</span>
            </label>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--cor-texto-muted)' }}>Quantidade:</span>
              <div style={{ display: 'flex', gap: '6px' }}>
                {[10, 20, 30, 50].map(q => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => setQtdQuestoes(q)}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      border: qtdQuestoes === q ? '1px solid var(--cor-primaria)' : '1px solid rgba(255, 255, 255, 0.1)',
                      background: qtdQuestoes === q ? 'rgba(255, 107, 0, 0.2)' : 'rgba(0,0,0,0.3)',
                      color: qtdQuestoes === q ? 'var(--cor-primaria)' : '#fff',
                      fontSize: '0.85rem',
                      fontWeight: qtdQuestoes === q ? 700 : 400,
                      cursor: 'pointer'
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 5. Gerador IA Opcional */}
          <div style={{ padding: '16px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.08)', background: 'rgba(0, 0, 0, 0.25)', marginBottom: '28px' }}>
            <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--cor-primaria)' }}>
              <Sparkles size={16} /> Gerador IA (Opcional):
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)', marginBottom: '12px' }}>
              Gera questões inéditas contextualizadas no escopo selecionado acima (Grupo ➔ Subgrupo ➔ Item).
            </p>
            <button
              onClick={handleGerarQuestaoIA}
              disabled={gerandoIA || temasSelecionados.length === 0}
              className="btn-sovereign btn-secondary"
              style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px', cursor: temasSelecionados.length === 0 ? 'not-allowed' : 'pointer' }}
            >
              {gerandoIA ? <RefreshCw className="animate-spin" size={16} /> : <Sparkles size={16} />}
              {gerandoIA ? 'Gerando questão inédita com IA...' : '✨ Gerar Questão Inédita com IA para a seleção atual'}
            </button>
          </div>

          {/* 6. Ações Iniciar / Limpar */}
          <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
            <button
              onClick={iniciarSimulado}
              disabled={loading || gerandoIA}
              className="btn-sovereign btn-primary"
              style={{ flex: 1, padding: '14px 24px', fontSize: '1rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
            >
              {loading ? <RefreshCw className="animate-spin" size={18} /> : <Play size={18} />}
              Iniciar Novo Simulado
            </button>
            <button
              onClick={() => {
                setTemasSelecionados([]);
                setSubgruposSelecionados([]);
                setItensSelecionados([]);
                setApenasIneditas(true);
              }}
              className="btn-sovereign btn-secondary"
              style={{ padding: '14px 20px', fontSize: '0.95rem' }}
            >
              Limpar Filtros
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '24px' }}>
          {/* Painel da Questão */}
          <div className="glass-card" style={{ padding: '28px' }}>
            {/* Header da Questão */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <span style={{ fontSize: '0.8rem', color: 'var(--cor-secundaria)', fontWeight: 700 }}>
                  Questão {currentIndex + 1} de {questoes.length}
                </span>
                <div style={{ fontSize: '0.75rem', color: 'var(--cor-texto-muted)', marginTop: '2px' }}>
                  {qAtual?.itens_estudo?.subgrupos?.grupos?.nome} ➔ {qAtual?.itens_estudo?.nome}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--cor-primaria)', fontWeight: 700 }}>
                <Clock size={18} />
                <span>{formatTempo(tempoSegundos)}</span>
              </div>
            </div>

            <div style={{
              padding: '24px',
              borderRadius: '12px',
              background: 'rgba(0, 0, 0, 0.25)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              fontSize: '1rem',
              lineHeight: 1.7,
              marginBottom: '24px'
            }}>
              {qAtual?.enunciado}
            </div>

            {(() => {
              const hasMultiplaEscolha = !!(qAtual?.alternativa_a || qAtual?.alternativa_b || qAtual?.alternativa_c || qAtual?.alternativa_d);
              
              if (hasMultiplaEscolha) {
                const alts = [
                  { key: 'A', text: qAtual.alternativa_a },
                  { key: 'B', text: qAtual.alternativa_b },
                  { key: 'C', text: qAtual.alternativa_c },
                  { key: 'D', text: qAtual.alternativa_d },
                  { key: 'E', text: qAtual.alternativa_e },
                ].filter(a => a.text && a.text.trim() !== '' && a.text !== 'N/A');

                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
                    {alts.map(alt => {
                      const isSelected = respostaDada === alt.key;
                      const isCorrect = qAtual.gabarito?.trim().toUpperCase() === alt.key;
                      let bg = 'rgba(0, 0, 0, 0.3)';
                      let borderColor = 'rgba(255, 255, 255, 0.1)';

                      if (respostaDada) {
                        if (isSelected) {
                          bg = isCorrect ? 'rgba(6, 240, 168, 0.2)' : 'rgba(239, 68, 68, 0.25)';
                          borderColor = isCorrect ? 'var(--cor-secundaria)' : '#ef4444';
                        } else if (isCorrect) {
                          bg = 'rgba(6, 240, 168, 0.15)';
                          borderColor = 'var(--cor-secundaria)';
                        }
                      }

                      return (
                        <button
                          key={alt.key}
                          disabled={!!respostaDada}
                          onClick={() => handleResponder(alt.key)}
                          style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: '14px',
                            padding: '16px 20px',
                            borderRadius: '12px',
                            border: `1px solid ${borderColor}`,
                            background: bg,
                            color: '#ffffff',
                            textAlign: 'left',
                            fontSize: '0.95rem',
                            lineHeight: 1.5,
                            cursor: respostaDada ? 'default' : 'pointer',
                            transition: 'all 0.2s ease'
                          }}
                        >
                          <span style={{
                            width: '28px',
                            height: '28px',
                            borderRadius: '50%',
                            background: isSelected ? 'var(--cor-primaria)' : 'rgba(255, 255, 255, 0.1)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 800,
                            fontSize: '0.85rem',
                            flexShrink: 0
                          }}>
                            {alt.key}
                          </span>
                          <span style={{ flex: 1, marginTop: '2px' }}>{alt.text}</span>
                        </button>
                      );
                    })}
                  </div>
                );
              }

              return (
                <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
                  {['C', 'E'].map(alt => (
                    <button
                      key={alt}
                      disabled={!!respostaDada}
                      onClick={() => handleResponder(alt)}
                      style={{
                        flex: 1,
                        padding: '16px',
                        borderRadius: '12px',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        background: respostaDada === alt
                          ? acertou ? 'rgba(6, 240, 168, 0.25)' : 'rgba(239, 68, 68, 0.25)'
                          : 'rgba(0, 0, 0, 0.3)',
                        color: '#ffffff',
                        fontSize: '1rem',
                        fontWeight: 700,
                        cursor: respostaDada ? 'default' : 'pointer'
                      }}
                    >
                      {alt === 'C' ? 'CERTO' : 'ERRADO'}
                    </button>
                  ))}
                </div>
              );
            })()}

            {respostaDada && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px 20px',
                borderRadius: '12px',
                background: acertou ? 'rgba(6, 240, 168, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                border: `1px solid ${acertou ? 'var(--cor-secundaria)' : '#ef4444'}`,
                marginBottom: '20px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  {acertou ? (
                    <>
                      <CheckCircle2 size={22} color="var(--cor-secundaria)" />
                      <span style={{ fontWeight: 700, color: 'var(--cor-secundaria)' }}>Parabéns, você acertou!</span>
                    </>
                  ) : (
                    <>
                      <XCircle size={22} color="#ef4444" />
                      <span style={{ fontWeight: 700, color: '#ef4444' }}>
                        Incorreto. Gabarito Oficial: {qAtual?.gabarito}
                      </span>
                    </>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => {
                      if (confirm('Deseja realmente encerrar o simulado agora?')) {
                        setEmAndamento(false);
                      }
                    }}
                    style={{
                      padding: '10px 16px',
                      borderRadius: '8px',
                      background: 'rgba(239, 68, 68, 0.2)',
                      border: '1px solid #ef4444',
                      color: '#ef4444',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Encerrar
                  </button>
                  <button
                    onClick={handleProximaQuestao}
                    className="btn-sovereign btn-primary"
                    style={{ padding: '10px 20px', fontSize: '0.95rem' }}
                  >
                    Próxima Questão ➔
                  </button>
                </div>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Placar Líquido */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '12px' }}>Placar Líquido (Estilo Cebraspe)</h3>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--cor-texto-muted)' }}>Acertos:</span>
                <strong style={{ color: 'var(--cor-secundaria)' }}>{score.totalAcertos} / {currentIndex + (respostaDada ? 1 : 0)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginTop: '6px' }}>
                <span style={{ color: 'var(--cor-texto-muted)' }}>Score Líquido:</span>
                <strong style={{ color: '#FF8C00' }}>{(score.basic + score.esp).toFixed(1)} pts</strong>
              </div>
            </div>

            {/* Chat com Tutor IA */}
            <div className="glass-card" style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Sparkles size={18} color="var(--cor-secundaria)" />
                <h3 style={{ fontSize: '0.95rem', margin: 0 }}>Tutor IA da Questão</h3>
              </div>

              <div style={{
                flex: 1,
                maxHeight: '260px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                marginBottom: '12px',
                paddingRight: '4px'
              }}>
                {chatHistory.length === 0 ? (
                  <p style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)' }}>
                    Ficou com dúvida no enunciado ou gabarito? Pergunte ao Tutor IA abaixo.
                  </p>
                ) : (
                  chatHistory.map((msg, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '10px 12px',
                        borderRadius: '8px',
                        fontSize: '0.8rem',
                        lineHeight: 1.4,
                        background: msg.role === 'user' ? 'rgba(255, 140, 0, 0.15)' : 'rgba(6, 240, 168, 0.1)',
                        alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        maxWidth: '90%'
                      }}
                    >
                      {msg.text}
                    </div>
                  ))
                )}
                {chatLoading && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--cor-secundaria)' }}>Tutor IA digitando...</span>
                )}
              </div>

              <form onSubmit={handleEnviarDuvidaIA} style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  placeholder="Dúvida sobre a questão..."
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--cor-texto)',
                    fontSize: '0.8rem',
                    outline: 'none'
                  }}
                />
                <button
                  type="submit"
                  disabled={chatLoading}
                  className="btn-sovereign btn-primary"
                  style={{ padding: '8px 12px' }}
                >
                  <MessageSquare size={14} />
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
