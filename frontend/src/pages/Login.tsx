import { useState } from 'react';
import { Link } from 'react-router-dom';
import { login } from '../api';

interface LoginProps {
  onLogin: (user: any) => void;
}

export default function Login({ onLogin }: LoginProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await login(username, password);
      localStorage.setItem('token', response.access_token);

      // Get user data
      const { getMe } = await import('../api');
      const userData = await getMe();
      onLogin(userData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'ログインに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mb-6 inline-block">
            <div className="text-3xl font-bold tracking-tight mb-2">
              <span className="text-unitec-blue">UNITEC FOODS</span>
            </div>
            <div className="h-1 w-full bg-gradient-to-r from-unitec-blue via-unitec-yellow to-unitec-blue rounded-full"></div>
          </div>
          <h2 className="text-2xl font-bold text-unitec-darkGray">
            食品開発ナレッジプラットフォーム
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            ログインしてご利用ください
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="username" className="sr-only">
                ユーザー名
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-2 focus:ring-unitec-blue focus:border-unitec-blue focus:z-10 sm:text-sm"
                placeholder="ユーザー名"
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                パスワード
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-2 focus:ring-unitec-blue focus:border-unitec-blue focus:z-10 sm:text-sm"
                placeholder="パスワード"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-unitec-blue hover:bg-unitec-lightBlue focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-unitec-blue disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '読み込み中...' : 'ログイン'}
            </button>
          </div>

          <div className="text-center text-sm text-gray-500 space-y-1">
            <p>初期アカウント</p>
            <p>admin / admin123</p>
            <p>user / user123</p>
          </div>

          <div className="text-center">
            <Link
              to="/register"
              className="text-sm text-unitec-blue hover:text-unitec-lightBlue transition-colors"
            >
              新規ユーザー登録はこちら
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
