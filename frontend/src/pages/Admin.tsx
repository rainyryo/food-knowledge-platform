import { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Upload,
  FileText,
  Trash2,
  RefreshCw,
  Database,
  Search,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import {
  getDocuments,
  uploadDocument,
  deleteDocument,
  reprocessDocument,
  getSystemStats,
  createSearchIndex,
} from '../api';

interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  application: string | null;
  issue: string | null;
  ingredient: string | null;
  status: string;
  created_at: string;
  indexed_at: string | null;
  error_message: string | null;
}

interface SystemStats {
  total_documents: number;
  indexed_documents: number;
  pending_documents: number;
  error_documents: number;
  total_users: number;
  total_searches: number;
  avg_response_time_ms: number;
}

export default function Admin() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [docsResponse, statsResponse] = await Promise.all([
        getDocuments(1, 100),
        getSystemStats(),
      ]);
      setDocuments(docsResponse.documents);
      setStats(statsResponse);
    } catch (err: any) {
      console.error('Failed to load data:', err);
      if (err.response?.status === 403) {
        setMessage({ 
          type: 'error', 
          text: 'アクセス権限がありません。管理者権限が必要です。' 
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true);
    setMessage(null);

    try {
      for (const file of acceptedFiles) {
        await uploadDocument(file);
      }
      setMessage({
        type: 'success',
        text: `${acceptedFiles.length}件のファイルをアップロードしました`,
      });
      loadData();
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'アップロードに失敗しました',
      });
    } finally {
      setUploading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'application/vnd.ms-powerpoint': ['.ppt'],
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg'],
    },
  });

  const handleDelete = async (id: number, filename: string) => {
    if (!confirm(`「${filename}」を削除しますか？`)) return;

    try {
      await deleteDocument(id);
      setMessage({ type: 'success', text: 'ドキュメントを削除しました' });
      loadData();
    } catch (err) {
      setMessage({ type: 'error', text: '削除に失敗しました' });
    }
  };

  const handleReprocess = async (id: number, filename: string) => {
    if (!confirm(`「${filename}」を再処理しますか？`)) return;

    try {
      await reprocessDocument(id);
      setMessage({ type: 'success', text: 'ドキュメントの再処理を開始しました' });
      loadData();
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || '再処理の開始に失敗しました',
      });
    }
  };

  const handleCreateIndex = async () => {
    try {
      await createSearchIndex();
      setMessage({ type: 'success', text: '検索インデックスを作成しました' });
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'インデックス作成に失敗しました',
      });
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'processing':
        return <RefreshCw className="w-4 h-4 text-unitec-blue animate-spin" />;
      default:
        return <AlertCircle className="w-4 h-4 text-unitec-blueGray" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('ja-JP');
  };

  return (
    <div className="space-y-6">
      {/* Message */}
      {message && (
        <div
          className={`p-4 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-unitec-blue">
            <div className="flex items-center">
              <Database className="w-8 h-8 text-unitec-blue mr-3" />
              <div>
                <div className="text-2xl font-bold text-unitec-darkGray">{stats.total_documents}</div>
                <div className="text-sm text-unitec-blueGray">ドキュメント数</div>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-500 mr-3" />
              <div>
                <div className="text-2xl font-bold text-unitec-darkGray">{stats.indexed_documents}</div>
                <div className="text-sm text-unitec-blueGray">インデックス済み</div>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-unitec-lightBlue">
            <div className="flex items-center">
              <Search className="w-8 h-8 text-unitec-lightBlue mr-3" />
              <div>
                <div className="text-2xl font-bold text-unitec-darkGray">{stats.total_searches}</div>
                <div className="text-sm text-unitec-blueGray">総検索数</div>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-unitec-yellow">
            <div className="flex items-center">
              <Clock className="w-8 h-8 text-unitec-blueGray mr-3" />
              <div>
                <div className="text-2xl font-bold text-unitec-darkGray">
                  {(stats.avg_response_time_ms / 1000).toFixed(1)}s
                </div>
                <div className="text-sm text-unitec-blueGray">平均応答時間</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">ドキュメントアップロード</h2>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
            isDragActive
              ? 'border-unitec-blue bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          {uploading ? (
            <p className="text-gray-600">アップロード中...</p>
          ) : isDragActive ? (
            <p className="text-unitec-blue font-medium">ここにドロップしてください</p>
          ) : (
            <div>
              <p className="text-gray-600 mb-2">
                ファイルをドラッグ＆ドロップ、またはクリックして選択
              </p>
              <p className="text-sm text-gray-400">
                対応形式: Excel, Word, PowerPoint, PDF, 画像
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={loadData}
            className="flex items-center px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2 text-unitec-blueGray" />
            更新
          </button>
          <button
            onClick={handleCreateIndex}
            className="flex items-center px-4 py-2 text-sm bg-blue-100 text-unitec-blue hover:bg-blue-200 rounded-lg transition-colors"
          >
            <Database className="w-4 h-4 mr-2" />
            インデックス作成
          </button>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">ドキュメント一覧</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ファイル名
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  サイズ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ステータス
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  登録日時
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    読み込み中...
                  </td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    ドキュメントがありません
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <FileText className="w-4 h-4 text-gray-400 mr-2" />
                        <span className="text-sm truncate max-w-xs" title={doc.original_filename}>
                          {doc.original_filename}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td className="px-6 py-4">
                      <div 
                        className="flex items-center"
                        title={doc.status === 'error' && doc.error_message ? doc.error_message : undefined}
                      >
                        {getStatusIcon(doc.status)}
                        <span className="ml-2 text-sm text-gray-500">
                          {doc.status === 'completed' ? '完了' :
                           doc.status === 'processing' ? '処理中' :
                           doc.status === 'error' ? 'エラー' : '待機中'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatDate(doc.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {(doc.status === 'error' || doc.status === 'processing') && (
                          <button
                            onClick={() => handleReprocess(doc.id, doc.original_filename)}
                            className="text-blue-600 hover:text-blue-800"
                            title="再処理"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(doc.id, doc.original_filename)}
                          className="text-red-600 hover:text-red-800"
                          title="削除"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
