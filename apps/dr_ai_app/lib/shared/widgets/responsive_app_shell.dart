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
          icon: Icon(Icons.menu_book_outlined),
          selectedIcon: Icon(Icons.menu_book),
          label: context.l10n.resources,
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
          icon: Icon(Icons.receipt_long_outlined),
          label: _copy(context, 'Care & costs', '诊疗费用'),
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

  List<NavigationDestination> _payerDestinations(BuildContext context) =>
      <NavigationDestination>[
        NavigationDestination(
          icon: const Icon(Icons.dashboard_outlined),
          selectedIcon: const Icon(Icons.dashboard),
          label: context.l10n.dashboard,
        ),
        NavigationDestination(
          icon: const Icon(Icons.fact_check_outlined),
          label: _copy(context, 'Review queue', '审核队列'),
        ),
        NavigationDestination(
          icon: const Icon(Icons.manage_accounts_outlined),
          label: context.l10n.account,
        ),
      ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final width = MediaQuery.sizeOf(context).width;
    final destinations = switch (role) {
      AppRole.doctor => _doctorDestinations(context),
      AppRole.patient => _patientDestinations(context),
      AppRole.payer => _payerDestinations(context),
      AppRole.unsupported => const <NavigationDestination>[],
    };

    if (width < DrAiBreakpoints.mobile) {
      return Scaffold(
        appBar: _appBar(context),
        body: child,
        bottomNavigationBar: DecoratedBox(
          decoration: const BoxDecoration(
            color: DrAiColors.white,
            border: Border(top: BorderSide(color: DrAiColors.outline)),
          ),
          child: NavigationBarTheme(
            data: _navigationBarTheme(context),
            child: NavigationBar(
              height: role == AppRole.doctor ? 74 : 68,
              backgroundColor: DrAiColors.white,
              surfaceTintColor: Colors.transparent,
              elevation: 0,
              selectedIndex: selectedIndex,
              onDestinationSelected: (index) =>
                  _goToDestination(context, index),
              labelBehavior: role == AppRole.doctor
                  ? NavigationDestinationLabelBehavior.onlyShowSelected
                  : NavigationDestinationLabelBehavior.alwaysShow,
              destinations: destinations,
            ),
          ),
        ),
      );
    }

    if (width < DrAiBreakpoints.desktop || role != AppRole.doctor) {
      return Scaffold(
        body: SafeArea(
          child: Row(
            children: <Widget>[
              DecoratedBox(
                decoration: const BoxDecoration(
                  color: DrAiColors.white,
                  border: Border(right: BorderSide(color: DrAiColors.outline)),
                ),
                child: NavigationRail(
                  backgroundColor: DrAiColors.white,
                  indicatorColor: DrAiColors.brandSoft,
                  selectedIconTheme: const IconThemeData(
                    color: DrAiColors.brand,
                  ),
                  selectedLabelTextStyle: const TextStyle(
                    color: DrAiColors.brand,
                    fontWeight: FontWeight.w700,
                  ),
                  unselectedIconTheme: const IconThemeData(
                    color: DrAiColors.inkSecondary,
                  ),
                  groupAlignment: -0.75,
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
              ),
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
      backgroundColor: DrAiColors.white,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      scrolledUnderElevation: 0,
      leading: const Padding(
        padding: EdgeInsets.all(10),
        child: DrAiBrandMark(size: 32),
      ),
      titleSpacing: 2,
      title: Text(
        context.l10n.appName,
        style: Theme.of(context).textTheme.titleLarge?.copyWith(
          color: DrAiColors.ink,
          fontWeight: FontWeight.w800,
        ),
      ),
      bottom: const PreferredSize(
        preferredSize: Size.fromHeight(1),
        child: Divider(height: 1, color: DrAiColors.outline),
      ),
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
                const Spacer(),
                if (!compact) ...<Widget>[
                  const SizedBox(width: DrAiSpacing.md),
                  Flexible(
                    child: Text(switch (role) {
                      AppRole.doctor => context.l10n.doctorWorkspace,
                      AppRole.patient => context.l10n.patientWorkspace,
                      AppRole.payer => _copy(
                        context,
                        'Payer workspace',
                        '支付方工作台',
                      ),
                      AppRole.unsupported => context.l10n.appName,
                    }, overflow: TextOverflow.ellipsis),
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
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: DrAiColors.white,
        border: Border(bottom: BorderSide(color: DrAiColors.outline)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: DrAiSpacing.md),
        child: Row(
          children: <Widget>[
            const DrAiBrandMark(size: 38),
            const SizedBox(width: DrAiSpacing.xs),
            Text(
              context.l10n.appName,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: DrAiColors.ink,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(width: DrAiSpacing.xl),
            Expanded(
              child: NavigationBarTheme(
                data: _navigationBarTheme(context),
                child: NavigationBar(
                  height: 52,
                  backgroundColor: Colors.transparent,
                  surfaceTintColor: Colors.transparent,
                  elevation: 0,
                  selectedIndex: selectedIndex,
                  onDestinationSelected: (index) =>
                      _goToDestination(context, index),
                  labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
                  destinations: _doctorDestinations(context),
                ),
              ),
            ),
            const SizedBox(width: DrAiSpacing.md),
          ],
        ),
      ),
    );
  }

  NavigationBarThemeData _navigationBarTheme(BuildContext context) {
    return NavigationBarThemeData(
      indicatorColor: DrAiColors.brandSoft,
      iconTheme: WidgetStateProperty.resolveWith<IconThemeData>((states) {
        return IconThemeData(
          color: states.contains(WidgetState.selected)
              ? DrAiColors.brand
              : DrAiColors.inkSecondary,
          size: 22,
        );
      }),
      labelTextStyle: WidgetStateProperty.resolveWith<TextStyle>((states) {
        return (Theme.of(context).textTheme.labelMedium ?? const TextStyle())
            .copyWith(
              color: states.contains(WidgetState.selected)
                  ? DrAiColors.brand
                  : DrAiColors.inkSecondary,
              fontWeight: states.contains(WidgetState.selected)
                  ? FontWeight.w700
                  : FontWeight.w500,
            );
      }),
    );
  }

  void _goToDestination(BuildContext context, int index) {
    if (role == AppRole.doctor) {
      if (index == 1) {
        context.go('/doctor/patients');
        return;
      }
      if (index == 2) {
        context.go('/doctor/resources');
        return;
      }
      if (index == 3) {
        context.go('/doctor/contact');
        return;
      }
      if (index == 4) {
        context.go('/doctor/account');
        return;
      }
      context.go('/doctor');
      return;
    }
    if (role == AppRole.payer) {
      switch (index) {
        case 1:
          context.go('/payer/requests');
        case 2:
          context.go('/payer/account');
        default:
          context.go('/payer');
      }
      return;
    }
    switch (index) {
      case 1:
        context.go('/patient/contact');
      case 2:
        context.go('/patient/care-costs');
      case 3:
        context.go('/patient/recovery-plan');
      case 4:
        context.go('/patient/account');
      default:
        context.go('/patient');
    }
  }
}

String _copy(BuildContext context, String en, String zh) {
  return Localizations.localeOf(context).languageCode == 'zh' ? zh : en;
}
