import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DoctorDashboardScreen extends ConsumerWidget {
  const DoctorDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    return ResponsiveAppShell(
      role: AppRole.doctor,
      child: dashboard.when(
        loading: () => const DashboardLoadingView(),
        error: (error, stackTrace) => DashboardErrorView(
          message: error.toString(),
          onRetry: () => ref.invalidate(dashboardProvider),
        ),
        data: (data) => _DoctorDashboard(data: data),
      ),
    );
  }
}

class _DoctorDashboard extends StatelessWidget {
  const _DoctorDashboard({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context) {
    if (data.data.isEmpty) {
      return const Center(
        child: Text(
          'No synthetic dashboard data is available.',
          key: Key('doctor-empty'),
        ),
      );
    }
    return ColoredBox(
      color: DrAiColors.brandSoft,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final desktop = constraints.maxWidth >= DrAiBreakpoints.desktop;
          return SingleChildScrollView(
            padding: const EdgeInsets.all(DrAiSpacing.xs),
            child: desktop
                ? Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      SizedBox(
                        width: 258,
                        child: _DoctorIdentityColumn(data: data.data),
                      ),
                      const SizedBox(width: DrAiSpacing.xs),
                      Expanded(child: _DoctorMainColumn(data: data.data)),
                      const SizedBox(width: DrAiSpacing.xs),
                      SizedBox(
                        width: 326,
                        child: _DoctorSideColumn(data: data.data),
                      ),
                    ],
                  )
                : Column(
                    children: <Widget>[
                      _DoctorIdentityColumn(data: data.data),
                      const SizedBox(height: DrAiSpacing.xs),
                      _DoctorMainColumn(data: data.data),
                      const SizedBox(height: DrAiSpacing.xs),
                      _DoctorSideColumn(data: data.data),
                    ],
                  ),
          );
        },
      ),
    );
  }
}

