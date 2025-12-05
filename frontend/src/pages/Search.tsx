import { useState, useRef, useEffect } from 'react';
import { Search as SearchIcon, Send, FileText, Clock, Eye, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { search, getSearchHistory, getDocumentDownloadUrl } from '../api';

interface SearchResult {
  id: string;
  document_id: number;
  filename: string;
  application: string | null;
  issue: string | null;
  ingredient: string | null;
  customer: string | null;
  trial_id: string | null;
  sheet_name: string | null;
  content_preview: string;
  score: number;
  blob_url: string | null;
}

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  results?: SearchResult[];
  responseTime?: number;
}

interface HistoryItem {
  id: number;
  query: string;
  results_count: number;
  created_at: string;
}

export default function Search() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewFilename, setPreviewFilename] = useState<string>('');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadHistory = async () => {
    try {
      const data = await getSearchHistory(20);
      setHistory(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };


  const handleFilePreview = async (documentId: number, filename: string) => {
    setPreviewFilename(filename);
    setPreviewError(null);
    setPreviewLoading(true);
    
    try {
      const data = await getDocumentDownloadUrl(documentId);
      setPreviewUrl(data.download_url);
      setPreviewError(null);
    } catch (err: any) {
      console.error('Failed to preview file:', err);
      
      // エラーメッセージをより詳細に
      let errorMessage = 'ファイルのプレビューURLの取得に失敗しました';
      
      if (err.response?.status === 400) {
        errorMessage = 'ファイルがまだアップロード中、または処理に失敗しています。\n管理画面でファイルのステータスを確認してください。';
      } else if (err.response?.status === 404) {
        errorMessage = 'ドキュメントが見つかりません。\nファイルが削除された可能性があります。';
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      
      setPreviewError(errorMessage);
      setPreviewUrl(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreview = () => {
    setPreviewUrl(null);
    setPreviewFilename('');
    setPreviewError(null);
  };

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: query,
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setLoading(true);

    try {
      const result = await search(query.trim(), 10, undefined);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: result.response,
        results: result.results,
        responseTime: result.response_time_ms,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      loadHistory();
    } catch (err: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'エラーが発生しました。もう一度お試しください。',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleHistoryClick = (historyQuery: string) => {
    setQuery(historyQuery);
    setShowHistory(false);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto bg-white rounded-lg shadow mb-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500 p-8">
            <SearchIcon className="w-16 h-16 mb-4 text-gray-300" />
            <h3 className="text-xl font-medium mb-2">過去の案件を検索</h3>
            <p className="text-center text-sm mb-6">
              自然言語で質問を入力してください
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
              {[
                'りんごプレザーブ耐熱性付与',
                'ドーナツの吸油抑制',
                'カルボナーラソース',
                '野菜の離水防止剤',
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => setQuery(example)}
                  className="px-4 py-2 text-sm bg-gray-100 hover:bg-blue-50 hover:text-unitec-blue hover:border-unitec-yellow border border-transparent rounded-lg text-left transition-all"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl rounded-lg p-4 ${
                    message.type === 'user'
                      ? 'bg-unitec-blue text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {message.type === 'assistant' ? (
                    <div>
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>

                      {message.results && message.results.length > 0 && (
                        <div className="mt-4 border-t pt-4">
                          <h4 className="text-sm font-medium mb-3">
                            関連する過去案件
                          </h4>
                          <div className="space-y-3">
                            {message.results.slice(0, 5).map((result) => (
                              <div
                                key={result.id}
                                className="bg-white rounded border p-3 text-sm"
                              >
                                <div className="flex items-start justify-between mb-2">
                                  <div className="flex items-center">
                                    <FileText className="w-4 h-4 mr-2 text-gray-400" />
                                    <span className="font-medium truncate max-w-xs">
                                      {result.filename}
                                    </span>
                                  </div>
                                </div>

                                <div className="flex flex-wrap gap-2 mb-2">
                                  {result.application && (
                                    <span className="text-xs bg-blue-50 text-unitec-blue border border-unitec-blue px-2 py-0.5 rounded font-medium">
                                      {result.application}
                                    </span>
                                  )}
                                  {result.issue && (
                                    <span className="text-xs bg-yellow-50 text-unitec-darkGray border border-unitec-yellow px-2 py-0.5 rounded font-medium">
                                      {result.issue}
                                    </span>
                                  )}
                                  {result.ingredient && (
                                    <span className="text-xs bg-gray-50 text-unitec-blueGray border border-unitec-blueGray px-2 py-0.5 rounded font-medium">
                                      {result.ingredient}
                                    </span>
                                  )}
                                </div>

                                <p className="text-xs text-gray-600 line-clamp-3">
                                  {result.content_preview}
                                </p>

                                <button
                                  onClick={() => handleFilePreview(result.document_id, result.filename)}
                                  className="mt-2 inline-flex items-center text-xs text-unitec-blue hover:text-unitec-lightBlue font-medium transition-colors"
                                >
                                  <Eye className="w-3 h-3 mr-1" />
                                  プレビュー
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {message.responseTime && (
                        <div className="mt-2 text-xs text-gray-400">
                          応答時間: {(message.responseTime / 1000).toFixed(1)}秒
                        </div>
                      )}
                    </div>
                  ) : (
                    <p>{message.content}</p>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="bg-white rounded-lg shadow p-4">
        <form onSubmit={handleSearch} className="flex items-center space-x-3">
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowHistory(!showHistory)}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            >
              <Clock className="w-5 h-5" />
            </button>

            {showHistory && history.length > 0 && (
              <div className="absolute bottom-full left-0 mb-2 w-64 bg-white rounded-lg shadow-lg border max-h-60 overflow-y-auto">
                <div className="p-2">
                  <div className="text-xs font-medium text-gray-500 px-2 py-1">
                    検索履歴
                  </div>
                  {history.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleHistoryClick(item.query)}
                      className="w-full text-left px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded"
                    >
                      {item.query}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="質問を入力してください（例: 野菜炒めの離水防止）"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-unitec-blue focus:border-transparent"
            disabled={loading}
          />

          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="p-3 bg-unitec-blue text-white rounded-lg hover:bg-unitec-lightBlue disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>

      {/* Preview Modal */}
      {(previewUrl || previewFilename) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center">
                <FileText className="w-5 h-5 mr-2 text-unitec-blue" />
                <h3 className="font-medium text-gray-900 truncate max-w-xl">
                  {previewFilename}
                </h3>
              </div>
              <button
                onClick={closePreview}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-hidden bg-gray-100">
              {previewLoading ? (
                <div className="h-full flex flex-col items-center justify-center">
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-3 h-3 bg-unitec-blue rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-3 h-3 bg-unitec-blue rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-3 h-3 bg-unitec-blue rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <p className="text-sm text-gray-600">ファイルを読み込んでいます...</p>
                </div>
              ) : previewError ? (
                <div className="h-full flex flex-col items-center justify-center p-8">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-lg">
                    <div className="flex items-start">
                      <svg className="w-6 h-6 text-red-600 mr-3 flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-red-800 mb-3">プレビューを表示できません</h4>
                        <div className="text-sm text-red-700 mb-4 whitespace-pre-line">
                          {previewError}
                        </div>
                        <div className="bg-white border border-red-300 rounded p-3 mb-3">
                          <p className="text-xs font-medium text-red-800 mb-2">📌 対処方法：</p>
                          <ul className="text-xs text-red-700 space-y-1 list-disc list-inside">
                            <li>「閉じる」ボタンでモーダルを閉じる</li>
                            <li>管理画面でファイルのステータスを確認</li>
                            <li>ステータスが「error」の場合は再アップロード</li>
                            <li>ステータスが「processing」の場合は処理完了まで待つ</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : previewUrl ? (
                <iframe
                  src={`https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(previewUrl)}`}
                  className="w-full h-full border-0"
                  title="Document Preview"
                  onError={() => {
                    setPreviewError('プレビューの読み込みに失敗しました。「新しいタブで開く」または「ダウンロード」をお試しください。');
                  }}
                />
              ) : null}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t bg-gray-50">
              {!previewError && (
                <p className="text-xs text-gray-600 mb-3">
                  ※プレビューが表示されない場合は、「新しいタブで開く」または「ダウンロード」をお試しください
                </p>
              )}
              <div className="flex justify-end gap-3">
                <button
                  onClick={closePreview}
                  className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  閉じる
                </button>
                {previewUrl && (
                  <>
                    <a
                      href={previewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      新しいタブで開く
                    </a>
                    <a
                      href={previewUrl}
                      download
                      className="px-4 py-2 text-sm text-white bg-unitec-blue rounded-lg hover:bg-unitec-lightBlue transition-colors"
                    >
                      ダウンロード
                    </a>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
