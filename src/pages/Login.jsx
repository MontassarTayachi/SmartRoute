import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppIcon from '../components/AppIcon';
import { useAuth } from '../hooks/useAuth';

const roleToPath = {
  ADMIN: '/admin/dashboard',
  MANAGER: '/manager/dashboard',
  DRIVER: '/driver/profile',
};

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = await login(form.email, form.password);
      navigate(roleToPath[payload?.user?.role] ?? '/login', { replace: true });
    } catch (requestError) {
      const status = requestError?.response?.status;
      if (status === 401) {
        setError('Identifiants invalides.');
      } else if (status === 423) {
        setError('Compte verrouillé. Réessayez plus tard.');
      } else if (status === 400 && requestError?.response?.data?.message) {
        setError(requestError.response.data.message);
      } else {
        setError('Une erreur réseau est survenue.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <AppIcon size={72} className="login-logo" />
          <h1>SmartRoute</h1>
          <p>Geolocation, IA et orchestration de flotte en temps réel.</p>
        </div>
        <form className="auth-form" onSubmit={submit}>
          <label className="field-label">
            Email
            <input
              className="input-glass"
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              required
            />
          </label>
          <label className="field-label">
            Mot de passe
            <input
              className="input-glass"
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
            />
          </label>
          {error ? <div className="form-error">{error}</div> : null}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
