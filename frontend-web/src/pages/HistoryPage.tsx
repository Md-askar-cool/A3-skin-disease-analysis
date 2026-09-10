import React from 'react';
import { Clock, Trash2, Eye, ChevronRight } from 'lucide-react';
import Badge from '../components/ui/Badge';
import { motion } from 'framer-motion';

const HistoryPage = () => {
  // Mock data for display
  const mockHistory = [
    {
      id: '1',
      date: '2023-10-15T14:30:00Z',
      result: 'potentially_affected',
      condition: 'Eczema / Atopic Dermatitis',
      confidence: 0.88,
      severity: 'mild',
      quality: 92
    },
    {
      id: '2',
      date: '2023-09-02T09:15:00Z',
      result: 'uncertain',
      condition: null,
      confidence: 0.45,
      severity: null,
      quality: 60
    },
    {
      id: '3',
      date: '2023-08-20T16:45:00Z',
      result: 'no_clear_abnormality',
      condition: null,
      confidence: 0.95,
      severity: null,
      quality: 89
    }
  ];

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-slate-50 min-h-screen py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="flex items-center gap-3 mb-8">
          <div className="bg-sky-100 p-3 rounded-xl">
            <Clock className="w-6 h-6 text-sky-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Screening History</h1>
            <p className="text-slate-600">Review your past AI screenings.</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="divide-y divide-slate-100">
            {mockHistory.map((item, index) => (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                key={item.id} 
                className="p-6 hover:bg-slate-50 transition-colors flex flex-col sm:flex-row gap-6 items-start sm:items-center justify-between"
              >
                <div className="flex-1 space-y-2">
                  <div className="text-sm font-medium text-slate-500">
                    {formatDate(item.date)}
                  </div>
                  
                  <div className="flex flex-wrap gap-2 items-center">
                    {item.result === 'potentially_affected' && <Badge variant="warning">Potentially Affected</Badge>}
                    {item.result === 'no_clear_abnormality' && <Badge variant="success">No Abnormality Detected</Badge>}
                    {item.result === 'uncertain' && <Badge variant="neutral">Uncertain Result</Badge>}
                    
                    {item.condition && <Badge variant="info">{item.condition}</Badge>}
                  </div>
                  
                  <div className="flex gap-4 text-sm text-slate-600 mt-2">
                    <span>Confidence: {(item.confidence * 100).toFixed(0)}%</span>
                    {item.severity && <span className="capitalize border-l border-slate-300 pl-4">Severity: {item.severity}</span>}
                    <span className="border-l border-slate-300 pl-4">Quality: {item.quality}/100</span>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto">
                  <button className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 border border-slate-200 hover:border-slate-300 hover:bg-slate-100 rounded-lg text-sm font-medium text-slate-700 transition-colors">
                    <Eye className="w-4 h-4" />
                    Details
                  </button>
                  <button className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
          
          {mockHistory.length === 0 && (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Clock className="w-8 h-8 text-slate-400" />
              </div>
              <h3 className="text-lg font-medium text-slate-900 mb-1">No history yet</h3>
              <p className="text-slate-500">You haven't performed any screenings.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HistoryPage;
