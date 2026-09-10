import React from 'react';
import { motion } from 'framer-motion';
import { Camera, ImageOff, ShieldAlert, Cpu, Percent, BarChart3, FileText, ArrowDown } from 'lucide-react';

const HowItWorksPage = () => {
  const steps = [
    {
      icon: <Camera className="w-8 h-8 text-white" />,
      color: "bg-sky-500",
      title: "STEP 1: Upload Skin Image",
      description: "Take a photo or upload an existing image of the affected skin area."
    },
    {
      icon: <ImageOff className="w-8 h-8 text-white" />,
      color: "bg-indigo-500",
      title: "STEP 2: Image Quality Analysis",
      description: "The AI checks for blur, lighting, and resolution. If the image is poor, you will be asked to upload a clearer one."
    },
    {
      icon: <ShieldAlert className="w-8 h-8 text-white" />,
      color: "bg-emerald-500",
      title: "STEP 3: Healthy vs Potentially Affected",
      description: "A screening model evaluates if there is a clear abnormality or if the skin appears healthy."
    },
    {
      icon: <Cpu className="w-8 h-8 text-white" />,
      color: "bg-violet-500",
      title: "STEP 4: AI Condition Classification",
      description: "If an abnormality is detected, the classifier analyzes the condition against known datasets."
    },
    {
      icon: <Percent className="w-8 h-8 text-white" />,
      color: "bg-amber-500",
      title: "STEP 5: Confidence Analysis",
      description: "The system assesses its own confidence. If it is below a threshold, it returns an 'Uncertain' result rather than guessing."
    },
    {
      icon: <BarChart3 className="w-8 h-8 text-white" />,
      color: "bg-orange-500",
      title: "STEP 6: Severity Assessment",
      description: "Where medically supported, the AI estimates the severity (Mild, Moderate, Severe)."
    },
    {
      icon: <FileText className="w-8 h-8 text-white" />,
      color: "bg-rose-500",
      title: "STEP 7: AI Screening Report",
      description: "A comprehensive report is generated including Grad-CAM visual explanations of what the AI focused on."
    }
  ];

  return (
    <div className="bg-slate-50 min-h-screen py-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-extrabold text-slate-900 mb-4">How SafeSkin AI Works</h1>
          <p className="text-lg text-slate-600">
            Our multi-stage pipeline is designed to maximize accuracy and minimize false positives.
          </p>
        </div>

        <div className="relative">
          {/* Vertical connecting line */}
          <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-1 bg-sky-200 -translate-x-1/2 rounded-full hidden md:block"></div>

          <div className="space-y-12">
            {steps.map((step, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`flex flex-col md:flex-row items-center gap-6 ${index % 2 === 0 ? 'md:flex-row' : 'md:flex-row-reverse'}`}
              >
                {/* Content Box */}
                <div className={`flex-1 w-full md:w-1/2 ${index % 2 === 0 ? 'md:text-right md:pr-12' : 'md:text-left md:pl-12'}`}>
                  <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
                    <h3 className="text-xl font-bold text-slate-900 mb-2">{step.title}</h3>
                    <p className="text-slate-600 leading-relaxed">{step.description}</p>
                  </div>
                </div>

                {/* Center Icon */}
                <div className="relative z-10 shrink-0">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center shadow-lg ${step.color} border-4 border-white`}>
                    {step.icon}
                  </div>
                  {index < steps.length - 1 && (
                    <div className="md:hidden flex justify-center mt-6">
                      <ArrowDown className="text-sky-300 w-6 h-6" />
                    </div>
                  )}
                </div>

                {/* Empty space for alternating layout */}
                <div className="hidden md:block flex-1 w-1/2"></div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HowItWorksPage;
