import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Search, Settings, LogOut, User } from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
  user: {
    username: string;
    full_name: string;
    is_admin: boolean;
  };
  onLogout: () => void;
}

export default function Layout({ children, user, onLogout }: LayoutProps) {
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('token');
    onLogout();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b-4 border-unitec-yellow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div className="text-2xl font-bold tracking-tight">
                  <span className="text-unitec-blue">UNITEC FOODS</span>
                </div>
              </div>
              <div className="h-8 w-px bg-unitec-blueGray"></div>
              <h1 className="text-lg font-semibold text-unitec-darkGray">
                食品開発ナレッジプラットフォーム
              </h1>
            </div>

            {/* Navigation */}
            <nav className="flex items-center space-x-4">
              <Link
                to="/"
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === '/'
                    ? 'bg-unitec-blue text-white'
                    : 'text-gray-600 hover:bg-blue-50 hover:text-unitec-blue'
                }`}
              >
                <Search className="w-4 h-4 mr-2" />
                検索
              </Link>

              {user.is_admin && (
                <Link
                  to="/admin"
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    location.pathname === '/admin'
                      ? 'bg-unitec-blue text-white'
                      : 'text-gray-600 hover:bg-blue-50 hover:text-unitec-blue'
                  }`}
                >
                  <Settings className="w-4 h-4 mr-2" />
                  管理
                </Link>
              )}

              {/* User Menu */}
              <div className="flex items-center ml-4 pl-4 border-l">
                <div className="flex items-center text-sm text-gray-600 mr-4">
                  <User className="w-4 h-4 mr-1" />
                  <span className="mr-2">{user.full_name || user.username}</span>
                  {user.is_admin ? (
                    <span className="px-2 py-0.5 text-xs font-semibold bg-unitec-blue text-white rounded">
                      管理者
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 text-xs font-semibold bg-gray-200 text-gray-700 rounded">
                      ユーザー
                    </span>
                  )}
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  ログアウト
                </button>
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
