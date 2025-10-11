import React from "react";
import { useAuth } from "../auth";
import { apiPost } from "../api";

export default function Home(){
  const { user, refresh } = useAuth();

  async function logout(){
    try{
      await apiPost("/v1/logout", {});
      await refresh();
    }catch(err){
      console.error(err);
    }
  }

  return (
    <div>
      <h2>Home</h2>
      {user ? (
        <>
          <div>Signed in as <strong>{user.name || user.email}</strong></div>
          <button onClick={logout} style={{ marginTop: 8 }}>Logout</button>
        </>
      ) : (
        <div>Not signed in</div>
      )}
    </div>
  );
}
