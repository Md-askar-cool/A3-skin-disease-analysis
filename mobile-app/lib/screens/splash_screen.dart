import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/theme.dart';
import '../providers/auth_provider.dart';

/// Animated splash screen that checks auth state and redirects accordingly.
class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen>
    with TickerProviderStateMixin {
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    // Navigate after 2.5 seconds
    Future.delayed(const Duration(milliseconds: 2500), _navigate);
  }

  void _navigate() {
    if (!mounted) return;
    final isAuth = ref.read(isAuthenticatedProvider);
    context.go(isAuth ? '/home' : '/login');
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0369A1), Color(0xFF0EA5E9), Color(0xFF6366F1)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Animated logo container
                AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) {
                    return Container(
                      width: 120,
                      height: 120,
                      decoration: BoxDecoration(
                        color: Colors.white
                            .withOpacity(0.15 + _pulseController.value * 0.1),
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: Colors.white.withOpacity(0.4),
                          width: 2,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.white
                                .withOpacity(0.1 + _pulseController.value * 0.15),
                            blurRadius: 40,
                            spreadRadius: 10,
                          ),
                        ],
                      ),
                      child: child,
                    );
                  },
                  child: const Center(
                    child: Text(
                      '🩺',
                      style: TextStyle(fontSize: 56),
                    ),
                  ),
                )
                    .animate()
                    .scale(
                      duration: 600.ms,
                      curve: Curves.elasticOut,
                      begin: const Offset(0.5, 0.5),
                    )
                    .fade(duration: 400.ms),

                const SizedBox(height: 32),

                // App name
                const Text(
                  'SafeSkin AI',
                  style: TextStyle(
                    fontSize: 36,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                    letterSpacing: -0.5,
                  ),
                )
                    .animate()
                    .slideY(
                      begin: 0.3,
                      duration: 500.ms,
                      delay: 300.ms,
                      curve: Curves.easeOut,
                    )
                    .fade(duration: 500.ms, delay: 300.ms),

                const SizedBox(height: 8),

                // Subtitle
                Text(
                  'AI-Powered Skin Screening',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w400,
                    color: Colors.white.withOpacity(0.85),
                    letterSpacing: 0.5,
                  ),
                )
                    .animate()
                    .slideY(
                      begin: 0.3,
                      duration: 500.ms,
                      delay: 500.ms,
                      curve: Curves.easeOut,
                    )
                    .fade(duration: 500.ms, delay: 500.ms),

                const SizedBox(height: 80),

                // Loading indicator
                SizedBox(
                  width: 32,
                  height: 32,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.5,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      Colors.white.withOpacity(0.7),
                    ),
                  ),
                )
                    .animate()
                    .fade(duration: 400.ms, delay: 800.ms),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
