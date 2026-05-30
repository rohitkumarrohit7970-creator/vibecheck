'use client';

interface EngagementChartProps {
  rateA: number;
  rateB: number;
}

export default function EngagementChart({ rateA, rateB }: EngagementChartProps) {
  const max = Math.max(rateA, rateB, 1);
  const widthA = (rateA / max) * 100;
  const widthB = (rateB / max) * 100;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <h3 className="text-sm font-bold text-gray-500 uppercase mb-4 tracking-wider">Engagement Benchmarks</h3>
      <div className="space-y-6">
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">Video A</span>
            <span className="text-sm font-black text-blue-600">{rateA}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-4 overflow-hidden">
            <div 
              className="bg-blue-600 h-full rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${widthA}%` }}
            ></div>
          </div>
        </div>
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">Video B</span>
            <span className="text-sm font-black text-indigo-600">{rateB}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-4 overflow-hidden">
            <div 
              className="bg-indigo-600 h-full rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${widthB}%` }}
            ></div>
          </div>
        </div>
      </div>
      <p className="mt-4 text-xs text-gray-400 italic text-center">
        *Engagement rate = (Likes + Comments) / Views × 100
      </p>
    </div>
  );
}
