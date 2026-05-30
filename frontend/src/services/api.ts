import { ProcessingResponse, VideoMetadata } from '../types/video';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const processVideos = async (
  videoAUrl: string, 
  videoBUrl: string,
  transcriptA?: string,
  transcriptB?: string
): Promise<ProcessingResponse> => {
  const response = await fetch(`${API_BASE_URL}/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      video_a_url: videoAUrl,
      video_b_url: videoBUrl,
      video_a_transcript: transcriptA,
      video_b_transcript: transcriptB,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to process videos');
  }

  return response.json();
};

export const sendMessageStream = async (
  sessionId: string, 
  message: string, 
  onChunk: (chunk: string) => void
): Promise<void> => {
  console.log(`Sending message for session ${sessionId}...`);
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    console.error('Chat error:', error);
    throw new Error(error.detail || 'Failed to send message');
  }

  const reader = response.body?.getReader();
  if (!reader) {
    console.error('No reader available for response body');
    throw new Error('No reader available');
  }

  const decoder = new TextDecoder();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        console.log('Stream finished');
        break;
      }
      const chunk = decoder.decode(value, { stream: true });
      onChunk(chunk);
    }
  } catch (err) {
    console.error('Error reading stream:', err);
    throw err;
  } finally {
    reader.releaseLock();
  }
};
