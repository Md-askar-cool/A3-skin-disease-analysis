import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../core/theme.dart';
import '../../core/constants.dart';
import '../../providers/auth_provider.dart';
import '../../providers/history_provider.dart';
import '../../widgets/common/disclaimer_banner.dart';

/// Home dashboard screen - entry hub of the SafeSkin AI app.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final displayName = ref.watch(displayNameProvider);
    final initials = ref.watch(userInitialsProvider);
    final historyAsync = ref.watch(historyProvider);

    return Scaffold(
      backgroundColor: AppTheme.background,
      body: CustomScrollView(
        slivers: [
          // Custom AppBar
          SliverAppBar(
            expandedHeight: 180,
            floating: false,
            pinned: true,
            backgroundColor: Colors.white,
            surfaceTintColor: Colors.transparent,
            flexibleSpace: FlexibleSpaceBar(
              background: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Color(0xFF0369A1), Color(0xFF0EA5E9)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Good day,',
                                  style: TextStyle(
                                    color: Colors.white.withOpacity(0.8),
                                    fontSize: 14,
                                  ),
                                ),
                                Text(
                                  displayName,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 22,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ],
                            ),
                            GestureDetector(
                              onTap: () => context.push('/settings'),
                              child: CircleAvatar(
                                radius: 24,
                                backgroundColor:
                                    Colors.white.withOpacity(0.25),
                                child: Text(
                                  initials,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w700,
                                    fontSize: 16,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.shield_outlined,
                                  color: Colors.white, size: 16),
                              SizedBox(width: 6),
                              Text(
                                'AI Skin Analysis • Private & Secure',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.notifications_none_outlined),
                onPressed: () {},
                color: AppTheme.textPrimary,
              ),
            ],
          ),

          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Primary action - Start Screening
                  _PrimaryActionCard(
                    onTap: () => context.push('/screening'),
                  ).animate().fadeIn(delay: 100.ms).slideY(begin: 0.1),

                  const SizedBox(height: 20),

                  Text(
                    'Quick Actions',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),

                  const SizedBox(height: 12),

                  // Action grid
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 1.3,
                    children: [
                      _ActionCard(
                        icon: Icons.history,
                        label: 'My History',
                        color: const Color(0xFF6366F1),
                        onTap: () => context.push('/history'),
                      ),
                      _ActionCard(
                        icon: Icons.trending_up,
                        label: 'My Progress',
                        color: const Color(0xFF10B981),
                        onTap: () => context.push('/progress'),
                      ),
                      _ActionCard(
                        icon: Icons.info_outline,
                        label: 'How It Works',
                        color: const Color(0xFFF59E0B),
                        onTap: () => _showHowItWorks(context),
                      ),
                      _ActionCard(
                        icon: Icons.settings_outlined,
                        label: 'Settings',
                        color: const Color(0xFF64748B),
                        onTap: () => context.push('/settings'),
                      ),
                    ]
                        .asMap()
                        .entries
                        .map((e) => e.value
                            .animate()
                            .fadeIn(delay: Duration(milliseconds: 200 + e.key * 80))
                            .slideY(begin: 0.15))
                        .toList(),
                  ),

                  const SizedBox(height: 24),

                  // Recent screenings
                  Text(
                    'Recent Screenings',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),

                  const SizedBox(height: 12),

                  historyAsync.when(
                    loading: () => const _HistoryLoadingShimmer(),
                    error: (_, __) => _EmptyHistoryCard(
                      onTap: () => context.push('/screening'),
                    ),
                    data: (items) => items.isEmpty
                        ? _EmptyHistoryCard(
                            onTap: () => context.push('/screening'))
                        : Column(
                            children: items
                                .take(3)
                                .map((item) => _RecentHistoryTile(item: item,
                                    onTap: () => context.push('/history/${item.id}')))
                                .toList(),
                          ),
                  ),

                  const SizedBox(height: 24),

                  // Disclaimer
                  const DisclaimerBanner(),

                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showHowItWorks(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _HowItWorksSheet(),
    );
  }
}

