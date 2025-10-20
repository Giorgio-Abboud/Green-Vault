import React from "react";
import { useAuth } from "../auth";
import { apiPost } from "../api";
import { Link } from "react-router-dom";

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

  return (
    <div>
      <h2>Home</h2>
      {user ? (
        <>
          <div>Signed in as <strong>{user.name || user.email}</strong></div>
          <div style={{ marginTop: 12, display: "flex", gap: "8px" }}>
            <Link to="/edit-profile">
              <button>Edit Profile</button>
            </Link>
            <button onClick={logout}>Logout</button>
          </div>
        </>
      ) : (
        <div>Not signed in</div>
      )}
    </div>
  );
}
