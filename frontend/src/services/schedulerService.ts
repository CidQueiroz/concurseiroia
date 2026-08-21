import { supabase } from '../config/supabase';

export interface ItemEstudo {
  item_id: number;
  status: string;
  grupo_nome: string;
  subgrupo_nome: string;
  item_nome: string;
  vezes_estudado: number;
  taxa_acerto: number;
  total_respondidas: number;
  dias_desde_revisao?: number;
  proxima_revisao?: string;
  resumo?: string;
}

export const getPesoGrupo = (_grupoNome?: string): number => {
  return 1.0;
};

export const montarPlanoDiario = async (userId: string): Promise<{ novos: ItemEstudo[]; revisoes: ItemEstudo[] }> => {
  const { data: itens, error } = await supabase
    .from('aprendizado_item')
    .select(`
      *,
      itens_estudo!inner(
        id,
        nome,
        subgrupos!inner(
          nome,
          grupos!inner(
            nome
          )
        )
      )
    `)
    .eq('user_id', userId);

  if (error || !itens) {
    console.error('Erro ao buscar itens de aprendizado:', error);
    return { novos: [], revisoes: [] };
  }

  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);

  const formatado: ItemEstudo[] = itens.map((row: any) => {
    let diasDesde = 0;
    if (row.ultima_revisao) {
      const d = new Date(row.ultima_revisao);
      diasDesde = Math.floor((hoje.getTime() - d.getTime()) / (1000 * 3600 * 24));
    }

    return {
      item_id: row.item_id,
      status: row.status || 'NOVO',
      grupo_nome: row.itens_estudo?.subgrupos?.grupos?.nome || 'Geral',
      subgrupo_nome: row.itens_estudo?.subgrupos?.nome || '',
      item_nome: row.itens_estudo?.nome || '',
      vezes_estudado: row.vezes_estudado || 0,
      taxa_acerto: row.taxa_acerto || 0,
      total_respondidas: row.total_respondidas || 0,
      dias_desde_revisao: diasDesde,
      proxima_revisao: row.proxima_revisao,
      resumo: row.resumo
    };
  });

  // 1. Filtrar Novos
  const novos = formatado.filter(i => i.status === 'NOVO').slice(0, 3);

  // 2. Filtrar Revisões
  const revisoes = formatado.filter(i => {
    if (i.status === 'NOVO') return false;
    if (!i.proxima_revisao) return true;
    const prox = new Date(i.proxima_revisao);
    prox.setHours(0, 0, 0, 0);
    return prox <= hoje;
  });

  return { novos, revisoes };
};

export const processarResposta = async (
  userId: string,
  itemId: number,
  acertou: boolean
) => {
  const { data: rows } = await supabase
    .from('aprendizado_item')
    .select('*')
    .eq('user_id', userId)
    .eq('item_id', itemId);

  if (!rows || rows.length === 0) return;
  const row = rows[0];

  const total = (row.total_respondidas || 0) + 1;
  const acertos = (row.total_acertos || 0) + (acertou ? 1 : 0);
  const taxa = (acertos / total) * 100;
  const vezes = (row.vezes_estudado || 0) + 1;

  let intervaloDias = 1;
  if (acertou) {
    if (vezes === 1) intervaloDias = 1;
    else if (vezes === 2) intervaloDias = 3;
    else if (vezes === 3) intervaloDias = 7;
    else intervaloDias = Math.min(15 * (vezes - 3), 60);
  } else {
    intervaloDias = 1;
  }

  const proxData = new Date();
  proxData.setDate(proxData.getDate() + intervaloDias);

  const status = taxa >= 80 && vezes >= 4 ? 'APRENDIDO' : 'EM_REVISAO';

  await supabase
    .from('aprendizado_item')
    .update({
      total_respondidas: total,
      total_acertos: acertos,
      taxa_acerto: taxa,
      vezes_estudado: vezes,
      status,
      ultima_revisao: new Date().toISOString(),
      proxima_revisao: proxData.toISOString().split('T')[0]
    })
    .eq('user_id', userId)
    .eq('item_id', itemId);
};

export const salvarResumoItem = async (userId: string, itemId: number, resumo: string) => {
  await supabase
    .from('aprendizado_item')
    .update({ resumo })
    .eq('user_id', userId)
    .eq('item_id', itemId);
};
