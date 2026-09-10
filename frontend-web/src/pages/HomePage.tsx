import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Activity, Lock, ArrowRight, UploadCloud, CheckCircle, BarChart2 } from 'lucide-react';
import { motion } from 'framer-motion';

const HomePage = () => {
  return (
    <div className="bg-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-sky-50 via-white to-sky-100 pt-16 pb-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sky-100 text-sky-700 font-semibold mb-6">
                <Shield className="w-5 h-5" />
                Privacy-First Health Tech
              </div>
              <h1 className="text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight mb-8">
                Intelligent Skin Condition <br className="hidden md:block" />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-600 to-indigo-600">
                  Screening & Assessment
                </span>
              </h1>
              <p className="text-xl text-slate-600 mb-10 max-w-2xl mx-auto leading-relaxed">
                Upload a skin image and receive an AI-based screening result with confidence-aware predictions. Designed with safety and accuracy in mind.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  to="/screening"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 text-lg font-semibold text-white bg-sky-600 hover:bg-sky-700 rounded-full shadow-lg shadow-sky-200 transition-all hover:scale-105"
                >
                  Start Screening
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  to="/how-it-works"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 text-lg font-semibold text-slate-700 bg-white border-2 border-slate-200 hover:border-sky-200 hover:bg-sky-50 rounded-full transition-all"
                >
                  How It Works
                </Link>
              </div>
            </motion.div>
          </div>
        </div>
        
        {/* Decorative background elements */}
        <div className="absolute top-0 w-full h-full overflow-hidden -z-10 opacity-30">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[60%] rounded-full bg-gradient-to-r from-sky-300 to-indigo-300 blur-[100px]" />
          <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[70%] rounded-full bg-gradient-to-r from-emerald-200 to-sky-300 blur-[120px]" />
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Advanced AI for Peace of Mind</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Our multi-stage AI pipeline ensures high accuracy and protects against false positives.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<UploadCloud className="w-8 h-8 text-sky-500" />}
              title="Image Quality Analysis"
              description="Instantly checks lighting, blur, and resolution to ensure the AI has a clear view before processing."
            />
            <FeatureCard 
              icon={<Activity className="w-8 h-8 text-indigo-500" />}
              title="Confidence-Aware Predictions"
              description="The system won't force a diagnosis if it's unsure. Low-confidence results are clearly marked as 'Uncertain'."
            />
            <FeatureCard 
              icon={<BarChart2 className="w-8 h-8 text-emerald-500" />}
              title="Longitudinal Tracking"
              description="Upload images over time to visually compare changes and track the progress of skin conditions."
            />
          </div>
        </div>
      </section>

      {/* Safety Disclaimer Section */}
      <section className="py-20 bg-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <Lock className="w-12 h-12 text-sky-400 mx-auto mb-6" />
          <h2 className="text-3xl font-bold mb-6">AI Screening ≠ Medical Diagnosis</h2>
          <p className="text-lg text-slate-300 leading-relaxed mb-8">
            SafeSkin AI is an advanced screening tool designed to assist in identifying potential skin conditions. 
            It is <strong>not a replacement for a dermatologist or qualified healthcare professional</strong>. 
            All results should be reviewed by a medical expert.
          </p>
          <div className="inline-flex items-center gap-2 text-emerald-400 bg-emerald-900/30 px-6 py-3 rounded-full border border-emerald-800">
            <CheckCircle className="w-5 h-5" />
            Your data is encrypted and private.
          </div>
        </div>
      </section>
    </div>
  );
};

const FeatureCard = ({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) => (
  <motion.div 
    whileHover={{ y: -5 }}
    className="bg-white p-8 rounded-2xl border border-slate-100 shadow-sm hover:shadow-xl hover:shadow-sky-100 transition-all"
  >
    <div className="bg-sky-50 w-16 h-16 rounded-xl flex items-center justify-center mb-6">
      {icon}
    </div>
    <h3 className="text-xl font-bold text-slate-900 mb-3">{title}</h3>
    <p className="text-slate-600 leading-relaxed">{description}</p>
  </motion.div>
);

export default HomePage;
