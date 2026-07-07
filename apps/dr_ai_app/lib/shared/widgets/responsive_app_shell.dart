import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/shared/widgets/brand_mark.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class ResponsiveAppShell extends ConsumerWidget {
  const ResponsiveAppShell({
    required this.role,
    required this.child,
    this.selectedIndex = 0,
    super.key,
  });

  final AppRole role;
  final Widget child;
  final int selectedIndex;

  static const doctorDestinations = <NavigationDestination>[
    NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
    NavigationDestination(
      icon: Icon(Icons.science_outlined),
      label: 'AI Diagnostic',
    ),
    NavigationDestination(
      icon: Icon(Icons.monitor_heart_outlined),
      label: 'AI Recovery Plan',
    ),
    NavigationDestination(
      icon: Icon(Icons.medical_services_outlined),
      label: 'Medical Resources',
    ),
    NavigationDestination(
      icon: Icon(Icons.people_outline),
      label: 'Patient Management',
    ),
  ];

  static const patientDestinations = <NavigationDestination>[
    NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
    NavigationDestination(icon: Icon(Icons.phone_outlined), label: 'Contact'),
    NavigationDestination(
      icon: Icon(Icons.medical_services_outlined),
      label: 'Medical Service',
    ),
    NavigationDestination(
      icon: Icon(Icons.assignment_outlined),
      label: 'Recovery Plan',
    ),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final width = MediaQuery.sizeOf(context).width;
    final destinations = role == AppRole.doctor
        ? doctorDestinations
        : patientDestinations;

    if (width < DrAiBreakpoints.mobile) {
      return Scaffold(
        appBar: _appBar(context, ref),
        body: child,
        bottomNavigationBar: role == AppRole.patient
            ? NavigationBar(
                height: 66,
                selectedIndex: selectedIndex,
                onDestinationSelected: (index) =>
                    _goToDestination(context, index),
                labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
                destinations: destinations,
              )
            : null,
      );
    }

    if (width < DrAiBreakpoints.desktop || role == AppRole.patient) {
      return Scaffold(
        body: SafeArea(
          child: Row(
            children: <Widget>[
              NavigationRail(
                selectedIndex: selectedIndex,
                onDestinationSelected: (index) =>
                    _goToDestination(context, index),
                labelType: width >= 760
                    ? NavigationRailLabelType.all
                    : NavigationRailLabelType.selected,
                destinations: destinations
                    .map(
                      (destination) => NavigationRailDestination(
                        icon: destination.icon,
                        selectedIcon: destination.selectedIcon,
                        label: Text(destination.label),
                      ),
                    )
                    .toList(),
              ),
              const VerticalDivider(width: 1),
              Expanded(
                child: Column(
                  children: <Widget>[
                    SizedBox(height: 64, child: _header(context, ref)),
                    Expanded(child: child),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: <Widget>[
            SizedBox(height: 70, child: _doctorDesktopHeader(context, ref)),
            Expanded(child: child),
          ],
        ),
      ),
    );
  }

  AppBar _appBar(BuildContext context, WidgetRef ref) {
    return AppBar(
      leading: const Padding(
        padding: EdgeInsets.all(10),
        child: DrAiBrandMark(size: 32),
      ),
      title: const Text('Dr. AI'),
      actions: <Widget>[
        IconButton(
          key: const Key('logout-button'),
          tooltip: 'Sign out',
          onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          icon: const Icon(Icons.logout),
        ),
      ],
    );
  }

  Widget _header(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).value?.user;
    return ColoredBox(
      color: DrAiColors.white,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 520;
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: DrAiSpacing.md),
            child: Row(
              children: <Widget>[
                const DrAiBrandMark(size: 36),
                if (!compact) ...<Widget>[
                  const SizedBox(width: DrAiSpacing.xs),
                  Text('Dr. AI', style: Theme.of(context).textTheme.titleLarge),
                ],
                if (!compact && role == AppRole.doctor) ...<Widget>[
                  const SizedBox(width: DrAiSpacing.xl),
                  const Expanded(
                    child: SearchBar(
                      hintText: 'Search synthetic patients and resources',
                      leading: Icon(Icons.search),
                    ),
                  ),
                ] else
                  const Spacer(),
                if (!compact) ...<Widget>[
                  const SizedBox(width: DrAiSpacing.md),
                  Flexible(
                    child: Text(
                      user?.displayName ?? '',
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
                IconButton(
                  key: const Key('logout-button'),
                  tooltip: 'Sign out',
                  onPressed: () =>
                      ref.read(authControllerProvider.notifier).logout(),
                  icon: const Icon(Icons.logout),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _doctorDesktopHeader(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).value?.user;
    return ColoredBox(
      color: DrAiColors.white,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: DrAiSpacing.md),
        child: Row(
          children: <Widget>[
            const DrAiBrandMark(size: 38),
            const SizedBox(width: DrAiSpacing.xl),
            const SizedBox(
              width: 280,
              height: 48,
              child: SearchBar(
                hintText:
                    'Search synthetic patients, cases, diagnoses, resources',
                leading: Icon(Icons.search),
              ),
            ),
            const SizedBox(width: DrAiSpacing.xl),
            Expanded(
              child: NavigationBar(
                height: 52,
                selectedIndex: selectedIndex,
                onDestinationSelected: (index) =>
                    _goToDestination(context, index),
                labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
                destinations: doctorDestinations,
              ),
            ),
            const SizedBox(width: DrAiSpacing.md),
            Flexible(
              child: Text(
                user?.displayName ?? '',
                overflow: TextOverflow.ellipsis,
              ),
            ),
            IconButton(
              key: const Key('logout-button'),
              tooltip: 'Sign out',
              onPressed: () =>
                  ref.read(authControllerProvider.notifier).logout(),
              icon: const Icon(Icons.logout),
            ),
          ],
        ),
      ),
    );
  }

  void _goToDestination(BuildContext context, int index) {
    if (role == AppRole.doctor) {
      if (index == 4) {
        context.go('/doctor/patients');
        return;
      }
      context.go('/doctor');
      return;
    }
    context.go('/patient');
  }
}
