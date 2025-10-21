import React from "react";
import { useAuth } from "../auth";
import { apiPost } from "../api";

export default function Home() {
  const { user, refresh } = useAuth();

  async function logout() {
    try {
      await apiPost("/v1/logout", {});
      await refresh();
    } catch (err) {
      console.error(err);
    }
  }

  const btn =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-brand-accent text-black hover:brightness-110 transition shadow-soft";

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <div className="mx-auto max-w-3xl px-4 py-10">
        <h2 className="text-2xl font-semibold tracking-tight mb-6">Home</h2>

        <div className="rounded-xl2 border border-brand-border bg-brand-card p-6 shadow-soft">
          {user ? (
            <>
              <div className="text-gray-300">
                Signed in as{" "}
                <strong className="text-white">{user.name || user.email}</strong>
              </div>
              <button onClick={logout} className={`${btn} mt-4`}>
                Logout
              </button>
            </>
          ) : (
            <div className="text-gray-300">Not signed in</div>
          )}
        </div>
      </div>
    </div>
  );
}
