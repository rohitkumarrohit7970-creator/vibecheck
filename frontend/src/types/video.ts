export interface VideoMetadata {
  video_id: string;
  platform: 'youtube' | 'instagram';
  url: string;
  title?: string;
  creator?: string;
  follower_count?: number;
  views?: number;
  likes?: number;
  comments?: number;
  hashtags: string[];
  upload_date?: string;
  duration?: number;
  engagement_rate?: number;
  thumbnail_url?: string;
}

export interface ProcessingResponse {
  session_id: string;
  video_a: VideoMetadata;
  video_b: VideoMetadata;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}
