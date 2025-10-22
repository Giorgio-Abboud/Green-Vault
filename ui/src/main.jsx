import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from "react-router-dom";
import "./index.css";

import { AuthProvider, useAuth } from "./auth";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Calculate from "./pages/Calculate";
import Home from "./pages/Home";
import EditProfile from "./pages/EditProfile";

// Simple route guard
function RequireAuth({ children }) {
  const { user } = useAuth();
  const loc = useLocation();
  if (!user) {
    return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  }
  return children;
}

function AppShell() {
  const { user } = useAuth();

  const linkBase =
    "px-3 py-1.5 rounded-md text-sm font-medium transition outline-none focus:ring-2 focus:ring-brand-accent/70";
  const linkIdle =
    "text-gray-300 hover:text-white hover:bg-brand-card/60 border border-transparent";
  const linkActive =
    "text-white bg-brand-card border border-brand-border";

  const navLink = ({ to, label, active }) => (
    <Link
      to={to}
      className={`${linkBase} ${active ? linkActive : linkIdle}`}
    >
      {label}
    </Link>
  );

  const location = useLocation();

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
            {navLink({ to: "/", label: "Home", active: location.pathname === "/" })}
            {!user &&
              navLink({
                to: "/signup",
                label: "Sign up",
                active: location.pathname === "/signup",
              })}
            {!user &&
              navLink({
                to: "/login",
                label: "Log in",
                active: location.pathname === "/login",
              })}
            {user &&
              navLink({
                to: "/calculate",
                label: "Calculate",
                active: location.pathname === "/calculate",
              })}
            {user &&
              navLink({
                to: "/edit-profile",
                label: "Edit Profile",
                active: location.pathname === "/edit-profile",
              })}
          </nav>
        </div>
      </header>

      {/* Routes */}
      <main className="mx-auto max-w-5xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route
            path="/signup"
            element={!user ? <Signup /> : <Navigate to="/" replace />}
          />
          <Route
            path="/login"
            element={!user ? <Login /> : <Navigate to="/" replace />}
          />
          <Route
            path="/calculate"
            element={
              <RequireAuth>
                <Calculate />
              </RequireAuth>
            }
          />
          <Route
            path="/edit-profile"
            element={
              <RequireAuth>
                <EditProfile />
              </RequireAuth>
            }
          />
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
