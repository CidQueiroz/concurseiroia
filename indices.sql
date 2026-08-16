-- Índice composto para consultas do AMV 2.0 (WHERE user_id = X AND item_id = Y)
CREATE INDEX IF NOT EXISTS idx_aprendizado_user_item ON public.aprendizado_item (user_id, item_id);

-- Índice para ordenação e filtro das revisões diárias
CREATE INDEX IF NOT EXISTS idx_aprendizado_revisao ON public.aprendizado_item (user_id, status, proxima_revisao);

-- Índice para busca rápida no painel de evolução temporal
CREATE INDEX IF NOT EXISTS idx_respostas_user_data ON public.respostas (user_id, data);
