'use client';

import { useState } from 'react';
import VideoInput from '@/components/VideoInput';
import VideoCard from '@/components/VideoCard';
import ChatPanel from '@/components/ChatPanel';
import EngagementChart from '@/components/EngagementChart';
import { processVideos, sendMessageStream } from '@/services/api';
import { VideoMetadata, ChatMessage } from '@/types/video';

export default function Home() {
  const [videoA, setVideoA] = useState<VideoMetadata | null>(null);
  const [videoB, setVideoB] = useState<VideoMetadata | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isChatting, setIsChatting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleProcess = async (urlA: string, urlB: string, transcriptA?: string, transcriptB?: string) => {
    setIsProcessing(true);
    setError(null);
    try {
      const data = await processVideos(urlA, urlB, transcriptA, transcriptB);
      setVideoA(data.video_a);
      setVideoB(data.video_b);
      setSessionId(data.session_id);
      setMessages([]); // Reset chat for new videos
    } catch (err: any) {
      setError(err.message || 'An error occurred during processing');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!sessionId) return;

    const userMessage: ChatMessage = { role: 'user', content };
    setMessages((prev) => [...prev, userMessage]);
    setIsChatting(true);

    // Add placeholder for assistant message
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

    try {
      let fullContent = '';
      await sendMessageStream(sessionId, content, (chunk) => {
        fullContent += chunk;
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastMessage = newMessages[newMessages.length - 1];
          if (lastMessage.role === 'assistant') {
            lastMessage.content = fullContent;
          }
          return newMessages;
        });
      });
    } catch (err: any) {
      setError(err.message || 'Failed to get response');
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 font-sans text-gray-900">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-black tracking-tight text-gray-900 sm:text-6xl">
            Vibe<span className="text-blue-600">Check</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto font-medium">
            Analyze and compare any two social media videos with AI-driven RAG analysis.
          </p>
        </div>

        {/* Input Section */}
        {!videoA && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <VideoInput onProcess={handleProcess} isLoading={isProcessing} />
          </div>
        )}

        {error && (
          <div className="max-w-4xl mx-auto bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Comparison Section */}
        {videoA && videoB && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-in fade-in zoom-in-95 duration-500">
            {/* Left side: Video Cards */}
            <div className="lg:col-span-5 space-y-6">
              <EngagementChart rateA={videoA.engagement_rate || 0} rateB={videoB.engagement_rate || 0} />
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-6">
                <VideoCard video={videoA} label="A" />
                <VideoCard video={videoB} label="B" />
              </div>
              <button 
                onClick={() => { setVideoA(null); setVideoB(null); setSessionId(null); }}
                className="w-full py-3 text-gray-500 hover:text-gray-700 font-medium transition flex items-center justify-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                <span>Compare different videos</span>
              </button>
            </div>

            {/* Right side: Chat Panel */}
            <div className="lg:col-span-7">
              <ChatPanel 
                messages={messages} 
                onSendMessage={handleSendMessage} 
                isLoading={isChatting} 
              />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
