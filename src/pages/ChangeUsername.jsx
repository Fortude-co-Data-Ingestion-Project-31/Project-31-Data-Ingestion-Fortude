import React, { useState } from "react";

export default function ChangeUsername({ token, currentUser, onSaved, goTo }) {
  const [newUsername, setNewUsername] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [message, setMessage] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);

  const submitConfirmed = async () => {
    setMessage("");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/auth/change", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, old_password: oldPassword, new_username: newUsername }),
      });
      setShowConfirm(false);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setMessage(body.detail || "Failed to update username");
        return;
      }
      const data = await res.json();
      setMessage("Saved");
      if (onSaved) onSaved(data.username);
      // return to settings
      goTo("settings");
    } catch (err) {
      setMessage("Network error");
    }
  };

  const submit = (e) => {
    e.preventDefault();
    setMessage("");
    if (!oldPassword) {
      setMessage("Please enter your current password to confirm.");
      return;
    }
    if (!newUsername) {
      setMessage("Please enter a new username.");
      return;
    }
    setShowConfirm(true);
  };

  return (
    <div className="max-w-lg">
      <h2 className="text-lg font-semibold mb-4">Change Username</h2>
      <div className="mb-4">Signed in as <strong>{currentUser}</strong></div>
      <form onSubmit={submit} className="space-y-3">
        <div>
          <label className="block mb-1 text-sm">New username</label>
          <input value={newUsername} onChange={(e) => setNewUsername(e.target.value)} className="w-full p-2 border rounded" />
        </div>
        <div>
          <label className="block mb-1 text-sm">Current password</label>
          <input type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} className="w-full p-2 border rounded" />
        </div>
        <div className="flex gap-2">
          <button className="bg-blue-600 text-white px-3 py-2 rounded">Save</button>
          <button type="button" onClick={() => goTo("settings")} className="px-3 py-2 rounded border">Back</button>
        </div>
        {message ? <div className="text-sm mt-2">{message}</div> : null}
      </form>

      {showConfirm && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/40">
          <div className="bg-white p-6 rounded shadow max-w-sm w-full">
            <div className="mb-4">Are you sure you want to change your username to <strong>{newUsername}</strong>?</div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowConfirm(false)} className="px-3 py-2 border rounded">Cancel</button>
              <button onClick={submitConfirmed} className="px-3 py-2 bg-blue-600 text-white rounded">Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
