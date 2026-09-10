/// SafeSkin AI - App Constants
/// Centralised configuration for API endpoints, Supabase settings, and thresholds.
class AppConstants {
  AppConstants._();

  // ---------- Supabase ----------
  static const String supabaseUrl = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: 'https://your-project.supabase.co',
  );
  static const String supabaseAnonKey = String.fromEnvironment(
    'SUPABASE_ANON_KEY',
    defaultValue: 'your-anon-key',
  );

  // ---------- API ----------
  static const String apiBaseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://localhost:8000',
  );
  static const String apiVersion = '/api/v1';
  static String get apiUrl => '$apiBaseUrl$apiVersion';

  // ---------- Supabase Storage Buckets ----------
  static const String skinImagesBucket = 'skin-images';
  static const String progressImagesBucket = 'progress-images';
  static const String gradcamBucket = 'gradcam-results';

  // ---------- API Endpoints ----------
  static const String uploadEndpoint = '/upload';
  static const String analyzeEndpoint = '/analyze';
  static const String screeningsEndpoint = '/screenings';
  static const String progressEndpoint = '/progress';
  static const String compareEndpoint = '/progress/compare';

  // ---------- Quality Thresholds ----------
  /// Minimum quality score (0-100) to proceed with AI analysis
  static const double minQualityScore = 60.0;
  /// Threshold for "good quality" classification
  static const double goodQualityScore = 80.0;

  // ---------- Confidence Thresholds ----------
  /// Minimum confidence to show a definitive result
  static const double minConfidenceThreshold = 0.65;
  /// High confidence threshold
  static const double highConfidenceThreshold = 0.85;

  // ---------- File Constraints ----------
  static const int maxImageSizeBytes = 10 * 1024 * 1024; // 10 MB
  static const List<String> allowedImageExtensions = ['jpg', 'jpeg', 'png', 'heic', 'webp'];
  static const int imageCompressionQuality = 85;
  static const int maxImageDimension = 1024;

  // ---------- App Info ----------
  static const String appName = 'SafeSkin AI';
  static const String appVersion = '1.0.0';
  static const String supportEmail = 'support@safeskin.ai';
  static const String privacyPolicyUrl = 'https://safeskin.ai/privacy';
  static const String termsUrl = 'https://safeskin.ai/terms';

  // ---------- Medical Disclaimer ----------
  static const String medicalDisclaimer =
      'SafeSkin AI is an educational and informational tool only. '
      'Results are NOT a medical diagnosis. Always consult a qualified '
      'dermatologist or healthcare professional for any skin concerns.';

  // ---------- Result Labels ----------
  static const String resultAffected = 'Potentially Affected';
  static const String resultHealthy = 'Appears Healthy';
  static const String resultUncertain = 'Uncertain';

  // ---------- Severity Labels ----------
  static const String severityMild = 'Mild';
  static const String severityModerate = 'Moderate';
  static const String severitySevere = 'Severe';
  static const String severityNone = 'None Detected';
}
