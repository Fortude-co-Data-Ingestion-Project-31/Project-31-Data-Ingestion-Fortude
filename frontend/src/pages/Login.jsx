import React, { useState } from "react";
import Mfa from "./Mfa";

// Login component
// ----------------
// This component renders the sign-in / register form and handles the
// initial authentication request to the backend. If the server responds
// that MFA is required the component stores the temporary MFA token and
// displays the `Mfa` component which will complete the second factor.
//
// Props:
// - `onLogin(username)` called when sign-in completes successfully.

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [mfaStep, setMfaStep] = useState(false);
  const [tmpToken, setTmpToken] = useState(null);
  const [mfaCode, setMfaCode] = useState("");
  const [mfaSetup, setMfaSetup] = useState({ otpauthUrl: null, secret: null });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login";
      const res = await fetch("http://127.0.0.1:8000" + endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.detail || (isRegister ? "Register failed" : "Login failed"));
        return;
      }
      const data = await res.json();
      if (data.mfa_required) {
        setTmpToken(data.tmp_token);
        setMfaSetup({ otpauthUrl: data.otpauth_url || null, secret: data.secret || null });
        setMfaStep(true);
        return;
      }
      const token = data.token;
      if (token) {
        localStorage.setItem("auth_token", token);
      }
      onLogin(data.username);
    } catch (err) {
      setError("Network error");
    }
  };

  const cancelMfa = () => {
    setMfaStep(false);
    setTmpToken(null);
    setMfaCode("");
    setMfaSetup({ otpauthUrl: null, secret: null });
    setError("");
  };

  const handleMfaVerified = (username) => {
    setMfaStep(false);
    setTmpToken(null);
    setMfaCode("");
    setMfaSetup({ otpauthUrl: null, secret: null });
    onLogin(username);
  };

  if (mfaStep) {
    return <Mfa tmpToken={tmpToken} onVerified={handleMfaVerified} onCancel={cancelMfa} otpauthUrl={mfaSetup.otpauthUrl} secret={mfaSetup.secret} />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "#f3f4f6" }}>
      <form onSubmit={submit} className="bg-white p-6 rounded shadow-md w-96">
        <h2 className="text-xl mb-4">{isRegister ? "Create account" : "Sign in"}</h2>
        {error ? <div className="text-red-600 mb-2">{error}</div> : null}
        <label className="block mb-2">Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} className="w-full mb-3 p-2 border rounded" />
        <label className="block mb-2">Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full mb-4 p-2 border rounded" />
        <button className="w-full bg-blue-600 text-white p-2 rounded">{isRegister ? "Register" : "Sign in"}</button>
        <div className="mt-3 text-center text-sm">
          <button type="button" onClick={() => setIsRegister((s) => !s)} className="text-blue-600 underline">
            {isRegister ? "Have an account? Sign in" : "Create account"}
          </button>
        </div>
      </form>
    </div>
  );
}
