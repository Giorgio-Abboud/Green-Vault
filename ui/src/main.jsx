import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from "react-router-dom";
import "./styles.css";

import { AuthProvider, useAuth } from "./auth";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Calculate from "./pages/Calculate";
import Home from "./pages/Home";

// Simple route guard
function RequireAuth({ children }) {
  const { user } = useAuth();
  const loc = useLocation();
  if (!user) {
    // send them to login, but remember where they wanted to go
    return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  }
  return children;
}

function AppShell(){
  const { user } = useAuth();

  return (
    <div>
      <h1>Green Vault UI</h1>
      <nav style={{ display:"flex", gap:12, marginBottom:16 }}>
        <Link to="/">Home</Link>
        {!user && <Link to="/signup">Sign up</Link>}
        {!user && <Link to="/login">Log in</Link>}
        {user && <Link to="/calculate">Calculate</Link>}
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/signup" element={!user ? <Signup /> : <Navigate to="/" replace />} />
        <Route path="/login"  element={!user ? <Login />  : <Navigate to="/" replace />} />
        <Route
          path="/calculate"
          element={
            <RequireAuth>
              <Calculate />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
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
