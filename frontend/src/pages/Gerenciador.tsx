import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../config/supabase';
import { 
  FolderKanban, 
  Search, 
  Plus, 
  Trash2, 
  Edit3, 
  CheckCircle, 
  RefreshCw, 
  Filter, 
  Layers, 
  Save, 
  Check, 
  X, 
  ChevronDown, 
  ChevronUp, 
  Sparkles,
  BookOpen
} from 'lucide-react';

export const Gerenciador: React.FC = () => {
  const { isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState<'busca' | 'tema' | 'add' | 'limpeza'>('busca');

  // Estado Geral de Questões Retornadas
  const [questoes, setQuestoes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Tab 1: Busca por Texto
  const [termoBusca, setTermoBusca] = useState('');

  // Tab 2: Filtro por Tema Hierárquico
  const [gruposDisponiveis, setGruposDisponiveis] = useState<any[]>([]);
  const [grupoSel, setGrupoSel] = useState<string>('');
  const [subgruposDisponiveis, setSubgruposDisponiveis] = useState<any[]>([]);
  const [subgrupoSel, setSubgrupoSel] = useState<string>('');
  const [itensDisponiveis, setItensDisponiveis] = useState<any[]>([]);
  const [itemSel, setItemSel] = useState<string>('');

  // Tab 3: Adicionar Questão
  const [addNovaMateria, setAddNovaMateria] = useState(false);
  const [addGrupoNome, setAddGrupoNome] = useState('');
  const [addNovoSubgrupo, setAddNovoSubgrupo] = useState(false);
  const [addSubgrupoNome, setAddSubgrupoNome] = useState('');
  const [addNovoItem, setAddNovoItem] = useState(false);
  const [addItemNome, setAddItemNome] = useState('');

  const [addEnunciado, setAddEnunciado] = useState('');
  const [addAltA, setAddAltA] = useState('');
  const [addAltB, setAddAltB] = useState('');
  const [addAltC, setAddAltC] = useState('');
  const [addAltD, setAddAltD] = useState('');
  const [addAltE, setAddAltE] = useState('');
  const [addGabarito, setAddGabarito] = useState('A');
  const [addBanca, setAddBanca] = useState('FGV');
  const [addAno, setAddAno] = useState('2024');
  const [savingAdd, setSavingAdd] = useState(false);

  // Tab 4: Limpeza de Tópicos Genéricos
  const [topicosGenericos, setTopicosGenericos] = useState<any[]>([]);
  const [loadingLimpeza, setLoadingLimpeza] = useState(false);
  const [novoNomeMap, setNovoNomeMap] = useState<{ [key: number]: string }>({});

  // Edição Inline de Questões
  const [expandedQuestaoId, setExpandedQuestaoId] = useState<number | null>(null);
  const [editFormData, setEditFormData] = useState<any>({});
  const [savingEdit, setSavingEdit] = useState<number | null>(null);

  // Carregar Grupos Iniciais
  useEffect(() => {
    if (!isAdmin) return;
    const carregarGrupos = async () => {
      const { data } = await supabase.from('grupos').select('id, nome').order('nome');
      if (data) setGruposDisponiveis(data);
    };
    carregarGrupos();
  }, [isAdmin]);

  // Carregar Subgrupos quando seleciona Grupo no Filtro por Tema
  useEffect(() => {
    if (!grupoSel) {
      setSubgruposDisponiveis([]);
      setSubgrupoSel('');
      return;
    }
    const gObj = gruposDisponiveis.find(g => g.nome === grupoSel);
    if (!gObj) return;

    const carregarSubs = async () => {
      const { data } = await supabase.from('subgrupos').select('id, nome').eq('grupo_id', gObj.id).order('nome');
      setSubgruposDisponiveis(data || []);
      setSubgrupoSel('');
    };
    carregarSubs();
  }, [grupoSel, gruposDisponiveis]);

  // Carregar Itens quando seleciona Subgrupo no Filtro por Tema
  useEffect(() => {
    if (!subgrupoSel) {
      setItensDisponiveis([]);
      setItemSel('');
      return;
    }
    const sObj = subgruposDisponiveis.find(s => s.nome === subgrupoSel);
    if (!sObj) return;

    const carregarItens = async () => {
      const { data } = await supabase.from('itens_estudo').select('id, nome').eq('subgrupo_id', sObj.id).order('nome');
      setItensDisponiveis(data || []);
      setItemSel('');
    };
    carregarItens();
  }, [subgrupoSel, subgruposDisponiveis]);

  // 1. Executar Busca por Texto
  const handleBuscaPorTexto = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!termoBusca.trim()) return;

    setLoading(true);
    try {
      const terms = termoBusca.trim().split(/\s+/);
      let query = supabase
        .from('questoes')
        .select('*, itens_estudo(id, subgrupo_id, nome, subgrupos(id, grupo_id, nome, grupos(id, nome)))');

      terms.forEach(t => {
        query = query.ilike('enunciado', `%${t}%`);
      });

      const { data, error } = await query.limit(100);
      if (!error && data) {
        setQuestoes(data);
      }
    } catch (err) {
      console.error('Erro ao buscar por texto:', err);
    } finally {
      setLoading(false);
    }
  };

  // 2. Executar Filtro por Tema
  const handleBuscaPorTema = async () => {
    if (!grupoSel) return;
    setLoading(true);

    try {
      let query = supabase
        .from('questoes')
        .select('*, itens_estudo!inner(id, subgrupo_id, nome, subgrupos!inner(id, grupo_id, nome, grupos!inner(id, nome)))');

      if (itemSel) {
        const itObj = itensDisponiveis.find(i => i.nome === itemSel);
        if (itObj) query = query.eq('item_id', itObj.id);
      } else if (subgrupoSel) {
        const subObj = subgruposDisponiveis.find(s => s.nome === subgrupoSel);
        if (subObj) query = query.eq('itens_estudo.subgrupo_id', subObj.id);
      } else {
        const gObj = gruposDisponiveis.find(g => g.nome === grupoSel);
        if (gObj) query = query.eq('itens_estudo.subgrupos.grupo_id', gObj.id);
      }

      const { data, error } = await query.limit(100);
      if (!error && data) {
        setQuestoes(data);
      }
    } catch (err) {
      console.error('Erro ao filtrar por tema:', err);
    } finally {
      setLoading(false);
    }
  };

  // Função auxiliar para buscar ou criar hierarquia (Grupo -> Subgrupo -> Item)
  const getOrCreateItemId = async (grupo: string, subgrupo: string, itemNome: string): Promise<number> => {
    // 1. Grupo
    let gId: number;
    const { data: gData } = await supabase.from('grupos').select('id').eq('nome', grupo);
    if (gData && gData.length > 0) {
      gId = gData[0].id;
    } else {
      const { data: gNew } = await supabase.from('grupos').insert({ nome: grupo }).select('id').single();
      gId = gNew.id;
    }

    // 2. Subgrupo
    let sId: number;
    const { data: sData } = await supabase.from('subgrupos').select('id').eq('grupo_id', gId).eq('nome', subgrupo);
    if (sData && sData.length > 0) {
      sId = sData[0].id;
    } else {
      const { data: sNew } = await supabase.from('subgrupos').insert({ grupo_id: gId, nome: subgrupo, peso: 1 }).select('id').single();
      sId = sNew.id;
    }

    // 3. Item
    let iId: number;
    const { data: iData } = await supabase.from('itens_estudo').select('id').eq('subgrupo_id', sId).eq('nome', itemNome);
    if (iData && iData.length > 0) {
      iId = iData[0].id;
    } else {
      const { data: iNew } = await supabase.from('itens_estudo').insert({ subgrupo_id: sId, nome: itemNome }).select('id').single();
      iId = iNew.id;
    }

    return iId;
  };

  // 3. Adicionar Nova Questão
  const handleAdicionarQuestao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addEnunciado || !addGabarito || !addGrupoNome || !addSubgrupoNome || !addItemNome) {
      alert('Preencha ao menos Matéria, Tópico, Item, Enunciado e Gabarito!');
      return;
    }

    setSavingAdd(true);
    try {
      const itemId = await getOrCreateItemId(addGrupoNome.trim(), addSubgrupoNome.trim(), addItemNome.trim());

      const novaQuestao = {
        enunciado: addEnunciado.trim(),
        alternativa_a: addAltA.trim() || null,
        alternativa_b: addAltB.trim() || null,
        alternativa_c: addAltC.trim() || null,
        alternativa_d: addAltD.trim() || null,
        alternativa_e: addAltE.trim() || null,
        gabarito: addGabarito.toUpperCase().trim(),
        item_id: itemId,
        banca: addBanca.trim() || 'GERAL',
        ano: parseInt(addAno) || 2024,
        valida: 1
      };

      const { error } = await supabase.from('questoes').insert(novaQuestao);
      if (error) throw error;

      alert('✅ Questão adicionada e validada com sucesso no banco!');
      setAddEnunciado('');
      setAddAltA('');
      setAddAltB('');
      setAddAltC('');
      setAddAltD('');
      setAddAltE('');
    } catch (err: any) {
      console.error('Erro ao adicionar questão:', err);
      alert(`Erro ao adicionar questão: ${err.message}`);
    } finally {
      setSavingAdd(false);
    }
  };

  // 4. Limpeza de Tópicos Genéricos
  const carregarTopicosGenericos = async () => {
    setLoadingLimpeza(true);
    try {
      const { data } = await supabase
        .from('itens_estudo')
        .select('id, nome, subgrupos(nome, grupos(nome))')
        .ilike('nome', '%Tópicos Gerais%');

      setTopicosGenericos(data || []);
    } catch (err) {
      console.error('Erro ao carregar tópicos genéricos:', err);
    } finally {
      setLoadingLimpeza(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'limpeza') {
      carregarTopicosGenericos();
    }
  }, [activeTab]);

  const handleRenomearTopico = async (itemId: number) => {
    const novo = novoNomeMap[itemId]?.trim();
    if (!novo || novo.toLowerCase() === 'tópicos gerais') {
      alert('Digite um nome específico e válido.');
      return;
    }

    try {
      const { error } = await supabase.from('itens_estudo').update({ nome: novo }).eq('id', itemId);
      if (error) throw error;

      alert('Tópico renomeado com sucesso!');
      setTopicosGenericos(topicosGenericos.filter(t => t.id !== itemId));
    } catch (err: any) {
      alert(`Erro ao renomear: ${err.message}`);
    }
  };

  // Salvar Edição de Questão
  const handleSalvarEdicao = async (qId: number) => {
    setSavingEdit(qId);
    try {
      const form = editFormData[qId];
      if (!form) return;

      const updateData = {
        enunciado: form.enunciado,
        alternativa_a: form.alternativa_a || null,
        alternativa_b: form.alternativa_b || null,
        alternativa_c: form.alternativa_c || null,
        alternativa_d: form.alternativa_d || null,
        alternativa_e: form.alternativa_e || null,
        gabarito: form.gabarito?.toUpperCase().trim(),
        banca: form.banca || 'GERAL',
        ano: parseInt(form.ano) || null,
        valida: 1
      };

      const { error } = await supabase.from('questoes').update(updateData).eq('id', qId);
      if (error) throw error;

      setQuestoes(questoes.map(q => q.id === qId ? { ...q, ...updateData } : q));
      alert('Questão atualizada e validada!');
      setExpandedQuestaoId(null);
    } catch (err: any) {
      alert(`Erro ao salvar: ${err.message}`);
    } finally {
      setSavingEdit(null);
    }
  };

  // Invalidar / Remover Questão
  const handleInvalidarQuestao = async (qId: number) => {
    if (!confirm('Deseja marcar esta questão como Removida (-1)?')) return;
    try {
      await supabase.from('questoes').update({ valida: -1 }).eq('id', qId);
      setQuestoes(questoes.filter(q => q.id !== qId));
      alert('Questão invalidada/removida com sucesso.');
    } catch (err: any) {
      alert(`Erro ao remover: ${err.message}`);
    }
  };

  if (!isAdmin) {
    return (
      <div style={{ textAlign: 'center', padding: '60px' }}>
        <h2 style={{ color: '#ef4444' }}>Acesso Restrito</h2>
        <p style={{ color: 'var(--cor-texto-muted)', marginTop: '8px' }}>
          Este módulo está disponível apenas para a conta de administração do sistema.
        </p>
      </div>
    );
  }

  return (
    <div style={{ paddingBottom: '40px' }}>
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.6rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FolderKanban size={26} color="var(--cor-primaria)" /> Gerenciador de Questões 🛠️
        </h1>
        <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.9rem' }}>
          Busque questões por tema ou por palavra-chave para editar o gabarito, o enunciado ou removê-las do banco.
        </p>
      </div>

      {/* Tabs de Navegação */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <button
          onClick={() => setActiveTab('busca')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 18px',
            borderRadius: '10px',
            background: activeTab === 'busca' ? 'rgba(6, 240, 168, 0.15)' : 'rgba(0,0,0,0.3)',
            border: activeTab === 'busca' ? '1px solid var(--cor-secundaria)' : '1px solid rgba(255,255,255,0.08)',
            color: activeTab === 'busca' ? 'var(--cor-secundaria)' : '#fff',
            fontWeight: 700,
            fontSize: '0.85rem',
            cursor: 'pointer'
          }}
        >
          <Search size={16} /> Busca por Texto
        </button>

        <button
          onClick={() => setActiveTab('tema')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 18px',
            borderRadius: '10px',
            background: activeTab === 'tema' ? 'rgba(6, 240, 168, 0.15)' : 'rgba(0,0,0,0.3)',
            border: activeTab === 'tema' ? '1px solid var(--cor-secundaria)' : '1px solid rgba(255,255,255,0.08)',
            color: activeTab === 'tema' ? 'var(--cor-secundaria)' : '#fff',
            fontWeight: 700,
            fontSize: '0.85rem',
            cursor: 'pointer'
          }}
        >
          <Filter size={16} /> Filtro por Tema
        </button>

        <button
          onClick={() => setActiveTab('add')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 18px',
            borderRadius: '10px',
            background: activeTab === 'add' ? 'rgba(255, 107, 0, 0.15)' : 'rgba(0,0,0,0.3)',
            border: activeTab === 'add' ? '1px solid var(--cor-primaria)' : '1px solid rgba(255,255,255,0.08)',
            color: activeTab === 'add' ? 'var(--cor-primaria)' : '#fff',
            fontWeight: 700,
            fontSize: '0.85rem',
            cursor: 'pointer'
          }}
        >
          <Plus size={16} /> Adicionar Questão
        </button>

        <button
          onClick={() => setActiveTab('limpeza')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 18px',
            borderRadius: '10px',
            background: activeTab === 'limpeza' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(0,0,0,0.3)',
            border: activeTab === 'limpeza' ? '1px solid #a855f7' : '1px solid rgba(255,255,255,0.08)',
            color: activeTab === 'limpeza' ? '#c084fc' : '#fff',
            fontWeight: 700,
            fontSize: '0.85rem',
            cursor: 'pointer'
          }}
        >
          <Sparkles size={16} /> Limpeza de Tópicos
        </button>
      </div>

      {/* ABA 1: BUSCA POR TEXTO */}
      {activeTab === 'busca' && (
        <div className="glass-card" style={{ padding: '24px', marginBottom: '28px' }}>
          <form onSubmit={handleBuscaPorTexto} style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              value={termoBusca}
              onChange={e => setTermoBusca(e.target.value)}
              placeholder="Digite um trecho da questão ou palavra-chave..."
              style={{
                flex: 1,
                padding: '12px 16px',
                borderRadius: '8px',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--cor-borda)',
                color: '#fff',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
            <button
              type="submit"
              disabled={loading}
              className="btn-sovereign btn-primary"
              style={{ padding: '12px 24px' }}
            >
              <Search size={18} /> {loading ? 'Buscando...' : 'Buscar por Texto'}
            </button>
          </form>
        </div>
      )}

      {/* ABA 2: FILTRO POR TEMA */}
      {activeTab === 'tema' && (
        <div className="glass-card" style={{ padding: '24px', marginBottom: '28px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '18px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--cor-texto-muted)', marginBottom: '6px' }}>
                Selecione o Grupo (Matéria):
              </label>
              <select
                value={grupoSel}
                onChange={e => setGrupoSel(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff', outline: 'none' }}
              >
                <option value="">Selecione...</option>
                {gruposDisponiveis.map(g => (
                  <option key={g.id} value={g.nome}>{g.nome}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--cor-texto-muted)', marginBottom: '6px' }}>
                Selecione o Subgrupo (Tópico):
              </label>
              <select
                value={subgrupoSel}
                onChange={e => setSubgrupoSel(e.target.value)}
                disabled={!grupoSel}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff', outline: 'none' }}
              >
                <option value="">Todos os subgrupos</option>
                {subgruposDisponiveis.map(s => (
                  <option key={s.id} value={s.nome}>{s.nome}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--cor-texto-muted)', marginBottom: '6px' }}>
                Item de Estudo (Assunto):
              </label>
              <select
                value={itemSel}
                onChange={e => setItemSel(e.target.value)}
                disabled={!subgrupoSel}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff', outline: 'none' }}
              >
                <option value="">Todo o subgrupo</option>
                {itensDisponiveis.map(i => (
                  <option key={i.id} value={i.nome}>{i.nome}</option>
                ))}
              </select>
            </div>
          </div>

          <button
            type="button"
            onClick={handleBuscaPorTema}
            disabled={loading || !grupoSel}
            className="btn-sovereign btn-primary"
            style={{ padding: '10px 22px' }}
          >
            <Filter size={18} /> {loading ? 'Carregando...' : 'Buscar por Tema'}
          </button>
        </div>
      )}

      {/* ABA 3: ADICIONAR QUESTÃO */}
      {activeTab === 'add' && (
        <div className="glass-card" style={{ padding: '24px', marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Plus size={20} color="var(--cor-primaria)" /> Adicionar Nova Questão Manualmente
          </h3>

          <form onSubmit={handleAdicionarQuestao}>
            {/* Hierarquia de Matéria / Subgrupo / Item */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '20px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)' }}>Matéria (Grupo):</label>
                  <label style={{ fontSize: '0.75rem', color: 'var(--cor-secundaria)', cursor: 'pointer' }}>
                    <input type="checkbox" checked={addNovaMateria} onChange={e => setAddNovaMateria(e.target.checked)} style={{ marginRight: '4px' }} />
                    ➕ Nova
                  </label>
                </div>
                {addNovaMateria ? (
                  <input
                    type="text"
                    placeholder="Digite nova matéria..."
                    value={addGrupoNome}
                    onChange={e => setAddGrupoNome(e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#0d1527', border: '1px solid var(--cor-secundaria)', color: '#fff' }}
                  />
                ) : (
                  <select
                    value={addGrupoNome}
                    onChange={e => setAddGrupoNome(e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff' }}
                  >
                    <option value="">Selecione...</option>
                    {gruposDisponiveis.map(g => <option key={g.id} value={g.nome}>{g.nome}</option>)}
                  </select>
                )}
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)' }}>Tópico (Subgrupo):</label>
                  <label style={{ fontSize: '0.75rem', color: 'var(--cor-secundaria)', cursor: 'pointer' }}>
                    <input type="checkbox" checked={addNovoSubgrupo} onChange={e => setAddNovoSubgrupo(e.target.checked)} style={{ marginRight: '4px' }} />
                    ➕ Novo
                  </label>
                </div>
                <input
                  type="text"
                  placeholder="Nome do subgrupo / tópico..."
                  value={addSubgrupoNome}
                  onChange={e => setAddSubgrupoNome(e.target.value)}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff' }}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)' }}>Item de Estudo:</label>
                  <label style={{ fontSize: '0.75rem', color: 'var(--cor-secundaria)', cursor: 'pointer' }}>
                    <input type="checkbox" checked={addNovoItem} onChange={e => setAddNovoItem(e.target.checked)} style={{ marginRight: '4px' }} />
                    ➕ Novo
                  </label>
                </div>
                <input
                  type="text"
                  placeholder="Nome do item exato..."
                  value={addItemNome}
                  onChange={e => setAddItemNome(e.target.value)}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff' }}
                />
              </div>
            </div>

            {/* Enunciado */}
            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--cor-texto-muted)', marginBottom: '6px' }}>Enunciado da Questão:</label>
              <textarea
                rows={4}
                value={addEnunciado}
                onChange={e => setAddEnunciado(e.target.value)}
                placeholder="Cole aqui o texto completo do enunciado da questão..."
                style={{ width: '100%', padding: '12px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--cor-borda)', color: '#fff', fontSize: '0.9rem' }}
              />
            </div>

            {/* Alternativas */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '14px', marginBottom: '18px' }}>
              <input type="text" placeholder="Alternativa A" value={addAltA} onChange={e => setAddAltA(e.target.value)} style={{ padding: '10px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--cor-borda)', color: '#fff' }} />
              <input type="text" placeholder="Alternativa B" value={addAltB} onChange={e => setAddAltB(e.target.value)} style={{ padding: '10px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--cor-borda)', color: '#fff' }} />
              <input type="text" placeholder="Alternativa C" value={addAltC} onChange={e => setAddAltC(e.target.value)} style={{ padding: '10px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--cor-borda)', color: '#fff' }} />
              <input type="text" placeholder="Alternativa D" value={addAltD} onChange={e => setAddAltD(e.target.value)} style={{ padding: '10px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--cor-borda)', color: '#fff' }} />
              <input type="text" placeholder="Alternativa E" value={addAltE} onChange={e => setAddAltE(e.target.value)} style={{ padding: '10px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--cor-borda)', color: '#fff' }} />
              
              <div style={{ display: 'flex', gap: '10px' }}>
                <input type="text" placeholder="Gabarito (A-E ou C/E)" value={addGabarito} onChange={e => setAddGabarito(e.target.value)} style={{ flex: 1, padding: '10px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--cor-secundaria)', color: 'var(--cor-secundaria)', fontWeight: 800, textAlign: 'center' }} />
                <input type="text" placeholder="Banca (ex: FGV)" value={addBanca} onChange={e => setAddBanca(e.target.value)} style={{ flex: 1, padding: '10px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--cor-borda)', color: '#fff' }} />
                <input type="number" placeholder="Ano" value={addAno} onChange={e => setAddAno(e.target.value)} style={{ width: '80px', padding: '10px', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--cor-borda)', color: '#fff' }} />
              </div>
            </div>

            <button
              type="submit"
              disabled={savingAdd}
              className="btn-sovereign btn-primary"
              style={{ padding: '12px 28px' }}
            >
              {savingAdd ? 'Salvando no Banco...' : '✅ Adicionar Questão ao Banco'}
            </button>
          </form>
        </div>
      )}

      {/* ABA 4: LIMPEZA DE TÓPICOS GENÉRICOS */}
      {activeTab === 'limpeza' && (
        <div className="glass-card" style={{ padding: '24px', marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={20} color="#a855f7" /> Renomear Tópicos Genéricos
          </h3>
          <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.85rem', marginBottom: '18px' }}>
            Abaixo estão listados todos os itens chamados 'Tópicos Gerais'. Renomeie-os para assuntos específicos do seu edital.
          </p>

          {loadingLimpeza ? (
            <p style={{ color: 'var(--cor-texto-muted)' }}>Buscando tópicos genéricos...</p>
          ) : topicosGenericos.length === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', background: 'rgba(6, 240, 168, 0.05)', borderRadius: '10px', border: '1px solid rgba(6, 240, 168, 0.2)' }}>
              <span style={{ color: 'var(--cor-secundaria)', fontWeight: 700 }}>🎉 Nenhum tópico genérico encontrado! O banco está 100% organizado.</span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {topicosGenericos.map(tg => (
                <div
                  key={tg.id}
                  style={{
                    padding: '14px 18px',
                    borderRadius: '10px',
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '12px'
                  }}
                >
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--cor-secundaria)', fontWeight: 700 }}>
                      {tg.subgrupos?.grupos?.nome || 'Geral'} ➔ {tg.subgrupos?.nome || 'Geral'} (ID: #{tg.id})
                    </span>
                    <p style={{ fontWeight: 600, fontSize: '0.9rem', marginTop: '2px' }}>{tg.nome}</p>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <input
                      type="text"
                      placeholder="Digite o assunto exato..."
                      value={novoNomeMap[tg.id] || ''}
                      onChange={e => setNovoNomeMap({ ...novoNomeMap, [tg.id]: e.target.value })}
                      style={{ padding: '8px 12px', borderRadius: '6px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff', fontSize: '0.85rem' }}
                    />
                    <button
                      type="button"
                      onClick={() => handleRenomearTopico(tg.id)}
                      className="btn-sovereign btn-primary"
                      style={{ padding: '8px 14px', fontSize: '0.8rem' }}
                    >
                      Renomear
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* LISTA DE QUESTÕES ENCONTRADAS (NAS ABAS DE BUSCA OU TEMA) */}
      {(activeTab === 'busca' || activeTab === 'tema') && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>Questões Encontradas ({questoes.length})</span>
            {questoes.length > 0 && <span style={{ fontSize: '0.8rem', color: 'var(--cor-texto-muted)' }}>Exibindo até 100 resultados</span>}
          </h3>

          {questoes.length === 0 ? (
            <p style={{ color: 'var(--cor-texto-muted)', fontSize: '0.85rem' }}>
              Nenhuma questão carregada. Realize uma busca por texto ou escolha um tema acima.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {questoes.map(q => {
                const isExpanded = expandedQuestaoId === q.id;
                const form = editFormData[q.id] || q;

                return (
                  <div
                    key={q.id}
                    style={{
                      borderRadius: '10px',
                      background: 'rgba(0, 0, 0, 0.25)',
                      border: isExpanded ? '1px solid var(--cor-primaria)' : '1px solid rgba(255, 255, 255, 0.05)',
                      overflow: 'hidden'
                    }}
                  >
                    {/* Header do Accordion */}
                    <div
                      onClick={() => {
                        if (isExpanded) {
                          setExpandedQuestaoId(null);
                        } else {
                          setExpandedQuestaoId(q.id);
                          setEditFormData({ ...editFormData, [q.id]: { ...q } });
                        }
                      }}
                      style={{
                        padding: '16px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '12px'
                      }}
                    >
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 800,
                            background: q.valida === 1 ? 'rgba(6, 240, 168, 0.15)' : q.valida === -1 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(234, 179, 8, 0.15)',
                            color: q.valida === 1 ? 'var(--cor-secundaria)' : q.valida === -1 ? '#ef4444' : '#eab308'
                          }}>
                            {q.valida === 1 ? '🟢 Válida' : q.valida === -1 ? '🔴 Removida' : '⚪ Não Validada'}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--cor-texto-muted)' }}>
                            [Q#{q.id}] {q.banca || 'GERAL'} • {q.ano || '2024'}
                          </span>
                        </div>
                        <p style={{ fontSize: '0.9rem', lineHeight: 1.4, margin: 0 }}>
                          {q.enunciado ? q.enunciado.slice(0, 120) + (q.enunciado.length > 120 ? '...' : '') : 'Sem enunciado'}
                        </p>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: '6px',
                          background: 'rgba(6, 240, 168, 0.15)',
                          color: 'var(--cor-secundaria)',
                          fontSize: '0.8rem',
                          fontWeight: 800
                        }}>
                          Gabarito: {q.gabarito}
                        </span>
                        {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                      </div>
                    </div>

                    {/* Formulário Expandido para Edição e Validação */}
                    {isExpanded && (
                      <div style={{ padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.06)', background: 'rgba(0,0,0,0.4)' }}>
                        <div style={{ marginBottom: '14px' }}>
                          <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--cor-texto-muted)', marginBottom: '4px' }}>Enunciado:</label>
                          <textarea
                            rows={4}
                            value={form.enunciado || ''}
                            onChange={e => setEditFormData({
                              ...editFormData,
                              [q.id]: { ...form, enunciado: e.target.value }
                            })}
                            style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff', fontSize: '0.85rem' }}
                          />
                        </div>

                        {/* Alternativas */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px', marginBottom: '14px' }}>
                          <input type="text" placeholder="Alternativa A" value={form.alternativa_a || ''} onChange={e => setEditFormData({ ...editFormData, [q.id]: { ...form, alternativa_a: e.target.value } })} style={{ padding: '8px 12px', borderRadius: '6px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff', fontSize: '0.85rem' }} />
                          <input type="text" placeholder="Alternativa B" value={form.alternativa_b || ''} onChange={e => setEditFormData({ ...editFormData, [q.id]: { ...form, alternativa_b: e.target.value } })} style={{ padding: '8px 12px', borderRadius: '6px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff', fontSize: '0.85rem' }} />
                          <input type="text" placeholder="Alternativa C" value={form.alternativa_c || ''} onChange={e => setEditFormData({ ...editFormData, [q.id]: { ...form, alternativa_c: e.target.value } })} style={{ padding: '8px 12px', borderRadius: '6px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff', fontSize: '0.85rem' }} />
                          <input type="text" placeholder="Alternativa D" value={form.alternativa_d || ''} onChange={e => setEditFormData({ ...editFormData, [q.id]: { ...form, alternativa_d: e.target.value } })} style={{ padding: '8px 12px', borderRadius: '6px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff', fontSize: '0.85rem' }} />
                          <input type="text" placeholder="Alternativa E" value={form.alternativa_e || ''} onChange={e => setEditFormData({ ...editFormData, [q.id]: { ...form, alternativa_e: e.target.value } })} style={{ padding: '8px 12px', borderRadius: '6px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff', fontSize: '0.85rem' }} />
                          
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <input type="text" placeholder="Gabarito" value={form.gabarito || ''} onChange={e => setEditFormData({ ...editFormData, [q.id]: { ...form, gabarito: e.target.value } })} style={{ flex: 1, padding: '8px', borderRadius: '6px', background: '#0d1527', border: '1px solid var(--cor-secundaria)', color: 'var(--cor-secundaria)', fontWeight: 800, textAlign: 'center' }} />
                            <input type="text" placeholder="Banca" value={form.banca || ''} onChange={e => setEditFormData({ ...editFormData, [q.id]: { ...form, banca: e.target.value } })} style={{ flex: 1, padding: '8px', borderRadius: '6px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff' }} />
                            <input type="number" placeholder="Ano" value={form.ano || ''} onChange={e => setEditFormData({ ...editFormData, [q.id]: { ...form, ano: e.target.value } })} style={{ width: '70px', padding: '8px', borderRadius: '6px', background: '#0d1527', border: '1px solid var(--cor-borda)', color: '#fff' }} />
                          </div>
                        </div>

                        {/* Botões de Ação */}
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
                          <button
                            type="button"
                            onClick={() => handleInvalidarQuestao(q.id)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px',
                              padding: '8px 14px',
                              borderRadius: '6px',
                              background: 'rgba(239, 68, 68, 0.15)',
                              border: '1px solid rgba(239, 68, 68, 0.4)',
                              color: '#ef4444',
                              fontSize: '0.8rem',
                              fontWeight: 700,
                              cursor: 'pointer'
                            }}
                          >
                            <Trash2 size={15} /> Invalidar Questão
                          </button>

                          <button
                            type="button"
                            disabled={savingEdit === q.id}
                            onClick={() => handleSalvarEdicao(q.id)}
                            className="btn-sovereign btn-primary"
                            style={{ padding: '8px 18px', fontSize: '0.8rem' }}
                          >
                            <Save size={15} /> {savingEdit === q.id ? 'Salvando...' : 'Salvar Edições e Validar'}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
