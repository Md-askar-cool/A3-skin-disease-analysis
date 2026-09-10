import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../screens/splash_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/auth/forgot_password_screen.dart';
import '../screens/home/home_screen.dart';
import '../screens/screening/upload_screen.dart';
import '../screens/screening/quality_result_screen.dart';
import '../screens/screening/result_screen.dart';
import '../screens/history/history_screen.dart';
import '../screens/history/history_detail_screen.dart';
import '../screens/progress/progress_screen.dart';
import '../screens/settings/settings_screen.dart';
import '../providers/auth_provider.dart';

/// GoRouter provider - re-creates router when auth state changes.
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isLoggedIn = authState.valueOrNull?.session != null;
      final isAuthRoute = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register' ||
          state.matchedLocation == '/forgot-password' ||
          state.matchedLocation == '/';

      // Not logged in + trying to access protected route -> login
      if (!isLoggedIn && !isAuthRoute) return '/login';

      // Already logged in + on auth route -> home
      if (isLoggedIn && (state.matchedLocation == '/login' ||
          state.matchedLocation == '/register')) {
        return '/home';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        pageBuilder: (context, state) => _fadeTransition(
          state: state,
          child: const LoginScreen(),
        ),
      ),
      GoRoute(
        path: '/register',
        pageBuilder: (context, state) => _slideTransition(
          state: state,
          child: const RegisterScreen(),
        ),
      ),
      GoRoute(
        path: '/forgot-password',
        pageBuilder: (context, state) => _slideTransition(
          state: state,
          child: const ForgotPasswordScreen(),
        ),
      ),
      GoRoute(
        path: '/home',
        pageBuilder: (context, state) => _fadeTransition(
          state: state,
          child: const HomeScreen(),
        ),
      ),
      GoRoute(
        path: '/screening',
        pageBuilder: (context, state) => _slideTransition(
          state: state,
          child: const UploadScreen(),
        ),
        routes: [
          GoRoute(
            path: 'quality',
            pageBuilder: (context, state) => _slideTransition(
              state: state,
              child: const QualityResultScreen(),
            ),
          ),
          GoRoute(
            path: 'result',
            pageBuilder: (context, state) => _slideTransition(
              state: state,
              child: const ResultScreen(),
            ),
          ),
        ],
      ),
      GoRoute(
        path: '/history',
        pageBuilder: (context, state) => _slideTransition(
          state: state,
          child: const HistoryScreen(),
        ),
        routes: [
          GoRoute(
            path: ':id',
            pageBuilder: (context, state) => _slideTransition(
              state: state,
              child: HistoryDetailScreen(id: state.pathParameters['id']!),
            ),
          ),
        ],
      ),
      GoRoute(
        path: '/progress',
        pageBuilder: (context, state) => _slideTransition(
          state: state,
          child: const ProgressScreen(),
        ),
      ),
      GoRoute(
        path: '/settings',
        pageBuilder: (context, state) => _slideTransition(
          state: state,
          child: const SettingsScreen(),
        ),
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text('Page not found: ${state.error}'),
            TextButton(
              onPressed: () => context.go('/home'),
              child: const Text('Go Home'),
            ),
          ],
        ),
      ),
    ),
  );
});

/// Fade page transition
CustomTransitionPage<void> _fadeTransition({
  required GoRouterState state,
  required Widget child,
}) {
  return CustomTransitionPage<void>(
    key: state.pageKey,
    child: child,
    transitionDuration: const Duration(milliseconds: 350),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      return FadeTransition(opacity: animation, child: child);
    },
  );
}

/// Slide-from-right page transition
CustomTransitionPage<void> _slideTransition({
  required GoRouterState state,
  required Widget child,
}) {
  return CustomTransitionPage<void>(
    key: state.pageKey,
    child: child,
    transitionDuration: const Duration(milliseconds: 300),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      return SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(1.0, 0.0),
          end: Offset.zero,
        ).animate(CurvedAnimation(parent: animation, curve: Curves.easeOut)),
        child: child,
      );
    },
  );
}
