import React, { createContext, useContext, useState, useEffect } from 'react';

interface AIKeys {
  groq: string;
  gemini: string;
}

interface AIContextType {
  keys: AIKeys;
  setGroqKey: (key: string) => void;
  setGeminiKey: (key: string) => void;
  preferredBanca: string;
  setPreferredBanca: (banca: string) => void;
}

const AIContext = createContext<AIContextType>({} as AIContextType);

const STORAGE_KEY = 'aprovateck_ai_config';

export const AIProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [keys, setKeys] = useState<AIKeys>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : { groq: '', gemini: '' };
    } catch {
      return { groq: '', gemini: '' };
    }
  });

  const [preferredBanca, setPreferredBancaState] = useState<string>(() => {
    return localStorage.getItem('aprovateck_preferred_banca') || 'Geral';
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
  }, [keys]);

  const setGroqKey = (groq: string) => {
    setKeys(prev => ({ ...prev, groq }));
  };

  const setGeminiKey = (gemini: string) => {
    setKeys(prev => ({ ...prev, gemini }));
  };

  const setPreferredBanca = (banca: string) => {
    setPreferredBancaState(banca);
    localStorage.setItem('aprovateck_preferred_banca', banca);
  };

  return (
    <AIContext.Provider value={{ keys, setGroqKey, setGeminiKey, preferredBanca, setPreferredBanca }}>
      {children}
    </AIContext.Provider>
  );
};

export const useAI = () => useContext(AIContext);
