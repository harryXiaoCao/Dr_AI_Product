import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
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

  List<NavigationDestination> _doctorDestinations(BuildContext context) =>
      <NavigationDestination>[
        NavigationDestination(
          icon: const Icon(Icons.dashboard),
          label: context.l10n.dashboard,
        ),
        NavigationDestination(
          icon: Icon(Icons.people_outline),
          label: context.l10n.patientManagement,
        ),
        NavigationDestination(
          icon: Icon(Icons.chat_bubble_outline),
          label: context.l10n.contacts,
        ),
        NavigationDestination(
          icon: Icon(Icons.manage_accounts_outlined),
          label: context.l10n.account,
        ),
      ];

  List<NavigationDestination> _patientDestinations(BuildContext context) =>
      <NavigationDestination>[
        NavigationDestination(
          icon: Icon(Icons.dashboard),
          label: context.l10n.dashboard,
        ),
        NavigationDestination(
          icon: Icon(Icons.chat_bubble_outline),
          label: context.l10n.contacts,
        ),
        NavigationDestination(
          icon: Icon(Icons.assignment_outlined),
          label: context.l10n.recoveryPlan,
        ),
        NavigationDestination(
          icon: Icon(Icons.manage_accounts_outlined),
          label: context.l10n.myAccount,
        ),
      ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final width = MediaQuery.sizeOf(context).width;
    final destinations = role == AppRole.doctor
        ? _doctorDestinations(context)
        : _patientDestinations(context);

    if (width < DrAiBreakpoints.mobile) {
      return Scaffold(
        appBar: _appBar(context),
        body: child,
        bottomNavigationBar: NavigationBar(
          height: 66,
          selectedIndex: selectedIndex,
          onDestinationSelected: (index) => _goToDestination(context, index),
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
          destinations: destinations,
        ),
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
                    SizedBox(height: 64, child: _header(context)),
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
            SizedBox(height: 70, child: _doctorDesktopHeader(context)),
            Expanded(child: child),
          ],
        ),
      ),
    );
  }

  AppBar _appBar(BuildContext context) {
    return AppBar(
      leading: const Padding(
        padding: EdgeInsets.all(10),
        child: DrAiBrandMark(size: 32),
      ),
      title: Text(context.l10n.appName),
    );
  }

  Widget _header(BuildContext context) {
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
                  Text(
                    context.l10n.appName,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ],
                if (!compact && role == AppRole.doctor) ...<Widget>[
                  const SizedBox(width: DrAiSpacing.xl),
                  Expanded(
                    child: SearchBar(
                      hintText: context.l10n.searchDoctor,
                      leading: const Icon(Icons.search),
                    ),
                  ),
                ] else
                  const Spacer(),
                if (!compact) ...<Widget>[
                  const SizedBox(width: DrAiSpacing.md),
                  Flexible(
                    child: Text(
                      role == AppRole.doctor
                          ? context.l10n.doctorWorkspace
                          : context.l10n.patientWorkspace,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _doctorDesktopHeader(BuildContext context) {
    return ColoredBox(
      color: DrAiColors.white,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: DrAiSpacing.md),
        child: Row(
          children: <Widget>[
            const DrAiBrandMark(size: 38),
            const SizedBox(width: DrAiSpacing.xl),
            SizedBox(
              width: 280,
              height: 48,
              child: SearchBar(
                hintText: context.l10n.searchDoctorWide,
                leading: const Icon(Icons.search),
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
                destinations: _doctorDestinations(context),
              ),
            ),
            const SizedBox(width: DrAiSpacing.md),
          ],
        ),
      ),
    );
  }

  void _goToDestination(BuildContext context, int index) {
    if (role == AppRole.doctor) {
      if (index == 1) {
        context.go('/doctor/patients');
        return;
      }
      if (index == 2) {
        context.go('/doctor/contact');
        return;
      }
      if (index == 3) {
        context.go('/doctor/account');
        return;
      }
      context.go('/doctor');
      return;
    }
    switch (index) {
      case 1:
        context.go('/patient/contact');
      case 2:
        context.go('/patient/recovery-plan');
      case 3:
        context.go('/patient/account');
      default:
        context.go('/patient');
    }
  }
}
