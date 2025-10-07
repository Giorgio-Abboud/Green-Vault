import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Link, Navigate } from "react-router-dom";
import "./styles.css";

import { AuthProvider } from "./auth";
import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Calculate from "./pages/Calculate";
import Home from "./pages/Home";

function AppShell(){
  return (
    <div>
      <h1>Green Vault UI</h1>
      <nav style={{ display:"flex", gap:12, marginBottom:16 }}>
        <Link to="/">Home</Link>
        <Link to="/signup">Sign up</Link>
        <Link to="/login">Log in</Link>
        <Link to="/calculate">Calculate</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/calculate" element={<Calculate />} />
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
