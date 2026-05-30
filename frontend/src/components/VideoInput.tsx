'use client';

import { useState } from 'react';

interface VideoInputProps {
  onProcess: (urlA: string, urlB: string, transcriptA?: string, transcriptB?: string) => void;
  isLoading: boolean;
}

export default function VideoInput({ onProcess, isLoading }: VideoInputProps) {
  const [urlA, setUrlA] = useState('');
  const [urlB, setUrlB] = useState('');
  const [transcriptA, setTranscriptA] = useState('');
  const [transcriptB, setTranscriptB] = useState('');
  const [showTranscripts, setShowTranscripts] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const finalUrlA = urlA || 'https://manual.video/a';
    const finalUrlB = urlB || 'https://manual.video/b';
    onProcess(finalUrlA, finalUrlB, transcriptA || undefined, transcriptB || undefined);
  };

  const isReady = (urlA && urlB) || (transcriptA && transcriptB);

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-lg border border-gray-100">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Video A URL (YouTube/Instagram)</label>
          <input
            type="text"
            value={urlA}
            onChange={(e) => setUrlA(e.target.value)}
            placeholder="Enter URL A..."
            className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">Video B URL (YouTube/Instagram)</label>
          <input
            type="text"
            value={urlB}
            onChange={(e) => setUrlB(e.target.value)}
            placeholder="Enter URL B..."
            className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
          />
        </div>
      </div>

      <div className="mb-6">
        <button
          type="button"
          onClick={() => setShowTranscripts(!showTranscripts)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center transition-colors"
        >
          {showTranscripts ? '− Hide Manual Transcripts' : '+ Add Manual Transcripts (Highly Recommended)'}
        </button>
        
        {showTranscripts && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">Transcript A (Required if no URL A)</label>
              <textarea
                value={transcriptA}
                onChange={(e) => setTranscriptA(e.target.value)}
                placeholder="Paste transcript for Video A here..."
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition h-32 resize-none text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">Transcript B (Required if no URL B)</label>
              <textarea
                value={transcriptB}
                onChange={(e) => setTranscriptB(e.target.value)}
                placeholder="Paste transcript for Video B here..."
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition h-32 resize-none text-sm"
              />
            </div>
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading || !isReady}
        className={`w-full py-4 rounded-lg font-bold text-white transition-all ${
          isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-md hover:shadow-lg active:scale-[0.98]'
        }`}
      >
        {isLoading ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processing Transcripts & Metadata...
          </span>
        ) : 'Analyze & Compare'}
      </button>
    </form>
  );
}
