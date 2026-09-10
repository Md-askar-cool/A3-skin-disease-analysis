import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../services/auth_service.dart';

/// Stream provider that emits Supabase AuthState on every auth event.
/// GoRouter listens to this to redirect on login/logout.
final authStateProvider = StreamProvider<AuthState>((ref) {
  return authService.authStateChanges;
});

/// Provider that exposes the current Supabase User (nullable).
final currentUserProvider = Provider<User?>((ref) {
  return authService.currentUser;
});

/// Provider that exposes the auth service singleton.
final authServiceProvider = Provider<AuthService>((ref) => authService);

/// Simple bool provider: is the user currently authenticated?
final isAuthenticatedProvider = Provider<bool>((ref) {
  final authState = ref.watch(authStateProvider);
  return authState.valueOrNull?.session != null;
});

/// Provider that exposes the user display name
final displayNameProvider = Provider<String>((ref) {
  ref.watch(authStateProvider); // react to auth changes
  return authService.displayName;
});

/// Provider that exposes user initials for avatar
final userInitialsProvider = Provider<String>((ref) {
  ref.watch(authStateProvider);
  return authService.initials;
});
