import { VideoMetadata } from '../types/video';

interface VideoCardProps {
  video: VideoMetadata;
  label: 'A' | 'B';
}

export default function VideoCard({ video, label }: VideoCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100 transition-hover hover:shadow-lg">
      <div className="relative h-48 w-full bg-gray-200">
        {video.thumbnail_url ? (
          <img 
            src={video.thumbnail_url} 
            alt={video.title} 
            className="w-full h-full object-cover" 
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">No Thumbnail</div>
        )}
        <div className="absolute top-4 left-4 bg-black/70 text-white px-3 py-1 rounded-full text-sm font-bold">
          Video {label}
        </div>
        <div className="absolute bottom-4 right-4 bg-blue-600 text-white px-2 py-1 rounded text-xs font-semibold uppercase">
          {video.platform}
        </div>
      </div>
      
      <div className="p-5">
        <h3 className="font-bold text-lg mb-2 line-clamp-2 min-h-[3.5rem]">{video.title || 'Untitled Video'}</h3>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Creator</span>
            <span className="font-semibold text-gray-800">{video.creator || 'Unknown'}</span>
          </div>
          
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Followers</span>
            <span className="font-semibold text-gray-800">{video.follower_count?.toLocaleString() || 0}</span>
          </div>

          <div className="grid grid-cols-3 gap-2 py-3 border-t border-b border-gray-50">
            <div className="text-center">
              <div className="text-xs text-gray-400 uppercase">Views</div>
              <div className="font-bold text-gray-800">{video.views?.toLocaleString() || 0}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400 uppercase">Likes</div>
              <div className="font-bold text-gray-800">{video.likes?.toLocaleString() || 0}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400 uppercase">Comments</div>
              <div className="font-bold text-gray-800">{video.comments?.toLocaleString() || 0}</div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-sm font-semibold text-gray-600">Engagement Rate</span>
            <span className="text-xl font-black text-blue-600">{video.engagement_rate}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
