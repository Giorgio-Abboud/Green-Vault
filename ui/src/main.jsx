import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from "react-router-dom";
import "./index.css";

import { AuthProvider } from "./auth";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Calculate from "./pages/Calculate";
import Home from "./pages/Home";

function AppShell() {
  const location = useLocation();

  const navBase =
    "px-3 py-1.5 rounded-md text-sm font-medium transition outline-none focus:ring-2 focus:ring-brand-accent/70";
  const navIdle = "text-gray-300 hover:text-white hover:bg-brand-card/60 border border-transparent";
  const navActive = "text-white bg-brand-card border border-brand-border";

  const linkCls = (path) =>
    `${navBase} ${location.pathname === path ? navActive : navIdle}`;

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-brand-border bg-brand-bg/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-brand-accent" />
            <span className="text-sm font-semibold tracking-wide text-white">
              Green Vault UI
            </span>
          </Link>

          <nav className="flex items-center gap-2">
            <Link to="/" className={linkCls("/")}>Home</Link>
            <Link to="/signup" className={linkCls("/signup")}>Sign up</Link>
            <Link to="/login" className={linkCls("/login")}>Log in</Link>
            <Link to="/calculate" className={linkCls("/calculate")}>Calculate</Link>
          </nav>
        </div>
      </header>

      {/* Page content */}
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/login" element={<Login />} />
          <Route path="/calculate" element={<Calculate />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  </BrowserRouter>
);
