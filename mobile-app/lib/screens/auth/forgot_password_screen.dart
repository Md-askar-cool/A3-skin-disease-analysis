import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../core/theme.dart';
import '../../services/auth_service.dart';

/// Forgot password screen - email input + success state.
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _isLoading = false;
  bool _emailSent = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _sendResetEmail() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);

    try {
      await authService.resetPassword(_emailController.text);
      if (mounted) setState(() => _emailSent = true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString()),
            backgroundColor: AppTheme.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Reset Password'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: AppTheme.textPrimary,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: _emailSent ? _buildSuccessState() : _buildInputState(),
        ),
      ),
    );
  }

  Widget _buildInputState() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 24),

        Container(
          width: 72,
          height: 72,
          decoration: BoxDecoration(
            color: AppTheme.primary.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.lock_reset, color: AppTheme.primary, size: 36),
        ).animate().scale(duration: 400.ms, curve: Curves.elasticOut),

        const SizedBox(height: 24),

        Text(
          'Forgot your password?',
          style: Theme.of(context)
              .textTheme
              .headlineSmall
              ?.copyWith(fontWeight: FontWeight.w700),
        ),

        const SizedBox(height: 8),

        Text(
          "No worries! Enter your email and we'll send you a reset link.",
          style: Theme.of(context)
              .textTheme
              .bodyMedium
              ?.copyWith(color: AppTheme.textSecondary),
        ),

        const SizedBox(height: 32),

        Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.done,
                onFieldSubmitted: (_) => _sendResetEmail(),
                decoration: const InputDecoration(
                  labelText: 'Email address',
                  prefixIcon: Icon(Icons.email_outlined),
                ),
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Email is required';
                  if (!v.contains('@')) return 'Enter a valid email';
                  return null;
                },
              ),

              const SizedBox(height: 24),

              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _sendResetEmail,
                  child: _isLoading
                      ? const SizedBox(
                          width: 22,
                          height: 22,
                          child: CircularProgressIndicator(
                              strokeWidth: 2.5, color: Colors.white),
                        )
                      : const Text('Send Reset Link'),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 24),

        Center(
          child: TextButton(
            onPressed: () => context.pop(),
            child: const Text('Back to Sign In'),
          ),
        ),
      ],
    );
  }

  Widget _buildSuccessState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              color: AppTheme.success.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child:
                const Icon(Icons.mark_email_read, color: AppTheme.success, size: 48),
          )
              .animate()
              .scale(duration: 600.ms, curve: Curves.elasticOut)
              .fade(),

          const SizedBox(height: 24),

          Text(
            'Check your inbox!',
            style: Theme.of(context)
                .textTheme
                .headlineSmall
                ?.copyWith(fontWeight: FontWeight.w700),
          ).animate().fadeIn(delay: 300.ms),

          const SizedBox(height: 12),

          Text(
            "We sent a password reset link to\n${_emailController.text}",
            textAlign: TextAlign.center,
            style: Theme.of(context)
                .textTheme
                .bodyMedium
                ?.copyWith(color: AppTheme.textSecondary),
          ).animate().fadeIn(delay: 400.ms),

          const SizedBox(height: 8),

          Text(
            "Check your spam folder if you don't see it.",
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 13, color: AppTheme.textHint),
          ).animate().fadeIn(delay: 500.ms),

          const SizedBox(height: 40),

          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => context.go('/login'),
              child: const Text('Back to Sign In'),
            ),
          ).animate().fadeIn(delay: 600.ms).slideY(begin: 0.2),

          const SizedBox(height: 16),

          TextButton(
            onPressed: () => setState(() => _emailSent = false),
            child: const Text('Try a different email'),
          ).animate().fadeIn(delay: 700.ms),
        ],
      ),
    );
  }
}
