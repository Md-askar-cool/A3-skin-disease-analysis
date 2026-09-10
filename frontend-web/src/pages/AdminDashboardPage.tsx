import React from 'react';
import { BarChart, Users, Activity, Target } from 'lucide-react';

const AdminDashboardPage = () => {
  return (
    <div className="bg-slate-50 min-h-screen py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Admin & Performance Dashboard</h1>
          <p className="text-slate-600">Model performance metrics and aggregate statistics.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard icon={<Target className="text-sky-500" />} title="Model Accuracy" value="94.2%" trend="+1.2%" />
          <MetricCard icon={<Activity className="text-indigo-500" />} title="Total Screenings" value="12,450" trend="+850 this week" />
          <MetricCard icon={<Users className="text-emerald-500" />} title="Active Users" value="3,204" trend="+120 this week" />
          <MetricCard icon={<BarChart className="text-amber-500" />} title="False Positive Rate" value="1.8%" trend="-0.4%" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 h-96 flex flex-col items-center justify-center">
            <h3 className="text-lg font-bold text-slate-900 mb-4 self-start">Screening Results Distribution</h3>
            <p className="text-slate-400">[ Chart Placeholder ]</p>
          </div>
          
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 h-96 flex flex-col items-center justify-center">
            <h3 className="text-lg font-bold text-slate-900 mb-4 self-start">Model Confidence Distribution</h3>
            <p className="text-slate-400">[ Chart Placeholder ]</p>
          </div>
        </div>

      </div>
    </div>
  );
};

const MetricCard = ({ icon, title, value, trend }: any) => (
  <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex items-start gap-4">
    <div className="p-3 bg-slate-50 rounded-xl">
      {icon}
    </div>
    <div>
      <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
      <h3 className="text-2xl font-bold text-slate-900">{value}</h3>
      <p className="text-xs font-medium text-emerald-600 mt-1">{trend}</p>
    </div>
  </div>
);

export default AdminDashboardPage;
