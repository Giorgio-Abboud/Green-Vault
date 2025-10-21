import React, { createContext, useContext, useEffect, useState } from "react";
import { apiGet } from "./api";

const AuthCtx = createContext({ user: null, setUser: () => {}, refresh: async () => {} });

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  async function refresh() {
    try {
      const me = await apiGet("/v1/me");
      setUser(me);
    } catch {
      setUser(null);
    }
  }

  useEffect(() => { refresh(); }, []);

  return (
    <AuthCtx.Provider value={{ user, setUser, refresh }}>
      {children}
    </AuthCtx.Provider>
  );
}

export function useAuth() { return useContext(AuthCtx); }
