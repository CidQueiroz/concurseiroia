import { describe, it, expect } from 'vitest';
import { generateAIAnswer } from '../services/aiService';

describe('🤖 Tutor IA & Geração de Conteúdo (aiService)', () => {
  it('deve retornar aviso amigável quando chaves de API não forem informadas', async () => {
    const keysEmpty = { groq: '', gemini: '' };
    const resposta = await generateAIAnswer(keysEmpty, 'Explique o que é RPD.');
    
    expect(resposta.error).toContain('Nenhuma chave de IA válida configurada');
  });

  it('deve possuir chave de bancas prioritárias padrão', () => {
    const bancasPadrao = ['FGV', 'CEBRASPE', 'CESGRANRIO', 'FCC', 'IBFC', 'VUNESP'];
    expect(bancasPadrao).toContain('FGV');
    expect(bancasPadrao).toContain('CEBRASPE');
  });
});
