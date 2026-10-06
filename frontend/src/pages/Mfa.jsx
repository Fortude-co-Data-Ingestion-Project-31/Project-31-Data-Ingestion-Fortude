import React, { useState } from "react";

// Mfa component
// -------------
// This component renders the second-factor verification UI. It expects
// a short-lived `tmpToken` (provided by the login endpoint) and a
// callback `onVerified(username)` to notify the parent when MFA has
// succeeded. The component submits the user-provided TOTP `code` to
// `/api/auth/mfa/login` which will exchange the temporary token for a
// session token on success.
//
// Props:
// - `tmpToken`: temporary MFA token obtained from `/api/auth/login`
// - `onVerified(username)`: callback when MFA verification completes
// - `onCancel()`: cancel MFA and return to login screen
// - `otpauthUrl` / `secret`: left available for setup flows but not
//   displayed in the simplified UI (we now expect users to already have
//   an authenticator app enrolled before MFA is toggled on).
export default function Mfa({ tmpToken, onVerified, onCancel, otpauthUrl, secret }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/auth/mfa/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tmp_token: tmpToken, code }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.detail || "MFA verification failed");
        return;
      }

      const data = await res.json();
      if (data.token) {
        localStorage.setItem("auth_token", data.token);
      }
      onVerified(data.username);
    } catch (err) {
      setError("Network error");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "#f3f4f6" }}>
      <form onSubmit={submit} className="bg-white p-6 rounded shadow-md w-96">
        <h2 className="text-xl mb-4">Enter MFA code</h2>
        {error ? <div className="text-red-600 mb-2">{error}</div> : null}
        {/* Removed QR and secret display: only accept authentication code now */}
        <label className="block mb-2">Authentication code</label>
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className="w-full mb-4 p-2 border rounded"
          placeholder="123456"
        />
        <button className="w-full bg-blue-600 text-white p-2 rounded">Verify</button>
        <div className="mt-3 text-center text-sm">
          <button type="button" onClick={onCancel} className="text-blue-600 underline">
            Back to login
          </button>
        </div>
      </form>
    </div>
  );
}
