import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PatientDashboardScreen extends ConsumerWidget {
  const PatientDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(dashboardProvider);
    return ResponsiveAppShell(
      role: AppRole.patient,
      child: dashboard.when(
        loading: () => const DashboardLoadingView(),
        error: (error, stackTrace) => DashboardErrorView(
          message: error.toString(),
          onRetry: () => ref.invalidate(dashboardProvider),
        ),
        data: (data) => _PatientDashboard(data: data),
      ),
    );
  }
}

class _PatientDashboard extends StatelessWidget {
  const _PatientDashboard({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context) {
    if (data.data.isEmpty) {
      return const Center(
        child: Text(
          'No synthetic dashboard data is available.',
          key: Key('patient-empty'),
        ),
      );
    }
    final recoveryDays = List<Map<String, dynamic>>.from(
      (data.data['recovery_days'] as List).map(
        (item) => Map<String, dynamic>.from(item as Map),
      ),
    );
    final doctor = Map<String, dynamic>.from(data.data['doctor'] as Map);
    final fees = List<Map<String, dynamic>>.from(
      (data.data['fee_items'] as List).map(
        (item) => Map<String, dynamic>.from(item as Map),
      ),
    );
    final hasRecords = (data.data['medical_records'] as List).isNotEmpty;
    final hasImages = (data.data['imaging_results'] as List).isNotEmpty;

    return ColoredBox(
      color: DrAiColors.brandSoft,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: ListView(
            padding: const EdgeInsets.all(6),
            children: <Widget>[
              SizedBox(
                height: 244,
                child: _PatientSection(
                  title: 'Recovery Plan',
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      for (var index = 0; index < recoveryDays.length; index++)
                        Expanded(
                          child: Padding(
                            padding: EdgeInsets.only(
                              right: index == recoveryDays.length - 1 ? 0 : 5,
                            ),
                            child: _RecoveryDay(
                              day: recoveryDays[index],
                              index: index,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 244,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Expanded(
                      child: _PatientSection(
                        title: 'Contact Doctor',
                        child: _ContactDoctor(doctor: doctor),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: _PatientSection(
                        title: 'Medical Fee',
                        child: _MedicalFee(items: fees),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 198,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Expanded(
                      child: _EmptyFeatureCard(
                        title: 'Check Medical Record',
                        icon: Icons.description_outlined,
                        emptyLabel: hasRecords
                            ? 'Synthetic records available'
                            : 'No Medical Records',
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: _EmptyFeatureCard(
                        title: 'Check Imaging Results',
                        icon: Icons.document_scanner_outlined,
                        emptyLabel: hasImages
                            ? 'Synthetic images available'
                            : 'No Imaging Results',
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              const SearchBar(
                hintText: 'Search synthetic dashboard',
                leading: Icon(Icons.search),
              ),
              const SizedBox(height: 4),
              Text(
                data.data['safety_label'] as String,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PatientSection extends StatelessWidget {
  const _PatientSection({required this.title, required this.child});

  final String title;
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
            height: 40,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: DrAiColors.brand,
              borderRadius: BorderRadius.vertical(
                top: Radius.circular(DrAiRadii.md),
              ),
            ),
            child: Text(
              title,
              style: const TextStyle(
                color: DrAiColors.white,
                fontSize: 16,
                height: 1.4,
              ),
            ),
          ),
          Expanded(
            child: Padding(padding: const EdgeInsets.all(5), child: child),
          ),
        ],
      ),
    );
  }
}

class _RecoveryDay extends StatelessWidget {
  const _RecoveryDay({required this.day, required this.index});

  final Map<String, dynamic> day;
  final int index;

  @override
  Widget build(BuildContext context) {
    final tasks = List<String>.from(day['tasks'] as List);
    final colors = <Color>[
      DrAiColors.accentCyan,
      DrAiColors.accentBlue,
      DrAiColors.accentIndigo,
      DrAiColors.accentOrange,
      DrAiColors.accentMint,
    ];
    return Container(
      padding: const EdgeInsets.all(5),
      decoration: BoxDecoration(
        color: DrAiColors.brandDark,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        children: <Widget>[
          Text(
            day['label'] as String,
            style: const TextStyle(
              color: DrAiColors.white,
              fontSize: 20,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 5),
          for (var taskIndex = 0; taskIndex < tasks.length; taskIndex++)
            Expanded(
              child: Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 5),
                padding: const EdgeInsets.symmetric(horizontal: 4),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: colors[(taskIndex + index) % colors.length],
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                ),
                child: Text(
                  tasks[taskIndex],
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: DrAiColors.white,
                    fontSize: 10,
                    height: 1.2,
                  ),
                ),
              ),
            ),
          Container(
            height: 20,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: DrAiColors.patientAccent,
              borderRadius: BorderRadius.circular(DrAiRadii.pill),
            ),
            child: const Text(
              '+  See More',
              style: TextStyle(fontSize: 10, color: DrAiColors.brandDark),
            ),
          ),
        ],
      ),
    );
  }
}

class _ContactDoctor extends StatelessWidget {
  const _ContactDoctor({required this.doctor});

  final Map<String, dynamic> doctor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(DrAiSpacing.xs),
      decoration: BoxDecoration(
        color: DrAiColors.ink,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            doctor['name'] as String,
            style: const TextStyle(
              color: DrAiColors.white,
              fontSize: 18,
              fontWeight: FontWeight.w700,
            ),
          ),
          Text(
            doctor['title'] as String,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: DrAiColors.white),
          ),
          const Spacer(),
          Row(
            children: <Widget>[
              const CircleAvatar(
                radius: 18,
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
    );
  }
}

class _MedicalFee extends StatelessWidget {
  const _MedicalFee({required this.items});

  final List<Map<String, dynamic>> items;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: DrAiColors.brandDark,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        children: <Widget>[
          for (final item in items)
            Expanded(
              child: Row(
                children: <Widget>[
                  Expanded(
                    child: Text(
                      '${item['label']}\n${item['amount']}',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: DrAiColors.white,
                        fontSize: 10,
                        height: 1.15,
                      ),
                    ),
                  ),
                  Checkbox(
                    value: item['selected'] as bool,
                    onChanged: null,
                    side: const BorderSide(color: DrAiColors.patientAccent),
                  ),
                ],
              ),
            ),
          Container(
            height: 28,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: DrAiColors.inkStrong,
              borderRadius: BorderRadius.circular(DrAiRadii.md),
            ),
            child: const Text(
              'Pay Now',
              style: TextStyle(color: DrAiColors.outlineMuted),
            ),
          ),
          const SizedBox(height: 2),
          const Text(
            'Visual placeholder only',
            style: TextStyle(color: DrAiColors.outlineMuted, fontSize: 9),
          ),
        ],
      ),
    );
  }
}

class _EmptyFeatureCard extends StatelessWidget {
  const _EmptyFeatureCard({
    required this.title,
    required this.icon,
    required this.emptyLabel,
  });

  final String title;
  final IconData icon;
  final String emptyLabel;

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
            height: 40,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: DrAiColors.brand,
              borderRadius: BorderRadius.vertical(
                top: Radius.circular(DrAiRadii.md),
              ),
            ),
            child: Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(color: DrAiColors.white),
            ),
          ),
          Expanded(
            child: DecoratedBox(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: <Color>[
                    DrAiColors.surfaceSubtle,
                    DrAiColors.patientAccent,
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.vertical(
                  bottom: Radius.circular(DrAiRadii.md),
                ),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: <Widget>[
                  Icon(icon, size: 50, color: DrAiColors.brand),
                  const SizedBox(height: DrAiSpacing.xs),
                  Text(
                    emptyLabel,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: DrAiColors.black),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
