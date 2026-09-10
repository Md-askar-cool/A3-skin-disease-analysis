// ============================================================
// SafeSkin AI – Footer Component
// Professional footer with disclaimer and links
// ============================================================
import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, AlertTriangle, Github, Twitter, Mail } from 'lucide-react';

const currentYear = new Date().getFullYear();

const footerLinks = {
  Product: [
    { label: 'How It Works', href: '/how-it-works' },
    { label: 'Screening', href: '/screening' },
    { label: 'Progress Tracking', href: '/progress' },
    { label: 'History', href: '/history' },
  ],
  Information: [
    { label: 'About SafeSkin AI', href: '/about' },
    { label: 'AI Technology', href: '/about#ai-technology' },
    { label: 'Privacy Policy', href: '/about#privacy' },
    { label: 'Limitations', href: '/about#limitations' },
  ],
  Account: [
    { label: 'Sign In', href: '/login' },
    { label: 'Create Account', href: '/register' },
    { label: 'Forgot Password', href: '/forgot-password' },
  ],
};

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-300 mt-auto">
      {/* ── Medical Disclaimer Banner ─────────────────────────── */}
      <div className="bg-gradient-to-r from-warning-600/90 to-warning-700/90 py-3 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-white text-sm font-medium text-center">
          <AlertTriangle size={16} className="shrink-0" />
          <p>
            <strong>Medical Disclaimer:</strong> SafeSkin AI is not a medical device and does not
            provide medical diagnoses. Always consult a licensed dermatologist for medical advice.
          </p>
        </div>
      </div>

      {/* ── Main footer content ───────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">

          {/* Brand column */}
          <div className="lg:col-span-2">
            <Link to="/" className="flex items-center gap-2.5 mb-4 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-600 flex items-center justify-center shadow-glow">
                <Shield size={18} className="text-white" />
              </div>
              <div>
                <span className="text-lg font-bold text-white block leading-none">
                  SafeSkin AI
                </span>
                <span className="text-xs text-slate-400 tracking-wider uppercase">
                  Skin Screening Assistant
                </span>
              </div>
            </Link>
            <p className="text-sm text-slate-400 leading-relaxed max-w-xs">
              AI-powered skin lesion screening assistance using deep learning.
              Designed to help users track skin health over time — not as a
              replacement for professional medical care.
            </p>

            {/* Social links */}
            <div className="flex items-center gap-3 mt-5">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                aria-label="GitHub"
              >
                <Github size={16} />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                aria-label="Twitter"
              >
                <Twitter size={16} />
              </a>
              <a
                href="mailto:contact@safeskin-ai.app"
                className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                aria-label="Email"
              >
                <Mail size={16} />
              </a>
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                {category}
              </h3>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      to={link.href}
                      className="text-sm text-slate-400 hover:text-primary-400 transition-colors duration-200 hover:underline underline-offset-4"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* ── Bottom bar ────────────────────────────────────────── */}
        <div className="border-t border-slate-800 mt-10 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-500">
            © {currentYear} SafeSkin AI. All rights reserved.
            Built for academic and research purposes only.
          </p>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-success-500 animate-pulse" />
              AI Model Active
            </span>
            <span>v1.0.0</span>
            <span>Not FDA Approved</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
