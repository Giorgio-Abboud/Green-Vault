import React from "react";
import { useAuth } from "../auth";

export default function Home(){
  const { user } = useAuth();
  return (
    <div>
      <h2>Home</h2>
      <div>{user ? `Signed in as ${user.email}` : "Not signed in"}</div>
    </div>
  );
}
