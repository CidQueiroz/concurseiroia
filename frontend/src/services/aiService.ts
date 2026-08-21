export interface AIResponse {
  content: string;
  error?: string;
}

export const callGroq = async (apiKey: string, prompt: string, systemPrompt?: string): Promise<AIResponse> => {
  try {
    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: [
          ...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
          { role: 'user', content: prompt }
        ],
        temperature: 0.2
      })
    });

    if (!res.ok) {
      const err = await res.json();
      return { content: '', error: err.error?.message || `Erro Groq HTTP ${res.status}` };
    }

    const data = await res.json();
    return { content: data.choices?.[0]?.message?.content || '' };
  } catch (err: any) {
    return { content: '', error: err.message || 'Falha na conexão com a API Groq' };
  }
};

export const callGemini = async (apiKey: string, prompt: string, systemPrompt?: string): Promise<AIResponse> => {
  try {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [
          ...(systemPrompt ? [{ role: 'user', parts: [{ text: `[INSTRUÇÃO DO SISTEMA]: ${systemPrompt}` }] }] : []),
          { role: 'user', parts: [{ text: prompt }] }
        ]
      })
    });

    if (!res.ok) {
      const err = await res.json();
      return { content: '', error: err.error?.message || `Erro Gemini HTTP ${res.status}` };
    }

    const data = await res.json();
    const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
    return { content: text };
  } catch (err: any) {
    return { content: '', error: err.message || 'Falha na conexão com a API Gemini' };
  }
};

export const generateAIAnswer = async (
  keys: { groq?: string; gemini?: string },
  prompt: string,
  systemPrompt?: string
): Promise<AIResponse> => {
  if (keys.groq) {
    const r = await callGroq(keys.groq, prompt, systemPrompt);
    if (!r.error) return r;
  }

  if (keys.gemini) {
    const r = await callGemini(keys.gemini, prompt, systemPrompt);
    if (!r.error) return r;
  }

  return { content: '', error: 'Nenhuma chave de IA válida configurada ou erro em todos os provedores.' };
};
