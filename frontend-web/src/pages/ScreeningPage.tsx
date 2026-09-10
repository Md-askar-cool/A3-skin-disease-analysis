import React, { useState } from 'react';
import ImageUploader from '../components/screening/ImageUploader';
import QualityReport from '../components/screening/QualityReport';
import ResultCard from '../components/screening/ResultCard';
import ConfidenceGauge from '../components/screening/ConfidenceGauge';
import GradCAMViewer from '../components/screening/GradCAMViewer';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { motion } from 'framer-motion';

// Mock API Call - replace with real API call later
const mockAnalyzeImage = async (file: File) => {
  return new Promise<any>((resolve) => {
    setTimeout(() => {
      resolve({
        image_quality: {
          overall_score: 85,
          status: 'acceptable',
          can_proceed: true,
          message: 'Image is clear enough for analysis.',
          checks: { blur: true, brightness: true, resolution: true }
        },
        screening_result: 'potentially_affected',
        possible_condition: 'Eczema / Atopic Dermatitis',
        confidence: 0.88,
        confidence_level: 'moderate',
        severity_estimate: 'mild',
        gradcam_url: null,
        recommendation: 'This is an AI screening result and not a medical diagnosis.'
      });
    }, 2000);
  });
};

const ScreeningPage = () => {
  const [state, setState] = useState<'upload' | 'analyzing' | 'quality_fail' | 'results'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);

  const handleUpload = (file: File) => {
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setState('analyzing');
    try {
      const data = await mockAnalyzeImage(selectedFile);
      if (data.image_quality.overall_score < 50) {
        setResults(data);
        setState('quality_fail');
      } else {
        setResults(data);
        setState('results');
      }
    } catch (error) {
      console.error(error);
      setState('upload');
    }
  };

  const handleReset = () => {
    setState('upload');
    setSelectedFile(null);
    setPreviewUrl(null);
    setResults(null);
  };

  return (
    <div className="bg-slate-50 min-h-screen py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">AI Skin Screening</h1>
          <p className="text-slate-600">Upload an image for automated analysis.</p>
        </div>

        {/* Disclaimer */}
        <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 mb-8 flex gap-3 items-start">
          <Info className="w-5 h-5 text-sky-600 mt-0.5 shrink-0" />
          <p className="text-sm text-sky-800">
            <strong>Disclaimer:</strong> This application provides AI-based screening results and is not a medical diagnosis. 
            Results should be reviewed by a qualified healthcare professional.
          </p>
        </div>

        {/* Main Content Area */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          
          {/* UPLOAD STATE */}
          {state === 'upload' && (
            <div className="p-8">
              <ImageUploader 
                onFileSelect={handleUpload} 
                preview={previewUrl} 
                onRemove={handleReset} 
              />
              
              {selectedFile && previewUrl && (
                <div className="mt-8 text-center">
                  <p className="text-slate-500 mb-4 text-sm">Your image will be processed for AI-based screening.</p>
                  <button
                    onClick={handleAnalyze}
                    className="bg-sky-600 hover:bg-sky-700 text-white px-8 py-3 rounded-full font-bold shadow-lg shadow-sky-200 transition-all hover:scale-105"
                  >
                    Analyze Image
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ANALYZING STATE */}
          {state === 'analyzing' && (
            <div className="p-16 flex flex-col items-center justify-center text-center">
              <div className="relative w-24 h-24 mb-6">
                <div className="absolute inset-0 border-4 border-slate-100 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-sky-500 rounded-full border-t-transparent animate-spin"></div>
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Analyzing Image...</h2>
              <p className="text-slate-500">Running quality checks and AI models</p>
            </div>
          )}

          {/* QUALITY FAIL STATE */}
          {state === 'quality_fail' && results && (
            <div className="p-8">
              <QualityReport 
                result={results.image_quality} 
                onProceed={() => setState('results')} 
                onRetry={handleReset} 
              />
            </div>
          )}

          {/* RESULTS STATE */}
          {state === 'results' && results && (
            <div className="p-0">
              {/* Quality Banner */}
              <div className="bg-slate-50 p-6 border-b border-slate-200">
                 <QualityReport result={results.image_quality} compact />
              </div>

              <div className="p-8 space-y-6">
                {/* Result Section */}
                {results.screening_result === 'uncertain' || results.confidence < 0.70 ? (
                   <motion.div 
                     initial={{ opacity: 0, scale: 0.95 }}
                     animate={{ opacity: 1, scale: 1 }}
                     className="bg-amber-50 border-2 border-amber-200 rounded-2xl p-8 text-center"
                   >
                     <AlertTriangle className="w-16 h-16 text-amber-500 mx-auto mb-4" />
                     <h2 className="text-3xl font-bold text-amber-900 mb-2">Uncertain Result</h2>
                     <p className="text-lg text-amber-800 mb-6">
                       The AI could not confidently classify this image.
                     </p>
                     <ul className="text-amber-700 text-left max-w-sm mx-auto space-y-2 list-disc pl-5">
                       <li>Try uploading a clearer image</li>
                       <li>Ensure proper lighting</li>
                       <li>Capture the affected area clearly</li>
                       <li>Consider consulting a healthcare professional</li>
                     </ul>
                   </motion.div>
                ) : (
                  <>
                    <div className="grid md:grid-cols-2 gap-6">
                      <ResultCard 
                        title="AI Screening Result" 
                        icon={<CheckCircle />}
                        colorScheme={results.screening_result === 'potentially_affected' ? 'warning' : 'success'}
                      >
                        <div className="flex items-center justify-center h-24">
                          <h2 className="text-2xl font-bold text-slate-800 text-center">
                            {results.screening_result === 'potentially_affected' ? 'Potentially Affected' : 'No Clear Abnormality'}
                          </h2>
                        </div>
                      </ResultCard>
                      
                      {results.possible_condition && (
                        <ResultCard 
                          title="Possible Condition" 
                          icon={<AlertTriangle />}
                          colorScheme="primary"
                        >
                          <div className="flex items-center justify-center h-24">
                            <h2 className="text-2xl font-bold text-slate-800 text-center">
                              {results.possible_condition}
                            </h2>
                          </div>
                        </ResultCard>
                      )}
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                       <ResultCard 
                          title="AI Confidence" 
                          icon={<Info />}
                          colorScheme="neutral"
                       >
                         <div className="flex items-center justify-center h-48 py-4">
                           <ConfidenceGauge confidence={results.confidence} level={results.confidence_level} />
                         </div>
                       </ResultCard>
                       
                       {results.severity_estimate && (
                         <ResultCard 
                           title="Severity Estimate" 
                           icon={<AlertTriangle />}
                           colorScheme="neutral"
                         >
                           <div className="flex items-center justify-center h-48">
                             <h2 className="text-2xl font-bold text-slate-800 text-center uppercase tracking-wider">
                               {results.severity_estimate}
                             </h2>
                           </div>
                         </ResultCard>
                       )}
                    </div>
                    
                    {results.gradcam_url && previewUrl && (
                      <GradCAMViewer originalUrl={previewUrl} heatmapUrl={results.gradcam_url} />
                    )}
                  </>
                )}
                
                <div className="pt-6 mt-6 border-t border-slate-100 flex justify-center gap-4">
                  <button onClick={handleReset} className="px-6 py-2 border border-slate-300 rounded-full font-medium hover:bg-slate-50 transition-colors">
                    Start New Screening
                  </button>
                  <button className="px-6 py-2 bg-sky-600 text-white rounded-full font-medium hover:bg-sky-700 transition-colors">
                    Save to History
                  </button>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default ScreeningPage;