// ---------- Primary Action Card ----------
class _PrimaryActionCard extends StatelessWidget {
  final VoidCallback onTap;
  const _PrimaryActionCard({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: AppTheme.primaryGradient,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: AppTheme.primary.withOpacity(0.35),
              blurRadius: 20,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Start AI Screening',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Upload or capture a skin image\nfor instant AI analysis',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.85),
                      fontSize: 13,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.camera_alt, color: AppTheme.primary, size: 18),
                        SizedBox(width: 6),
                        Text(
                          'Get Started',
                          style: TextStyle(
                            color: AppTheme.primary,
                            fontWeight: FontWeight.w700,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            const Text('📷', style: TextStyle(fontSize: 64)),
          ],
        ),
      ),
    );
  }
}

// ---------- Action Card ----------
class _ActionCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _ActionCard({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.divider),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.08),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(height: 10),
            Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 13,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------- Recent History Tile ----------
class _RecentHistoryTile extends StatelessWidget {
  final dynamic item;
  final VoidCallback onTap;

  const _RecentHistoryTile({required this.item, required this.onTap});

  Color get _statusColor {
    switch (item.status) {
      case 'healthy': return AppTheme.success;
      case 'affected': return AppTheme.error;
      default: return AppTheme.warning;
    }
  }

  String get _statusLabel {
    switch (item.status) {
      case 'healthy': return 'Healthy';
      case 'affected': return 'Affected';
      default: return 'Uncertain';
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppTheme.divider),
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: _statusColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(Icons.healing_outlined, color: _statusColor, size: 24),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.condition,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${item.confidencePercent}% confidence',
                    style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                  ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: _statusColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                _statusLabel,
                style: TextStyle(
                  color: _statusColor,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------- Empty History Card ----------
class _EmptyHistoryCard extends StatelessWidget {
  final VoidCallback onTap;
  const _EmptyHistoryCard({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.divider),
      ),
      child: Column(
        children: [
          Icon(Icons.science_outlined, size: 48, color: AppTheme.textHint),
          const SizedBox(height: 12),
          Text(
            'No screenings yet',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 4),
          Text(
            'Start your first AI screening today',
            style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
          ),
          const SizedBox(height: 16),
          OutlinedButton(
            onPressed: onTap,
            style: OutlinedButton.styleFrom(
              minimumSize: const Size(160, 40),
            ),
            child: const Text('Start Screening'),
          ),
        ],
      ),
    );
  }
}

// ---------- History Loading Shimmer ----------
class _HistoryLoadingShimmer extends StatelessWidget {
  const _HistoryLoadingShimmer();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(
        2,
        (i) => Container(
          margin: const EdgeInsets.only(bottom: 8),
          height: 72,
          decoration: BoxDecoration(
            color: AppTheme.divider,
            borderRadius: BorderRadius.circular(14),
          ),
        ),
      ),
    );
  }
}

// ---------- How It Works Bottom Sheet ----------
class _HowItWorksSheet extends StatelessWidget {
  const _HowItWorksSheet();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: const EdgeInsets.all(24),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppTheme.divider,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 20),
            Text('How SafeSkin AI Works',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w700)),
            const SizedBox(height: 20),
            ...[
              ('1', Icons.camera_alt_outlined, 'Capture or Upload',
                  'Take a clear photo of the affected skin area or upload from your gallery.'),
              ('2', Icons.verified_outlined, 'Quality Check',
                  'Our AI verifies image quality - resolution, lighting, and focus.'),
              ('3', Icons.psychology_outlined, 'AI Analysis',
                  'Deep learning models trained on thousands of dermatology images analyze your photo.'),
              ('4', Icons.assignment_outlined, 'Get Results',
                  'Receive a detailed report with condition, confidence, and Grad-CAM visualization.'),
            ].map((step) => _StepItem(
                  number: step.$1,
                  icon: step.$2,
                  title: step.$3,
                  desc: step.$4,
                )),
            const SizedBox(height: 20),
            const DisclaimerBanner(),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Got it!'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StepItem extends StatelessWidget {
  final String number;
  final IconData icon;
  final String title;
  final String desc;

  const _StepItem(
      {required this.number,
      required this.icon,
      required this.title,
      required this.desc});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              gradient: AppTheme.primaryGradient,
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(number,
                  style: const TextStyle(
                      color: Colors.white, fontWeight: FontWeight.w700)),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 2),
                Text(desc,
                    style:
                        TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
