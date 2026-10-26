import { useState } from "react";

import { apiPost } from "../../api.js";

const emptyForm = {
  username: "",
  first_name: "",
  last_name: "",
  email: "",
  password: "",
};

export default function Register({ onRegistered, submitRegistration = (values) => apiPost("register", values) }) {
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
    setError("");
    setSuccess("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      const user = await submitRegistration(form);
      setSuccess("Account created for " + user.username + ". You can now sign in.");
      setForm(emptyForm);
      onRegistered?.(user);
    } catch (requestError) {
      setError(requestError.message || "Registration failed. Check your details and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="form-card" aria-labelledby="register-heading">
      <p className="eyebrow">Create an account</p>
      <h1 id="register-heading">Register</h1>
      <p className="muted">Create an account to write and save a dealership review.</p>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div>
            <label htmlFor="register-username">Username</label>
            <input id="register-username" autoComplete="username" name="username" value={form.username} onChange={updateField} required minLength={3} />
          </div>
          <div>
            <label htmlFor="register-first-name">First Name</label>
            <input id="register-first-name" autoComplete="given-name" name="first_name" value={form.first_name} onChange={updateField} required />
          </div>
          <div>
            <label htmlFor="register-last-name">Last Name</label>
            <input id="register-last-name" autoComplete="family-name" name="last_name" value={form.last_name} onChange={updateField} required />
          </div>
          <div>
            <label htmlFor="register-email">Email</label>
            <input id="register-email" autoComplete="email" type="email" name="email" value={form.email} onChange={updateField} required />
          </div>
          <div className="full-width">
            <label htmlFor="register-password">Password</label>
            <input id="register-password" aria-describedby="register-password-hint" autoComplete="new-password" type="password" name="password" value={form.password} onChange={updateField} required minLength={8} />
            <span id="register-password-hint" className="field-hint">Use a strong password of at least 8 characters.</span>
          </div>
        </div>
        {error && <p className="form-message error" role="alert">{error}</p>}
        {success && <p className="form-message success" role="status">{success}</p>}
        <button className="button button-primary" type="submit" disabled={submitting}>
          {submitting ? "Creating account…" : "Register"}
        </button>
      </form>
    </section>
  );
}
