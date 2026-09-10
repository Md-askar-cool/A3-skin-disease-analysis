import 'package:supabase_flutter/supabase_flutter.dart';

/// SafeSkin AI - Authentication Service
/// Wraps Supabase Auth with typed methods and error handling.
class AuthService {
  final SupabaseClient _client = Supabase.instance.client;

  // ---------- Current User ----------
  User? get currentUser => _client.auth.currentUser;
  Session? get currentSession => _client.auth.currentSession;
  bool get isLoggedIn => currentUser != null;

  /// Stream of auth state changes (login, logout, token refresh)
  Stream<AuthState> get authStateChanges => _client.auth.onAuthStateChange;

  // ---------- Sign In ----------
  Future<AuthResponse> signIn({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _client.auth.signInWithPassword(
        email: email.trim(),
        password: password,
      );
      return response;
    } on AuthException catch (e) {
      throw _mapAuthException(e);
    }
  }

  // ---------- Sign Up ----------
  Future<AuthResponse> signUp({
    required String name,
    required String email,
    required String password,
  }) async {
    try {
      final response = await _client.auth.signUp(
        email: email.trim(),
        password: password,
        data: {'full_name': name.trim()},
      );
      return response;
    } on AuthException catch (e) {
      throw _mapAuthException(e);
    }
  }

  // ---------- Sign Out ----------
  Future<void> signOut() async {
    try {
      await _client.auth.signOut();
    } on AuthException catch (e) {
      throw _mapAuthException(e);
    }
  }

  // ---------- Reset Password ----------
  Future<void> resetPassword(String email) async {
    try {
      await _client.auth.resetPasswordForEmail(email.trim());
    } on AuthException catch (e) {
      throw _mapAuthException(e);
    }
  }

  // ---------- Update Password ----------
  Future<UserResponse> updatePassword(String newPassword) async {
    try {
      return await _client.auth.updateUser(
        UserAttributes(password: newPassword),
      );
    } on AuthException catch (e) {
      throw _mapAuthException(e);
    }
  }

  // ---------- Update Profile ----------
  Future<UserResponse> updateProfile({String? fullName}) async {
    try {
      return await _client.auth.updateUser(
        UserAttributes(
          data: {'full_name': fullName},
        ),
      );
    } on AuthException catch (e) {
      throw _mapAuthException(e);
    }
  }

  // ---------- Delete Account ----------
  Future<void> deleteAccount() async {
    try {
      await _client.rpc('delete_user');
      await _client.auth.signOut();
    } catch (e) {
      throw Exception('Failed to delete account: $e');
    }
  }

  // ---------- Helper ----------
  String _mapAuthException(AuthException e) {
    switch (e.statusCode) {
      case '400':
        return 'Invalid credentials. Please check your email and password.';
      case '422':
        return 'Email already in use. Try logging in instead.';
      case '429':
        return 'Too many attempts. Please wait a moment and try again.';
      default:
        return e.message;
    }
  }

  /// Get user display name from metadata
  String get displayName {
    return currentUser?.userMetadata?['full_name']?.toString() ??
        currentUser?.email?.split('@').first ??
        'User';
  }

  /// Get user avatar initials
  String get initials {
    final name = displayName;
    final parts = name.split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return name.isNotEmpty ? name[0].toUpperCase() : 'U';
  }

  /// Get the current access token for API calls
  String? get accessToken => currentSession?.accessToken;
}

/// Global singleton instance
final authService = AuthService();
