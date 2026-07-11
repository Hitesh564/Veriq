"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { User, Session } from "@supabase/supabase-js";
import { supabase } from "../utils/supabaseClient";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  showAuthModal: boolean;
  setShowAuthModal: (show: boolean) => void;
  loginCallback: (() => void) | null;
  setLoginCallback: (callback: (() => void) | null) => void;
  triggerAuthGuard: (onSuccess: () => void) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [loginCallback, setLoginCallback] = useState<(() => void) | null>(null);

  useEffect(() => {
    // 1. Check for initial session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // 2. Listen to active auth session state updates
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
      
      // If user logs in and there is a pending configuration callback, trigger it!
      if (session?.user && loginCallback) {
        loginCallback();
        setLoginCallback(null);
        setShowAuthModal(false);
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [loginCallback]);

  // Enforces auth for action triggers, saving the callback to run immediately upon login success
  const triggerAuthGuard = (onSuccess: () => void) => {
    if (user) {
      onSuccess();
    } else {
      setLoginCallback(() => onSuccess);
      setShowAuthModal(true);
    }
  };

  const logout = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        showAuthModal,
        setShowAuthModal,
        loginCallback,
        setLoginCallback,
        triggerAuthGuard,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
