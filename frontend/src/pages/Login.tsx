import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { LoginPage as CDKLoginPage } from '@cidqueiroz/cdkteck-ui';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleLogin = async (credentials: { email: string; password: string }) => {
    setLoading(true);
    setErrorMsg(null);

    const { error } = await signIn(credentials.email.trim(), credentials.password.trim());
    setLoading(false);

    if (error) {
      setErrorMsg(`Erro de login: ${error.message || 'Verifique seu e-mail e senha.'}`);
    } else {
      navigate('/', { replace: true });
    }
  };

  const handleRegister = async (credentials: { email: string; password: string }) => {
    setLoading(true);
    setErrorMsg(null);

    const { error } = await signUp(credentials.email.trim(), credentials.password.trim());
    setLoading(false);

    if (error) {
      setErrorMsg(`Erro ao cadastrar: ${error.message}`);
    } else {
      alert('Conta criada com sucesso! Faça login com suas credenciais.');
    }
  };

  const handleSocialLogin = (provider: string) => {
    alert(`Login com ${provider} em desenvolvimento.`);
  };

  const CustomRouterLink = ({ href, className, children, ...props }: any) => (
    <Link to={href} className={className} {...props}>
      {children}
    </Link>
  );

  return (
    <CDKLoginPage
      title="Bem-vindo ao"
      appName="AprovaTeck"
      onLogin={handleLogin}
      onRegister={handleRegister}
      onGoogleLogin={() => handleSocialLogin('Google')}
      onGitHubLogin={() => handleSocialLogin('GitHub')}
      onFacebookLogin={() => handleSocialLogin('Facebook')}
      isLoading={loading}
      error={errorMsg}
      LinkComponent={CustomRouterLink}
    />
  );
};

export default Login;
