"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api, Organization, User } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  org: Organization | null;
  orgs: Organization[];
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setOrg: (org: Organization) => void;
  refreshOrgs: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [org, setOrgState] = useState<Organization | null>(null);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const refreshOrgs = async () => {
    const list = await api.listOrganizations();
    setOrgs(list);
    if (list.length > 0 && !org) {
      const saved = localStorage.getItem("current_org_id");
      const found = list.find((o) => o.id === saved) || list[0];
      setOrgState(found);
    }
  };

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      setLoading(false);
      if (!pathname?.startsWith("/login") && !pathname?.startsWith("/register")) {
        router.push("/login");
      }
      return;
    }
    api.getMe()
      .then(async (u) => {
        setUser(u);
        await refreshOrgs();
      })
      .catch(() => {
        api.setToken(null);
        router.push("/login");
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const tokens = await api.login(email, password);
    api.setToken(tokens.access_token);
    const u = await api.getMe();
    setUser(u);
    await refreshOrgs();
    router.push("/dashboard");
  };

  const logout = () => {
    api.setToken(null);
    setUser(null);
    setOrgState(null);
    setOrgs([]);
    router.push("/login");
  };

  const setOrg = (o: Organization) => {
    setOrgState(o);
    localStorage.setItem("current_org_id", o.id);
  };

  return (
    <AuthContext.Provider value={{ user, org, orgs, loading, login, logout, setOrg, refreshOrgs }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
