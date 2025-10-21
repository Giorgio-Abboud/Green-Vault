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
      const res = await apiPut("/v1/users/me", {
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
      // fallback if parsing fails
      setMsg(`❌ ${message}`);
    }
  }

  // Helper to get border color
  const inputClass = (field) =>
    fieldErrors[field] ? "error" : "";

  return (
    <div>
      <h2>Edit Profile</h2>

      {user ? (
        <div className="banner" style={{ marginBottom: "16px" }}>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Name:</strong> {user.name || "(none)"}</p>
          <p><strong>Last name:</strong> {user.last_name || "(none)"}</p>
        </div>
      ) : (
        <p>Loading user info...</p>
      )}

      <h3>Change Password</h3>
      <form
        onSubmit={submit}
        className="form"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          maxWidth: "320px",
        }}
      >
        <div className="form-group">
          <input
            type="password"
            placeholder="Current password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            className={inputClass("old_password")}
          />
          {fieldErrors.old_password && (
            <span className="field-error">
              Old password field does not match current password
            </span>
          )}
        </div>

        <div className="form-group">
          <input
            type="password"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className={inputClass("new_password")}
          />
          {fieldErrors.new_password && (
            <span className="field-error">
              Must meet requirements (uppercase, lowercase, digit, symbol, ≥12 chars)
            </span>
          )}
        </div>

        <div className="form-group">
          <input
            type="password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className={inputClass("confirm_password")}
          />
          {fieldErrors.confirm_password && (
            <span className="field-error">
              The new password must match the confirmation
            </span>
          )}
        </div>

        <button type="submit">Save</button>
      </form>

      {msg && (
        <div
          className={`banner ${msg.startsWith("✅") ? "success" : "error"}`}
          style={{ marginTop: 10 }}
        >
          {msg}
        </div>
      )}

      <button
        style={{
          marginTop: 20,
          backgroundColor: "#94a3b8",
          border: "none",
          borderRadius: "4px",
          padding: "6px 10px",
          cursor: "pointer",
        }}
        onClick={() => navigate("/")}
      >
        ← Back
      </button>
    </div>
  );
}
