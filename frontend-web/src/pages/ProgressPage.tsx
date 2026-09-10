import React from 'react';
import { Activity, Camera, Plus, BarChart2 } from 'lucide-react';

const ProgressPage = () => {
  return (
    <div className="bg-slate-50 min-h-screen py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div className="flex items-center gap-3">
            <div className="bg-emerald-100 p-3 rounded-xl">
              <Activity className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Progress Tracker</h1>
              <p className="text-slate-600">Track visual changes over time.</p>
            </div>
          </div>
          
          <button className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-full font-medium transition-colors shadow-sm">
            <Plus className="w-5 h-5" />
            Add Progress Image
          </button>
        </div>

        {/* Mock empty state for now */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center">
           <div className="w-20 h-20 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-6">
             <Camera className="w-10 h-10 text-emerald-500" />
           </div>
           <h2 className="text-2xl font-bold text-slate-900 mb-2">Start Tracking Your Progress</h2>
           <p className="text-slate-600 max-w-md mx-auto mb-8">
             Upload images periodically to create a timeline of visual changes. Compare before and after images easily.
           </p>
           <button className="bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-full font-medium transition-colors">
             Upload First Image
           </button>
        </div>
      </div>
    </div>
  );
};

export default ProgressPage;
