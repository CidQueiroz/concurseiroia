ALTER TABLE public.questoes 
ADD COLUMN IF NOT EXISTS banca text,
ADD COLUMN IF NOT EXISTS padrao_distrator text,
ADD COLUMN IF NOT EXISTS gatilho_pegadinha jsonb;
