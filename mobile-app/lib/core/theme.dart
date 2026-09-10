import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// SafeSkin AI App Theme
/// Premium Material 3 theme with custom sky-blue branding.
class AppTheme {
  // ---------- Brand Colors ----------
  static const Color primary = Color(0xFF0EA5E9);       // Sky Blue
  static const Color primaryDark = Color(0xFF0284C7);
  static const Color primaryLight = Color(0xFF38BDF8);
  static const Color secondary = Color(0xFF6366F1);     // Indigo
  static const Color secondaryLight = Color(0xFF818CF8);
  static const Color background = Color(0xFFF0F9FF);    // Light sky tint
  static const Color surface = Color(0xFFFFFFFF);
  static const Color error = Color(0xFFEF4444);
  static const Color warning = Color(0xFFF59E0B);
  static const Color success = Color(0xFF10B981);
  static const Color textPrimary = Color(0xFF0F172A);
  static const Color textSecondary = Color(0xFF64748B);
  static const Color textHint = Color(0xFF94A3B8);
  static const Color divider = Color(0xFFE2E8F0);
  static const Color cardShadow = Color(0x1A0EA5E9);

  // ---------- Result Colors ----------
  static const Color resultAffected = Color(0xFFEF4444);
  static const Color resultHealthy = Color(0xFF10B981);
  static const Color resultUncertain = Color(0xFFF59E0B);
  static const Color resultMild = Color(0xFFF97316);
  static const Color resultModerate = Color(0xFFEF4444);
  static const Color resultSevere = Color(0xFF7F1D1D);

  // ---------- Gradients ----------
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [Color(0xFF0EA5E9), Color(0xFF6366F1)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient backgroundGradient = LinearGradient(
    colors: [Color(0xFFEFF6FF), Color(0xFFF0F9FF)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  // ---------- Light Theme ----------
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.light(
        primary: primary,
        onPrimary: Colors.white,
        primaryContainer: const Color(0xFFE0F2FE),
        onPrimaryContainer: primaryDark,
        secondary: secondary,
        onSecondary: Colors.white,
        secondaryContainer: const Color(0xFFE0E7FF),
        onSecondaryContainer: const Color(0xFF3730A3),
        error: error,
        onError: Colors.white,
        background: background,
        onBackground: textPrimary,
        surface: surface,
        onSurface: textPrimary,
        outline: divider,
        shadow: const Color(0x1A000000),
      ),
      scaffoldBackgroundColor: background,
      textTheme: _buildTextTheme(textPrimary),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: textPrimary,
        elevation: 0,
        shadowColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        centerTitle: false,
        titleTextStyle: GoogleFonts.inter(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        iconTheme: const IconThemeData(color: textPrimary),
      ),
      cardTheme: CardTheme(
        elevation: 0,
        color: surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0xFFE2E8F0), width: 1),
        ),
        margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 0),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          elevation: 0,
          shadowColor: Colors.transparent,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          textStyle: GoogleFonts.inter(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
          minimumSize: const Size(double.infinity, 52),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: primary,
          side: const BorderSide(color: primary, width: 1.5),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          textStyle: GoogleFonts.inter(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
          minimumSize: const Size(double.infinity, 52),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: primary,
          textStyle: GoogleFonts.inter(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFF8FAFC),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFE2E8F0), width: 1.5),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFE2E8F0), width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: error, width: 1.5),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: error, width: 2),
        ),
        labelStyle: GoogleFonts.inter(
          fontSize: 14,
          color: textSecondary,
        ),
        hintStyle: GoogleFonts.inter(
          fontSize: 14,
          color: textHint,
        ),
        errorStyle: GoogleFonts.inter(
          fontSize: 12,
          color: error,
        ),
      ),
      chipTheme: ChipThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        labelStyle: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w500),
      ),
      dividerTheme: const DividerThemeData(
        color: divider,
        thickness: 1,
        space: 1,
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        contentTextStyle: GoogleFonts.inter(fontSize: 14),
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
      ),
      dialogTheme: DialogTheme(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        backgroundColor: Colors.white,
        titleTextStyle: GoogleFonts.inter(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: textPrimary,
        ),
        contentTextStyle: GoogleFonts.inter(
          fontSize: 14,
          color: textSecondary,
        ),
      ),
      listTileTheme: ListTileThemeData(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      ),
    );
  }

  // ---------- Dark Theme ----------
  static ThemeData get darkTheme {
    return lightTheme.copyWith(
      colorScheme: const ColorScheme.dark(
        primary: primary,
        onPrimary: Colors.white,
        secondary: secondary,
        onSecondary: Colors.white,
        error: error,
        background: Color(0xFF0F172A),
        onBackground: Colors.white,
        surface: Color(0xFF1E293B),
        onSurface: Colors.white,
      ),
      scaffoldBackgroundColor: const Color(0xFF0F172A),
    );
  }

  // ---------- Text Theme ----------
  static TextTheme _buildTextTheme(Color color) {
    return TextTheme(
      displayLarge: GoogleFonts.inter(
        fontSize: 32, fontWeight: FontWeight.w700, color: color),
      displayMedium: GoogleFonts.inter(
        fontSize: 28, fontWeight: FontWeight.w700, color: color),
      displaySmall: GoogleFonts.inter(
        fontSize: 24, fontWeight: FontWeight.w600, color: color),
      headlineLarge: GoogleFonts.inter(
        fontSize: 22, fontWeight: FontWeight.w700, color: color),
      headlineMedium: GoogleFonts.inter(
        fontSize: 20, fontWeight: FontWeight.w600, color: color),
      headlineSmall: GoogleFonts.inter(
        fontSize: 18, fontWeight: FontWeight.w600, color: color),
      titleLarge: GoogleFonts.inter(
        fontSize: 16, fontWeight: FontWeight.w600, color: color),
      titleMedium: GoogleFonts.inter(
        fontSize: 14, fontWeight: FontWeight.w600, color: color),
      titleSmall: GoogleFonts.inter(
        fontSize: 12, fontWeight: FontWeight.w600, color: color),
      bodyLarge: GoogleFonts.inter(
        fontSize: 16, fontWeight: FontWeight.w400, color: color),
      bodyMedium: GoogleFonts.inter(
        fontSize: 14, fontWeight: FontWeight.w400, color: color),
      bodySmall: GoogleFonts.inter(
        fontSize: 12, fontWeight: FontWeight.w400, color: color),
      labelLarge: GoogleFonts.inter(
        fontSize: 14, fontWeight: FontWeight.w500, color: color),
      labelMedium: GoogleFonts.inter(
        fontSize: 12, fontWeight: FontWeight.w500, color: color),
      labelSmall: GoogleFonts.inter(
        fontSize: 10, fontWeight: FontWeight.w500, color: color),
    );
  }

  // ---------- Decoration Helpers ----------
  static BoxDecoration get cardDecoration => BoxDecoration(
    color: surface,
    borderRadius: BorderRadius.circular(16),
    border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
    boxShadow: [
      BoxShadow(
        color: cardShadow,
        blurRadius: 12,
        offset: const Offset(0, 4),
      ),
    ],
  );

  static BoxDecoration get glassDecoration => BoxDecoration(
    color: Colors.white.withOpacity(0.85),
    borderRadius: BorderRadius.circular(16),
    border: Border.all(color: Colors.white.withOpacity(0.6), width: 1),
    boxShadow: [
      BoxShadow(
        color: primary.withOpacity(0.1),
        blurRadius: 20,
        offset: const Offset(0, 8),
      ),
    ],
  );
}
