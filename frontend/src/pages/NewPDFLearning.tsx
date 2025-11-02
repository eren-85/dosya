/**
 * PDF Learning Page - RAG System
 * - Upload PDF documents
 * - Extract and process text
 * - Store in vector database
 * - Ask questions about uploaded PDFs
 */

import { useState } from 'react';
import { Upload, FileText, Trash2, MessageSquare, Send, BookOpen } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface UploadedPDF {
  id: string;
  name: string;
  size: number;
  uploadedAt: string;
  pages: number;
  status: 'processing' | 'ready' | 'error';
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export default function NewPDFLearning() {
  const [pdfs, setPdfs] = useState<UploadedPDF[]>([]);
  const [uploading, setUploading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [askingQuestion, setAskingQuestion] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);

    for (const file of Array.from(files)) {
      if (!file.name.endsWith('.pdf')) {
        alert('Please upload only PDF files');
        continue;
      }

      const newPdf: UploadedPDF = {
        id: Date.now().toString() + Math.random(),
        name: file.name,
        size: file.size,
        uploadedAt: new Date().toISOString(),
        pages: 0, // Will be updated after processing
        status: 'processing',
      };

      setPdfs(prev => [...prev, newPdf]);

      // Simulate processing (in real app, send to backend)
      setTimeout(() => {
        setPdfs(prev => prev.map(p =>
          p.id === newPdf.id
            ? { ...p, status: 'ready', pages: Math.floor(Math.random() * 50) + 10 }
            : p
        ));
      }, 2000);
    }

    setUploading(false);
    e.target.value = ''; // Reset input
  };

  const handleDeletePDF = (id: string) => {
    if (confirm('Are you sure you want to delete this PDF?')) {
      setPdfs(prev => prev.filter(p => p.id !== id));
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim()) return;
    if (pdfs.filter(p => p.status === 'ready').length === 0) {
      alert('Please upload and process at least one PDF first');
      return;
    }

    const userMessage: ChatMessage = {
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setAskingQuestion(true);

    // Simulate AI response (in real app, call RAG backend)
    setTimeout(() => {
      const aiMessage: ChatMessage = {
        role: 'assistant',
        content: `🤖 **RL Agent Eğitim Sistemi**\n\nPDF'leriniz Reinforcement Learning agent'ını eğitmek için kullanılıyor.\n\n**Amaç:**\n- Trading psikolojisi, davranış kalıpları ve smart money stratejilerini öğrenmek\n- Retail trader hatalarından kaçınmak\n- Büyük oyuncuların (whales, kurumsal yatırımcılar) stratejilerini taklit etmek\n\n**Nasıl Çalışır:**\n- PDF içerikleri analiz edilir ve yapılandırılır\n- RL agent bu bilgileri reward function'ına entegre eder\n- Model, öğrenilen stratejilere göre trade kararları verir\n\n**Demo Modu:** Gerçek üretimde PDF'ler işlenir ve model eğitim pipeline'ına eklenir.\n\nBackend: \`backend.learning.pdf_rag\` → \`backend.models.ppo_agent\``,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, aiMessage]);
      setAskingQuestion(false);
    }, 1500);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">PDF Learning (RL Training)</h1>
        <p className="text-muted-foreground">
          Upload trading psychology, smart money strategies, and market behavior PDFs to train the RL agent
        </p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            Upload Training PDFs
          </CardTitle>
          <CardDescription>
            Upload trading psychology, smart money strategies, whale behavior analysis, and institutional trading PDFs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed rounded-lg p-8 text-center">
            <input
              type="file"
              id="pdf-upload"
              accept=".pdf"
              multiple
              onChange={handleFileUpload}
              className="hidden"
              disabled={uploading}
            />
            <label htmlFor="pdf-upload" className="cursor-pointer">
              <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-sm font-medium">
                {uploading ? 'Uploading...' : 'Click to upload PDFs'}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Supports multiple files, max 50MB each
              </p>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Uploaded PDFs List */}
      {pdfs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Uploaded Documents ({pdfs.length})</CardTitle>
            <CardDescription>Manage your PDF knowledge base</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {pdfs.map((pdf) => (
                <div
                  key={pdf.id}
                  className="flex items-center justify-between p-3 rounded-lg border bg-secondary/50"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{pdf.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(pdf.size)}
                        {pdf.pages > 0 && ` • ${pdf.pages} pages`}
                        {' • '}
                        {new Date(pdf.uploadedAt).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={
                      pdf.status === 'ready' ? 'default' :
                      pdf.status === 'processing' ? 'secondary' : 'destructive'
                    }>
                      {pdf.status === 'ready' ? 'Ready' :
                       pdf.status === 'processing' ? 'Processing...' : 'Error'}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeletePDF(pdf.id)}
                      disabled={pdf.status === 'processing'}
                    >
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Q&A Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Ask Questions
          </CardTitle>
          <CardDescription>
            Ask questions about your uploaded PDFs using AI
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Messages */}
          {messages.length > 0 && (
            <div className="max-h-96 overflow-y-auto space-y-3 mb-4">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground ml-12'
                      : 'bg-secondary mr-12'
                  }`}
                >
                  <p className="text-sm">{msg.content}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              ))}
              {askingQuestion && (
                <div className="p-3 rounded-lg bg-secondary mr-12">
                  <p className="text-sm text-muted-foreground">AI is thinking...</p>
                </div>
              )}
            </div>
          )}

          {messages.length === 0 && (
            <Alert>
              <AlertDescription>
                Upload PDFs and start asking questions. Try: "What are the key support and resistance concepts?"
                or "Explain the Elliott Wave Theory"
              </AlertDescription>
            </Alert>
          )}

          {/* Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAskQuestion()}
              placeholder="Ask a question about your PDFs..."
              className="flex-1 px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              disabled={askingQuestion || pdfs.filter(p => p.status === 'ready').length === 0}
            />
            <Button
              onClick={handleAskQuestion}
              disabled={askingQuestion || !question.trim() || pdfs.filter(p => p.status === 'ready').length === 0}
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
