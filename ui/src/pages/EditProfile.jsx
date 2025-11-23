import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiPut } from "../api";
import { useAuth } from "../auth";

export default function EditProfile() {
  const { user, refresh } = useAuth();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [msg, setMsg] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false); // <-- NEW
  const navigate = useNavigate();

  function parseApiError(err) {
    let status = err?.status ?? err?.response?.status ?? null;
    let data = err?.data ?? err?.response?.data ?? undefined;
    const coerce = (x) => {
      if (!x) return undefined;
      if (typeof x !== "string") return x;
      try { return JSON.parse(x); } catch { return { error: x }; }
    };
    if (data === undefined && (typeof err === "string" || typeof err?.message === "string")) {
      const raw = String(typeof err === "string" ? err : err.message).trim();
      const m = raw.match(/^(\d{3})\s+(.+)$/);
      if (m) { status = Number(m[1]); data = coerce(m[2]); }
      else { data = coerce(raw); }
    } else {
      data = coerce(data);
    }
    return { status, data };
  }

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
      const { status, data } = parseApiError(err);
      if (status === 422 && data && typeof data === "object") {
        const fe = data.field_errors || {};
        setFieldErrors(fe);
        setMsg("❌ The information you entered doesn’t meet the requirements. Please fix the highlighted fields.");
        return;
      }
      if (status === 401 || status === 403) {
        setMsg("❌ The current password is incorrect. Please try again");
        return;
      }
      setMsg(`❌ ${data?.error || err?.message || "Something went wrong"}`);
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
  const btnDanger =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-red-600 text-white hover:brightness-110 transition shadow-soft";

  const inputClass = (field) => (fieldErrors[field] ? errorInput : baseInput);
  const isOk = msg.startsWith("✅");
  const isErr = msg.startsWith("❌");

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <div className="mx-auto max-w-3xl px-4 py-10">
        <h2 className="mb-6 text-2xl font-semibold tracking-tight">Edit Profile</h2>

        {/* USER DETAILS */}
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

        {/* FORM */}
        <div className="rounded-xl2 border border-brand-border bg-brand-card p-6 shadow-soft">
          <h3 className="mb-4 text-lg font-medium">Change Password</h3>

          <form onSubmit={submit} className="space-y-4 max-w-md">
            {/* CURRENT PASSWORD */}
            <div>
              <label className={labelCls}>Current password</label>
              <input
                name="old_password"
                type="password"
                placeholder="Current password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className={inputClass("old_password")}
              />
            </div>

            {/* NEW PASSWORD */}
            <div>
              <label className={labelCls}>New password</label>
              <input
                name="new_password"
                type="password"
                placeholder="New password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className={inputClass("new_password")}
              />
            </div>

            {/* CONFIRM PASSWORD */}
            <div>
              <label className={labelCls}>Confirm new password</label>
              <input
                name="confirm_password"
                type="password"
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={inputClass("confirm_password")}
              />
            </div>

            {/* BUTTONS */}
            <div className="flex items-center gap-3 pt-2">
              <button type="submit" className={btnPrimary}>Save</button>
              <button type="button" onClick={() => navigate("/")} className={btnGhost}>← Back</button>

              {/* DELETE ACCOUNT BUTTON — opens modal */}
              <button
                type="button"
                className={btnDanger}
                onClick={() => setShowDeleteConfirm(true)}
              >
                Delete account
              </button>
            </div>
          </form>

          {/* MESSAGES */}
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

      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="rounded-xl2 bg-brand-card p-6 border border-brand-border shadow-xl max-w-sm w-full space-y-4">
            <h3 className="text-lg font-semibold text-red-400">
              Delete your account?
            </h3>

            <p className="text-gray-300 text-sm">
              You cannot undo this action. All your data will be permanently deleted.
              Are you sure you want to continue?
            </p>

            <div className="flex justify-end gap-3 pt-2">
              <button
                className="px-4 py-2 rounded-lg text-sm bg-gray-600 text-white hover:bg-gray-500 transition"
                onClick={() => setShowDeleteConfirm(false)}
              >
                Cancel
              </button>

              <button
                className="px-4 py-2 rounded-lg text-sm bg-red-600 text-white hover:bg-red-500 transition shadow-soft"
                onClick={async () => {
                  try {
                    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/v1/users/me`, {
                      method: "DELETE",
                      credentials: "include",
                      headers: { "Accept": "application/json" },
                    });

                    if (res.ok) {
                      setMsg("✅ Account deleted successfully");
                      await refresh();
                      navigate("/");
                    } else {
                      const text = await res.text();
                      setMsg(`❌ Failed (HTTP ${res.status}): ${text || res.statusText}`);
                    }
                  } catch (err) {
                    setMsg(`❌ ${err.message || "Delete failed"}`);
                  }

                  setShowDeleteConfirm(false);
                }}
              >
                Delete account
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
