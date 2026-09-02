import React, { useState } from "react";

export default function Settings({ token, currentUser, onSaved, goTo }) {
  const [newPassword, setNewPassword] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [message, setMessage] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);
  const [mfaSecret, setMfaSecret] = useState(null);
  const [mfaCodeSetup, setMfaCodeSetup] = useState("");

  const submitConfirmed = async () => {
    setMessage("");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/auth/change", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, old_password: oldPassword, new_password: newPassword || undefined }),
      });
      setShowConfirm(false);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setMessage(body.detail || "Failed to update user");
        return;
      }
      const data = await res.json();
      setMessage("Saved");
      if (onSaved) onSaved(data.username);
    } catch (err) {
      setMessage("Network error");
    }
  };

  const enableMfa = async () => {
    setMessage("");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/auth/mfa/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: localStorage.getItem("auth_token") }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setMessage(body.detail || "Failed to setup MFA");
        return;
      }
      const data = await res.json();
      setMfaSecret({ secret: data.secret, qr: data.qr, otpauth_url: data.otpauth_url });
      setMessage("Scan the QR or copy the secret and enter a verification code to enable MFA.");
    } catch (err) {
      setMessage("Network error");
    }
  };

  const verifyMfaSetup = async () => {
    setMessage("");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/auth/mfa/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: localStorage.getItem("auth_token"), code: mfaCodeSetup }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setMessage(body.detail || "Failed to verify MFA");
        return;
      }
      setMfaSecret(null);
      setMfaCodeSetup("");
      setMessage("MFA enabled");
    } catch (err) {
      setMessage("Network error");
    }
  };

  const submit = (e) => {
    e.preventDefault();
    setMessage("");
    // require old password before showing confirmation
    if (!oldPassword) {
      setMessage("Please enter your current password to confirm.");
      return;
    }
    setShowConfirm(true);
  };

  return (
    <div className="max-w-4xl mx-auto" style={{ color: "var(--text)" }}>
      <div className="mb-6">
        <div className="flex flex-col gap-2">
          <div className="text-sm uppercase tracking-[0.24em] text-[color:var(--textMuted)]">Account settings</div>
          <h2 className="text-3xl font-semibold">Profile & security</h2>
          <p className="max-w-2xl text-sm text-[color:var(--textMuted)]">
            Manage your account details, change your password, and configure multi-factor authentication for stronger access protection.
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <section className="rounded-3xl border border-[color:var(--border)] bg-[color:var(--card)] p-6 shadow-sm">
            <div className="flex items-center justify-between gap-4 mb-4">
              <div>
                <h3 className="text-xl font-semibold">Account details</h3>
                <p className="text-sm text-[color:var(--textMuted)]">Update your username and password information.</p>
              </div>
            </div>

            <form onSubmit={submit} className="space-y-5">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-[color:var(--textMuted)]">Username</label>
                <div className="flex flex-col sm:flex-row sm:items-center sm:gap-3">
                  <div className="flex-1 rounded-2xl border border-[color:var(--borderSoft)] bg-[color:var(--bg)] px-4 py-3 text-sm text-[color:var(--text)]">{currentUser}</div>
                  <button type="button" onClick={() => goTo("change-username")} className="mt-3 sm:mt-0 inline-flex items-center justify-center rounded-2xl border border-[color:var(--border)] bg-[color:var(--bg)] px-4 py-2 text-sm font-medium text-[color:var(--text)] transition hover:bg-[color:var(--borderSoft)]">
                    Change username
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-[color:var(--textMuted)]">Current password</label>
                <input type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} className="w-full rounded-2xl border border-[color:var(--borderSoft)] bg-[color:var(--bg)] px-4 py-3 text-sm text-[color:var(--text)] outline-none focus:border-[color:var(--blue)] focus:ring-2 focus:ring-[color:var(--blueSoft)]" />
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-[color:var(--textMuted)]">New password</label>
                <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full rounded-2xl border border-[color:var(--borderSoft)] bg-[color:var(--bg)] px-4 py-3 text-sm text-[color:var(--text)] outline-none focus:border-[color:var(--blue)] focus:ring-2 focus:ring-[color:var(--blueSoft)]" />
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <button className="inline-flex items-center justify-center rounded-2xl bg-[color:var(--blue)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500" type="submit">
                  Save changes
                </button>
                {message ? <div className="text-sm text-[color:var(--textMuted)]">{message}</div> : null}
              </div>
            </form>
          </section>

          <section className="rounded-3xl border border-[color:var(--border)] bg-[color:var(--card)] p-6 shadow-sm">
            <div className="flex items-center justify-between gap-4 mb-4">
              <div>
                <h3 className="text-xl font-semibold">Security preferences</h3>
                <p className="text-sm text-[color:var(--textMuted)]">Enable extra protection and review your sign-in security options.</p>
              </div>
            </div>

            {mfaSecret ? (
              <div className="space-y-5">
                <div className="rounded-2xl border border-[color:var(--borderSoft)] bg-[color:var(--bg)] p-4 text-sm text-[color:var(--text)]">
                  <div className="font-medium mb-2">Scan QR code</div>
                  {mfaSecret.otpauth_url ? (
                    <img
                      src={`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(mfaSecret.otpauth_url)}&size=200x200`}
                      alt="mfa-qr"
                      className="mx-auto mb-4 h-40 w-40"
                    />
                  ) : null}
                  <div className="mb-2">Secret key</div>
                  <div className="rounded-2xl bg-[color:var(--card)] p-3 text-sm break-all">{mfaSecret.secret}</div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-[color:var(--textMuted)]">Verification code</label>
                  <input value={mfaCodeSetup} onChange={(e) => setMfaCodeSetup(e.target.value)} className="w-full rounded-2xl border border-[color:var(--borderSoft)] bg-[color:var(--bg)] px-4 py-3 text-sm text-[color:var(--text)] outline-none focus:border-[color:var(--blue)] focus:ring-2 focus:ring-[color:var(--blueSoft)]" />
                </div>

                <div className="flex flex-wrap gap-3">
                  <button type="button" onClick={verifyMfaSetup} className="inline-flex items-center justify-center rounded-2xl bg-[color:var(--blue)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500">
                    Verify MFA
                  </button>
                  <button type="button" onClick={() => setMfaSecret(null)} className="inline-flex items-center justify-center rounded-2xl border border-[color:var(--border)] bg-[color:var(--bg)] px-5 py-3 text-sm font-medium text-[color:var(--text)] transition hover:bg-[color:var(--borderSoft)]">
                    Cancel setup
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-[color:var(--textMuted)]">Protect your account with a TOTP authenticator app such as Google Authenticator or Authy.</p>
                <button type="button" onClick={enableMfa} className="inline-flex items-center justify-center rounded-2xl bg-[color:var(--blue)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500">
                  Enable MFA
                </button>
              </div>
            )}
          </section>
        </div>

        <aside className="space-y-6">
          <div className="rounded-3xl border border-[color:var(--border)] bg-[color:var(--card)] p-6 shadow-sm">
            <h3 className="text-lg font-semibold">Quick tips</h3>
            <div className="mt-3 space-y-3 text-sm text-[color:var(--textMuted)]">
              <p>Use a strong password and keep your MFA device secure.</p>
              <p>If you lose access to your authenticator app, contact support to recover your account.</p>
              <p>MFA adds an extra verification step to keep your data safe.</p>
            </div>
          </div>

          <div className="rounded-3xl border border-[color:var(--border)] bg-[color:var(--card)] p-6 shadow-sm">
            <h3 className="text-lg font-semibold">Account status</h3>
            <div className="mt-3 grid gap-3 text-sm text-[color:var(--textMuted)]">
              <div className="rounded-2xl bg-[color:var(--bg)] p-3">Signed in as <span className="font-medium text-[color:var(--text)]">{currentUser}</span></div>
              <div className="rounded-2xl bg-[color:var(--bg)] p-3">MFA status: <span className="font-medium text-[color:var(--text)]">{mfaSecret ? "Setup pending" : "Not enabled"}</span></div>
            </div>
          </div>
        </aside>
      </div>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md rounded-3xl border border-[color:var(--border)] bg-[color:var(--card)] p-6 shadow-2xl">
            <div className="mb-5 text-base text-[color:var(--text)]">Are you sure you want to save these changes?</div>
            <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
              <button onClick={() => setShowConfirm(false)} className="inline-flex items-center justify-center rounded-2xl border border-[color:var(--border)] bg-[color:var(--bg)] px-5 py-3 text-sm font-medium text-[color:var(--text)] transition hover:bg-[color:var(--borderSoft)]">
                Cancel
              </button>
              <button onClick={submitConfirmed} className="inline-flex items-center justify-center rounded-2xl bg-[color:var(--blue)] px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500">
                Confirm changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
