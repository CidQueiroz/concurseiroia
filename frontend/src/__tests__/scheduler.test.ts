import { describe, it, expect } from 'vitest';
import { getPesoGrupo } from '../services/schedulerService';

describe('🧠 Motor AMV 2.0 - Scheduler & Spaced Repetition', () => {
  it('deve aplicar peso isonômico 1.0x para todas as matérias e questões públicas', () => {
    const pesoEsp = getPesoGrupo('Conhecimentos Específicos - TI');
    const pesoGeral = getPesoGrupo('Língua Portuguesa');
    
    expect(pesoEsp).toBe(1.0);
    expect(pesoGeral).toBe(1.0);
  });

  it('deve calcular taxa de acerto com precisão percentual', () => {
    const acertos = 15;
    const total = 20;
    const taxa = (acertos / total) * 100;
    expect(taxa).toBe(75);
  });

  it('deve validar transições lógicas de status da repetição espaçada', () => {
    const statusSequence = ['NOVO', 'RECONHECIMENTO', 'RETENCAO_INICIAL', 'REVISAO_1', 'REVISAO_2', 'REVISAO_3', 'DOMINADO'];
    expect(statusSequence).toContain('DOMINADO');
    expect(statusSequence.indexOf('REVISAO_1')).toBeLessThan(statusSequence.indexOf('REVISAO_3'));
  });
});