class _DoctorIdentityColumn extends StatelessWidget {
  const _DoctorIdentityColumn({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final hospital = Map<String, dynamic>.from(data['hospital'] as Map);
    final doctor = Map<String, dynamic>.from(data['doctor'] as Map);
    final rating = doctor['rating'] as int;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Container(
          height: 300,
          decoration: BoxDecoration(
            color: DrAiColors.ink,
            borderRadius: BorderRadius.circular(DrAiRadii.md),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                height: 120,
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: <Color>[
                      DrAiColors.patientAccent,
                      DrAiColors.accentCyan,
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.vertical(
                    top: Radius.circular(DrAiRadii.md),
                  ),
                ),
                child: const Center(
                  child: Icon(
                    Icons.local_hospital_outlined,
                    size: 64,
                    color: DrAiColors.white,
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(DrAiSpacing.md),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      hospital['name'] as String,
                      style: const TextStyle(color: DrAiColors.white),
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    Text(
                      hospital['location'] as String,
                      style: const TextStyle(
                        color: DrAiColors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    Text(
                      hospital['summary'] as String,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: DrAiColors.outlineMuted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        const _MutedAction(label: 'Edit Hospital Info'),
        const SizedBox(height: DrAiSpacing.sm),
        Container(
          padding: const EdgeInsets.all(DrAiSpacing.md),
          decoration: BoxDecoration(
            color: DrAiColors.ink,
            borderRadius: BorderRadius.circular(DrAiRadii.md),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                children: List<Widget>.generate(
                  5,
                  (index) => Icon(
                    index < rating ? Icons.star : Icons.star_border,
                    color: DrAiColors.white,
                    size: 20,
                  ),
                ),
              ),
              const SizedBox(height: DrAiSpacing.md),
              Text(
                doctor['name'] as String,
                style: const TextStyle(
                  color: DrAiColors.white,
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Text(
                doctor['title'] as String,
                style: const TextStyle(color: DrAiColors.white),
              ),
              const SizedBox(height: DrAiSpacing.lg),
              Row(
                children: <Widget>[
                  const CircleAvatar(
                    backgroundColor: DrAiColors.white,
                    child: Icon(Icons.person, color: DrAiColors.brand),
                  ),
                  const SizedBox(width: DrAiSpacing.sm),
                  Expanded(
                    child: Text(
                      doctor['expertise'] as String,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: DrAiColors.outlineMuted),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        const _MutedAction(label: 'Edit Doctor Info'),
      ],
    );
  }
}

class _DoctorMainColumn extends StatelessWidget {
  const _DoctorMainColumn({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final quickAccess = List<String>.from(data['quick_access'] as List);
    final team = List<String>.from(data['team'] as List);
    return Column(
      children: <Widget>[
        _DoctorPanel(
          title: 'Quick Access',
          icon: Icons.adjust,
          child: GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: MediaQuery.sizeOf(context).width >= 1120 ? 2 : 1,
              childAspectRatio: 2.6,
              crossAxisSpacing: DrAiSpacing.xs,
              mainAxisSpacing: DrAiSpacing.xs,
            ),
            itemCount: quickAccess.length,
            itemBuilder: (context, index) {
              final icons = <IconData>[
                Icons.image_search,
                Icons.medical_information_outlined,
                Icons.document_scanner_outlined,
                Icons.description_outlined,
                Icons.assignment_outlined,
                Icons.monitor_heart_outlined,
                Icons.medical_services_outlined,
              ];
              return Container(
                decoration: BoxDecoration(
                  color: index.isEven
                      ? DrAiColors.m3SurfaceContainerHigh
                      : DrAiColors.patientAccent,
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                  border: Border.all(color: DrAiColors.mutedInk),
                ),
                child: Stack(
                  children: <Widget>[
                    Positioned(
                      right: 12,
                      bottom: 8,
                      child: Icon(
                        icons[index],
                        size: 44,
                        color: DrAiColors.brand.withValues(alpha: 0.22),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.all(DrAiSpacing.md),
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          quickAccess[index],
                          style: const TextStyle(
                            color: DrAiColors.brandDark,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        _DoctorPanel(
          title: 'Team Management',
          icon: Icons.groups_outlined,
          child: Row(
            children: <Widget>[
              for (final member in team)
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(right: DrAiSpacing.xs),
                    child: Container(
                      height: 132,
                      decoration: BoxDecoration(
                        color: DrAiColors.ink,
                        borderRadius: BorderRadius.circular(DrAiRadii.md),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: <Widget>[
                          CircleAvatar(
                            backgroundColor: DrAiColors.white,
                            child: Text(member.split(' ').last.substring(0, 1)),
                          ),
                          const SizedBox(height: DrAiSpacing.md),
                          Text(
                            member,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              color: DrAiColors.white,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              Expanded(
                child: Container(
                  height: 132,
                  decoration: BoxDecoration(
                    color: DrAiColors.ink,
                    borderRadius: BorderRadius.circular(DrAiRadii.md),
                  ),
                  child: const Icon(
                    Icons.add,
                    size: 48,
                    color: DrAiColors.outlineMuted,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _DoctorSideColumn extends StatelessWidget {
  const _DoctorSideColumn({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final activity = Map<String, dynamic>.from(data['recent_activity'] as Map);
    final resources = List<Map<String, dynamic>>.from(
      (data['resources'] as List).map(
        (item) => Map<String, dynamic>.from(item as Map),
      ),
    );
    return Column(
      children: <Widget>[
        _DoctorPanel(
          title: 'Recent Activities',
          icon: Icons.calendar_month_outlined,
          child: Container(
            padding: const EdgeInsets.all(DrAiSpacing.md),
            decoration: BoxDecoration(
              color: DrAiColors.inkStrong,
              borderRadius: BorderRadius.circular(DrAiRadii.lg),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                Text(
                  activity['title'] as String,
                  style: const TextStyle(color: DrAiColors.outlineMuted),
                ),
                const SizedBox(height: DrAiSpacing.lg),
                Text(
                  activity['time'] as String,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: DrAiColors.white,
                    fontSize: 42,
                    fontWeight: FontWeight.w300,
                  ),
                ),
                const SizedBox(height: DrAiSpacing.md),
                const Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: <Widget>[
                    Text(
                      'Cancel',
                      style: TextStyle(color: DrAiColors.patientAccent),
                    ),
                    SizedBox(width: DrAiSpacing.lg),
                    Text(
                      'OK',
                      style: TextStyle(color: DrAiColors.patientAccent),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        _DoctorPanel(
          title: 'Resource Overview',
          icon: Icons.medical_services_outlined,
          child: Column(
            children: <Widget>[
              Container(
                padding: const EdgeInsets.all(DrAiSpacing.md),
                decoration: BoxDecoration(
                  color: DrAiColors.m3SurfaceContainerHigh,
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                ),
                child: Column(
                  children: <Widget>[
                    const Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        'Medical Equipment',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    for (final resource in resources)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2),
                        child: Row(
                          children: <Widget>[
                            Expanded(child: Text(resource['name'] as String)),
                            Text(
                              '${resource['available']}/${resource['total']} Available',
                              style: const TextStyle(fontSize: 12),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
              for (final label in <String>[
                'Medication Stocks',
                'Staffing Levels',
                'Bed Availability',
              ])
                Container(
                  margin: const EdgeInsets.only(bottom: DrAiSpacing.xs),
                  padding: const EdgeInsets.all(DrAiSpacing.md),
                  decoration: BoxDecoration(
                    color: DrAiColors.surfaceSubtle,
                    borderRadius: BorderRadius.circular(DrAiRadii.md),
                    border: Border.all(color: DrAiColors.mutedInk),
                  ),
                  child: Row(
                    children: <Widget>[
                      Expanded(
                        child: Text(
                          label,
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                      ),
                      const Icon(Icons.expand_more),
                    ],
                  ),
                ),
              const Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Read-only synthetic summaries',
                  style: TextStyle(fontSize: 11, color: DrAiColors.mutedInk),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _DoctorPanel extends StatelessWidget {
  const _DoctorPanel({
    required this.title,
    required this.icon,
    required this.child,
  });

  final String title;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Container(
            height: 44,
            padding: const EdgeInsets.symmetric(horizontal: DrAiSpacing.md),
            decoration: const BoxDecoration(
              color: DrAiColors.brand,
              borderRadius: BorderRadius.vertical(
                top: Radius.circular(DrAiRadii.md),
              ),
            ),
            child: Row(
              children: <Widget>[
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      color: DrAiColors.white,
                      fontSize: 20,
                    ),
                  ),
                ),
                Icon(icon, color: DrAiColors.white),
              ],
            ),
          ),
          Padding(padding: const EdgeInsets.all(DrAiSpacing.xs), child: child),
        ],
      ),
    );
  }
}

class _MutedAction extends StatelessWidget {
  const _MutedAction({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 32,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: DrAiColors.inkStrong,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Text(
        label,
        style: const TextStyle(color: DrAiColors.outlineMuted),
      ),
    );
  }
}
