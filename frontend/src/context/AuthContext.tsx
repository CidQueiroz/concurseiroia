import React, { createContext, useContext, useEffect, useState } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import { supabase } from '../config/supabase';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isAdmin: boolean;
  signIn: (email: string, pass: string) => Promise<{ error: Error | null }>;
  signUp: (email: string, pass: string) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Obter sessão inicial
    supabase.auth.getSession().then(({ data }: any) => {
      const sess = data?.session;
      setSession(sess);
      setUser(sess?.user ?? null);
      setLoading(false);
    });

    // 2. Escutar mudanças de estado de autenticação (sem disparar re-renders falsos ao trocar de aba)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event: any, newSession: any) => {
      setSession(newSession);
      setUser((prevUser: any) => {
        if (prevUser?.id === newSession?.user?.id) {
          return prevUser; // Mantém a mesma referência de objeto se o user_id for o mesmo!
        }
        return newSession?.user ?? null;
      });
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email: string, pass: string) => {
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password: pass
      });
      return { error: error ? new Error(error.message) : null };
    } catch (err: any) {
      return { error: new Error(err.message || 'Erro inesperado ao realizar login') };
    }
  };

  const signUp = async (email: string, pass: string) => {
    try {
      const redirectUrl = window.location.origin || 'https://aprovateck.cdkteck.com.br';
      const { error } = await supabase.auth.signUp({
        email,
        password: pass,
        options: {
          emailRedirectTo: `${redirectUrl}/`
        }
      });
      return { error: error ? new Error(error.message) : null };
    } catch (err: any) {
      return { error: new Error(err.message || 'Erro inesperado ao criar conta') };
    }
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
  };

  const isAdmin = user?.email === 'cydy.potter@gmail.com';

  return (
    <AuthContext.Provider value={{ user, session, loading, isAdmin, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
