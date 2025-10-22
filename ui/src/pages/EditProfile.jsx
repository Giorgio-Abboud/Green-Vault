import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiPut } from "../api";
import { useAuth } from "../auth";

export default function EditProfile() {
  const { user } = useAuth();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [msg, setMsg] = useState("");
  const navigate = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setMsg("");
    setFieldErrors({});
    try {
      await apiPut("/v1/users/me", {
        old_password: oldPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setMsg("✅ Password updated successfully!");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => navigate("/"), 2000);
    } catch (err) {
      let message = err.message;
      try {
        const json = JSON.parse(message.split(" ", 2)[1]);
        if (json?.field_errors) {
          setFieldErrors(json.field_errors);
          setMsg("");
          return;
        }
      } catch {}
      setMsg(`❌ ${message}`);
    }
  }

  const baseInput =
    "w-full rounded-lg bg-brand-card/60 border border-brand-border px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-accent/70 focus:border-brand-accent/60 transition";
  const errorInput =
    "w-full rounded-lg border-2 px-3 py-2 bg-brand-card/60 text-gray-100 placeholder-gray-400 border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/60";
  const labelCls = "text-sm text-gray-300";
  const btnPrimary =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-brand-accent text-black hover:brightness-110 transition shadow-soft";
  const btnGhost =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-brand-card/60 text-gray-200 border border-brand-border hover:border-brand-accent/50 transition";

  const inputClass = (field) => (fieldErrors[field] ? errorInput : baseInput);
  const isOk = msg.startsWith("✅");
  const isErr = msg.startsWith("❌");

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <div className="mx-auto max-w-3xl px-4 py-10">
        <h2 className="mb-6 text-2xl font-semibold tracking-tight">Edit Profile</h2>

        <div className="mb-6 rounded-xl2 border border-brand-border bg-brand-card p-5 shadow-soft">
          {user ? (
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <p><strong>Email:</strong> {user.email}</p>
              <p><strong>Name:</strong> {user.name || "(none)"}</p>
              <p><strong>Last name:</strong> {user.last_name || "(none)"}</p>
            </div>
          ) : (
            <p>Loading user info...</p>
          )}
        </div>

        <div className="rounded-xl2 border border-brand-border bg-brand-card p-6 shadow-soft">
          <h3 className="mb-4 text-lg font-medium">Change Password</h3>
          <form onSubmit={submit} className="space-y-4 max-w-md">
            <div>
              <label className={labelCls}>Current password</label>
              <input type="password" placeholder="Current password" value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className={inputClass("old_password")} />
              {fieldErrors.old_password && (
                <div className="mt-1 text-xs text-red-400">Old password field does not match current password</div>
              )}
            </div>

            <div>
              <label className={labelCls}>New password</label>
              <input type="password" placeholder="New password" value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className={inputClass("new_password")} />
              {fieldErrors.new_password && (
                <div className="mt-1 text-xs text-red-400">Must meet requirements (uppercase, lowercase, digit, symbol, ≥12 chars)</div>
              )}
            </div>

            <div>
              <label className={labelCls}>Confirm new password</label>
              <input type="password" placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={inputClass("confirm_password")} />
              {fieldErrors.confirm_password && (
                <div className="mt-1 text-xs text-red-400">The new password must match the confirmation</div>
              )}
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button type="submit" className={btnPrimary}>Save</button>
              <button type="button" onClick={() => navigate("/")} className={btnGhost}>← Back</button>
            </div>
          </form>

          {msg && (
            <div
              className={[
                "mt-4 rounded-lg border px-4 py-3 text-sm",
                isOk
                  ? "border-emerald-600/40 bg-emerald-500/10 text-emerald-300"
                  : isErr
                  ? "border-red-600/40 bg-red-500/10 text-red-300"
                  : "border-brand-border bg-brand-card/80 text-gray-300",
              ].join(" ")}
            >
              {msg}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
