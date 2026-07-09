import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/cupertino.dart';
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

class PatientAccountScreen extends ConsumerWidget {
  const PatientAccountScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final care = ref.watch(ownPatientCareProvider);
    return ResponsiveAppShell(
      role: AppRole.patient,
      selectedIndex: 4,
      child: ColoredBox(
        color: DrAiColors.brandSoft,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: care.when(
              loading: () =>
                  const DashboardLoadingView(label: 'Loading your account'),
              error: (error, stackTrace) => DashboardErrorView(
                message: 'Unable to load your account. Try again.',
                onRetry: () => ref.invalidate(ownPatientCareProvider),
              ),
              data: (bundle) => _PatientAccountView(bundle: bundle),
            ),
          ),
        ),
      ),
    );
  }
}

class PatientRecoveryPlanScreen extends ConsumerWidget {
  const PatientRecoveryPlanScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final care = ref.watch(ownPatientCareProvider);
    final today = ref.watch(patientTodayProvider);
    return ResponsiveAppShell(
      role: AppRole.patient,
      selectedIndex: 3,
      child: ColoredBox(
        color: DrAiColors.brandSoft,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: care.when(
              loading: () =>
                  const DashboardLoadingView(label: 'Loading recovery plans'),
              error: (error, stackTrace) => DashboardErrorView(
                message: 'Unable to load recovery plans. Try again.',
                onRetry: () {
                  ref.invalidate(ownPatientCareProvider);
                  ref.invalidate(patientTodayProvider);
                },
              ),
              data: (bundle) => _PatientRecoveryPlanView(
                bundle: bundle,
                today: today,
                onRetry: () {
                  ref.invalidate(ownPatientCareProvider);
                  ref.invalidate(patientTodayProvider);
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class PatientPlaceholderScreen extends StatelessWidget {
  const PatientPlaceholderScreen({
    required this.selectedIndex,
    required this.title,
    super.key,
  });

  final int selectedIndex;
  final String title;

  @override
  Widget build(BuildContext context) {
    return ResponsiveAppShell(
      role: AppRole.patient,
      selectedIndex: selectedIndex,
      child: ColoredBox(
        color: DrAiColors.brandSoft,
        child: Center(
          child: Text(
            'Placeholder',
            key: Key(
              'patient-${title.toLowerCase().replaceAll(' ', '-')}-placeholder',
            ),
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              color: DrAiColors.brandDark,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
      ),
    );
  }
}

class _PatientDashboard extends ConsumerWidget {
  const _PatientDashboard({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final care = ref.watch(ownPatientCareProvider);
    switch (care) {
      case AsyncData(:final value)
          when !value.patient.medicalHistorySetupCompleted:
        return _PatientMedicalSurveyScreen(
          care: care,
          onRetry: () => ref.invalidate(ownPatientCareProvider),
        );
      case AsyncLoading():
        return const DashboardLoadingView(label: 'Loading your profile');
      case AsyncError():
        return DashboardErrorView(
          message: 'Unable to load your profile. Try again.',
          onRetry: () => ref.invalidate(ownPatientCareProvider),
        );
      case _:
        break;
    }
    final dashboardData = _patientDashboardData(data.data);
    final fees = List<Map<String, dynamic>>.from(
      (dashboardData['fee_items'] as List).map(
        (item) => Map<String, dynamic>.from(item as Map),
      ),
    );
    final hasRecords = (dashboardData['medical_records'] as List).isNotEmpty;
    final hasImages = (dashboardData['imaging_results'] as List).isNotEmpty;
    final today = ref.watch(patientTodayProvider);
    final notifications = ref.watch(medicationNotificationShellProvider);
    final textScale = MediaQuery.textScalerOf(context).scale(1);
    final cardScale = textScale.clamp(1.0, 1.6).toDouble();

    return ColoredBox(
      color: DrAiColors.brandSoft,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: ListView(
            key: const Key('patient-dashboard-list'),
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 5),
            children: <Widget>[
              SizedBox(
                height: 420 * cardScale,
                child: _PatientSection(
                  title: 'Today',
                  child: _PatientTodayCard(
                    today: today,
                    care: care,
                    notifications: notifications,
                    onRetry: () {
                      ref.invalidate(patientTodayProvider);
                      ref.invalidate(medicationNotificationShellProvider);
                      ref.invalidate(ownPatientCareProvider);
                    },
                  ),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 180 * cardScale,
                child: _PatientSection(
                  title: 'Medical Fee',
                  child: _MedicalFee(items: fees),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 334 * cardScale,
                child: const _PatientSection(
                  title: 'Ask Dr. AI',
                  child: _EducationalChatCard(),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 118 * cardScale,
                child: _PatientSection(
                  title: 'Care Records',
                  child: _CareRecordStatus(
                    hasRecords: hasRecords,
                    hasImages: hasImages,
                  ),
                ),
              ),
              const SizedBox(height: 6),
              const SearchBar(
                hintText: 'Search your care dashboard',
                leading: Icon(Icons.search),
              ),
              const SizedBox(height: 4),
              Text(
                dashboardData['safety_label'] as String,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 11,
                ),
              ),
              const SizedBox(height: 6),
            ],
          ),
        ),
      ),
    );
  }
}

Map<String, dynamic> _patientDashboardData(Map<String, dynamic> source) {
  if (source.containsKey('recovery_days') &&
      source.containsKey('doctor') &&
      source.containsKey('fee_items')) {
    return source;
  }
  return <String, dynamic>{
    'safety_label': 'Staging environment: do not enter real patient data.',
    'recovery_days': <Map<String, dynamic>>[
      <String, dynamic>{
        'label': 'Today',
        'tasks': <String>[
          'Complete profile setup',
          'Share your patient code',
          'Wait for your doctor to connect',
        ],
      },
      <String, dynamic>{
        'label': 'Next',
        'tasks': <String>[
          'Review your medical history',
          'Confirm contact preferences',
          'Prepare questions for your doctor',
        ],
      },
      <String, dynamic>{
        'label': 'After',
        'tasks': <String>[
          'Follow doctor-created care tasks',
          'Track recovery progress',
          'Check medications and imaging results',
        ],
      },
    ],
    'doctor': <String, dynamic>{
      'name': 'Doctor not connected',
      'title': 'Share patient code',
      'expertise': 'Care details appear after connection.',
    },
    'fee_items': <Map<String, dynamic>>[
      <String, dynamic>{
        'label': 'Consultation',
        'amount': 'Pending',
        'selected': false,
      },
      <String, dynamic>{
        'label': 'Medical record',
        'amount': 'Pending',
        'selected': false,
      },
      <String, dynamic>{
        'label': 'Medication',
        'amount': 'Pending',
        'selected': false,
      },
      <String, dynamic>{
        'label': 'Imaging',
        'amount': 'Pending',
        'selected': false,
      },
    ],
    'medical_records': <Object>[],
    'imaging_results': <Object>[],
    ...source,
  };
}

class _PatientAccountView extends StatelessWidget {
  const _PatientAccountView({required this.bundle});

  final PatientCareBundle bundle;

  @override
  Widget build(BuildContext context) {
    return ListView(
      key: const Key('patient-account-list'),
      padding: const EdgeInsets.all(DrAiSpacing.md),
      children: <Widget>[
        _PatientOnboardingPanel(
          title: 'My Account',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Text(
                bundle.patient.displayName,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: DrAiColors.brandDark,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 4),
              SelectableText(
                'Patient ID: ${bundle.patient.syntheticIdentifier}',
                style: const TextStyle(
                  color: DrAiColors.brand,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: DrAiSpacing.sm),
              _AccountLine(
                label: 'Birth date',
                value: bundle.patient.birthDate,
              ),
              _AccountLine(label: 'Gender', value: bundle.patient.gender),
              _AccountLine(label: 'Phone', value: bundle.patient.contactPhone),
              _AccountLine(
                label: 'Emergency contact',
                value: _compactContact(
                  bundle.patient.emergencyContactName,
                  bundle.patient.emergencyContactPhone,
                ),
              ),
              _AccountLine(
                label: 'Language',
                value: bundle.patient.preferredLanguage,
              ),
              _AccountLine(
                label: 'Contact preference',
                value: bundle.patient.contactPreference,
              ),
              const SizedBox(height: DrAiSpacing.sm),
              FilledButton.icon(
                key: const Key('patient-account-edit-profile-button'),
                onPressed: () => _showPatientSurveyEditor(context, bundle),
                icon: const Icon(Icons.edit_outlined),
                label: const Text('Edit profile and medical history'),
              ),
            ],
          ),
        ),
        const SizedBox(height: DrAiSpacing.md),
        _PatientOnboardingPanel(
          title: 'Clinical Events',
          child: bundle.clinicalEvents.isEmpty
              ? const _EmptyAccountState(
                  icon: Icons.event_note_outlined,
                  text: 'Clinical Events appear after your doctor creates one.',
                )
              : Column(
                  children: <Widget>[
                    for (final event in bundle.clinicalEvents)
                      _AccountListTile(
                        icon: Icons.event_note_outlined,
                        title: event.title,
                        subtitle: event.status,
                      ),
                    const SizedBox(height: DrAiSpacing.xs),
                    _PatientEventUpdatePanel(bundle: bundle),
                  ],
                ),
        ),
        const SizedBox(height: DrAiSpacing.md),
        _PatientOnboardingPanel(
          title: 'Medical History',
          child: Text(
            _patientHistorySummary(bundle),
            key: const Key('patient-account-history-summary'),
          ),
        ),
        const SizedBox(height: DrAiSpacing.md),
        _PatientOnboardingPanel(
          title: 'Medical Records And Imaging',
          child: Column(
            children: <Widget>[
              _AccountCountLine(
                label: 'Medical records',
                count: bundle.records.length,
              ),
              for (final record in bundle.records)
                _AccountListTile(
                  icon: Icons.description_outlined,
                  title: record.title,
                  subtitle: record.category,
                ),
              const SizedBox(height: DrAiSpacing.xs),
              _AccountCountLine(
                label: 'Imaging results',
                count: bundle.imagingAssets.length,
              ),
              for (final image in bundle.imagingAssets)
                _AccountListTile(
                  icon: Icons.document_scanner_outlined,
                  title: image.contentType,
                  subtitle: '${image.uploadStatus} / ${image.reviewStatus}',
                ),
            ],
          ),
        ),
        const SizedBox(height: DrAiSpacing.md),
        _PatientOnboardingPanel(
          title: 'Medications And Prescriptions',
          child: Column(
            children: <Widget>[
              if (bundle.medications.isEmpty)
                const _EmptyAccountState(
                  icon: Icons.medication_outlined,
                  text: 'No medications recorded yet.',
                )
              else
                for (final medication in bundle.medications)
                  _AccountListTile(
                    icon: Icons.medication_outlined,
                    title: medication.name,
                    subtitle: '${medication.dosage} - ${medication.schedule}',
                  ),
              const Divider(height: DrAiSpacing.lg),
              _AccountCountLine(
                label: 'Prescriptions',
                count: bundle.prescriptions.length,
              ),
              _AccountCountLine(
                label: 'Medication reminders',
                count: bundle.medicationReminders.length,
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _showPatientSurveyEditor(
    BuildContext context,
    PatientCareBundle bundle,
  ) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      barrierColor: DrAiColors.black.withValues(alpha: 0.22),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.62,
        maxChildSize: 0.96,
        expand: false,
        builder: (context, _) {
          return ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
            child: _PatientMedicalSurveyScreen(
              care: AsyncData<PatientCareBundle>(bundle),
              onRetry: () {},
            ),
          );
        },
      ),
    );
  }
}

class _AccountLine extends StatelessWidget {
  const _AccountLine({required this.label, required this.value});

  final String label;
  final String? value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: <Widget>[
          SizedBox(
            width: 132,
            child: Text(
              label,
              style: const TextStyle(color: DrAiColors.mutedInk),
            ),
          ),
          Expanded(
            child: Text(
              value == null || value!.trim().isEmpty ? 'Not recorded' : value!,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class _AccountCountLine extends StatelessWidget {
  const _AccountCountLine({required this.label, required this.count});

  final String label;
  final int count;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
      child: Row(
        children: <Widget>[
          Expanded(
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
          Text(
            count.toString(),
            style: const TextStyle(
              color: DrAiColors.brand,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _AccountListTile extends StatelessWidget {
  const _AccountListTile({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: DrAiSpacing.xs),
      padding: const EdgeInsets.all(DrAiSpacing.sm),
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        border: Border.all(color: DrAiColors.outline),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: DrAiColors.brand),
          const SizedBox(width: DrAiSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                Text(
                  subtitle,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: DrAiColors.mutedInk,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyAccountState extends StatelessWidget {
  const _EmptyAccountState({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: DrAiSpacing.sm),
      child: Row(
        children: <Widget>[
          Icon(icon, color: DrAiColors.mutedInk),
          const SizedBox(width: DrAiSpacing.sm),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: DrAiColors.mutedInk),
            ),
          ),
        ],
      ),
    );
  }
}

class _CareRecordStatus extends StatelessWidget {
  const _CareRecordStatus({required this.hasRecords, required this.hasImages});

  final bool hasRecords;
  final bool hasImages;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Expanded(
          child: _CareStatusPill(
            icon: Icons.description_outlined,
            label: 'Records',
            value: hasRecords ? 'Available' : 'None yet',
          ),
        ),
        const SizedBox(width: DrAiSpacing.xs),
        Expanded(
          child: _CareStatusPill(
            icon: Icons.document_scanner_outlined,
            label: 'Imaging',
            value: hasImages ? 'Available' : 'None yet',
          ),
        ),
      ],
    );
  }
}

class _CareStatusPill extends StatelessWidget {
  const _CareStatusPill({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        child: Row(
          children: <Widget>[
            Icon(icon, color: DrAiColors.brand, size: 20),
            const SizedBox(width: DrAiSpacing.xs),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    label,
                    style: const TextStyle(
                      color: DrAiColors.mutedInk,
                      fontSize: 12,
                    ),
                  ),
                  Text(
                    value,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

String _compactContact(String? name, String? phone) {
  final parts = <String>[
    if (name != null && name.trim().isNotEmpty) name.trim(),
    if (phone != null && phone.trim().isNotEmpty) phone.trim(),
  ];
  return parts.isEmpty ? 'Not recorded' : parts.join(' - ');
}

class _PatientRecoveryPlanView extends StatelessWidget {
  const _PatientRecoveryPlanView({
    required this.bundle,
    required this.today,
    required this.onRetry,
  });

  final PatientCareBundle bundle;
  final AsyncValue<PatientTodayData> today;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return ListView(
      key: const Key('patient-recovery-plan-list'),
      padding: const EdgeInsets.all(DrAiSpacing.md),
      children: <Widget>[
        _PatientOnboardingPanel(
          title: 'Recovery Plan',
          child: today.when(
            loading: () =>
                const DashboardLoadingView(label: 'Loading active plan'),
            error: (error, stackTrace) => DashboardErrorView(
              message: 'Unable to load active recovery plan. Try again.',
              onRetry: onRetry,
            ),
            data: (data) {
              if (data.activePlan == null) {
                return const _EmptyAccountState(
                  icon: Icons.assignment_outlined,
                  text:
                      'No active recovery plan yet. Your doctor can approve one from Patient Management.',
                );
              }
              return _PatientRecoveryTasks(data: data);
            },
          ),
        ),
        const SizedBox(height: DrAiSpacing.md),
        _PatientOnboardingPanel(
          title: 'Plan History',
          child: bundle.recoveryPlans.isEmpty
              ? const _EmptyAccountState(
                  icon: Icons.history_outlined,
                  text: 'Recovery plan history will appear here.',
                )
              : Column(
                  children: <Widget>[
                    for (final plan in bundle.recoveryPlans)
                      _AccountListTile(
                        icon: Icons.assignment_outlined,
                        title: plan.title,
                        subtitle:
                            '${plan.status} - ${plan.reviewStatus} - ${plan.progressSummary.completionPercent}% complete',
                      ),
                  ],
                ),
        ),
      ],
    );
  }
}

class _PatientRecoveryTasks extends ConsumerWidget {
  const _PatientRecoveryTasks({required this.data});

  final PatientTodayData data;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final completionState = ref.watch(recoveryTaskCompletionControllerProvider);
    final locallyCompleted = completionState.hasValue
        ? completionState.value ?? const <String>{}
        : const <String>{};
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Text(
          data.activePlan!.title,
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 4),
        Text(
          data.activePlan!.instructions,
          style: const TextStyle(color: DrAiColors.mutedInk),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        Text(
          '${data.progressSummary.completedTaskCount}/${data.progressSummary.taskCount} complete - ${data.progressSummary.completionPercent}%',
          style: const TextStyle(
            color: DrAiColors.brand,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: DrAiSpacing.sm),
        for (final task in data.tasks)
          _TodayTaskTile(
            task: task,
            locallyCompleted: locallyCompleted.contains(task.taskId),
            isPending: completionState.isLoading,
            onChanged: (completed) => ref
                .read(recoveryTaskCompletionControllerProvider.notifier)
                .setCompleted(task.taskId, completed: completed),
          ),
      ],
    );
  }
}

class _PatientMedicalSurveyScreen extends ConsumerStatefulWidget {
  const _PatientMedicalSurveyScreen({
    required this.care,
    required this.onRetry,
  });

  final AsyncValue<PatientCareBundle> care;
  final VoidCallback onRetry;

  @override
  ConsumerState<_PatientMedicalSurveyScreen> createState() =>
      _PatientMedicalSurveyScreenState();
}

class _PatientMedicalSurveyScreenState
    extends ConsumerState<_PatientMedicalSurveyScreen> {
  final _formKey = GlobalKey<FormState>();
  final _displayNameController = TextEditingController();
  final _birthDateController = TextEditingController();
  final _contactPhoneController = TextEditingController();
  final _emergencyNameController = TextEditingController();
  final _emergencyPhoneController = TextEditingController();
  final _heightController = TextEditingController();
  final _weightController = TextEditingController();
  final _systolicController = TextEditingController();
  final _diastolicController = TextEditingController();
  final _allergyLabelController = TextEditingController();
  final _allergyReactionController = TextEditingController();
  final _conditionNameController = TextEditingController();
  final _conditionNotesController = TextEditingController();
  final _heartDetailsController = TextEditingController();
  final _endocrineDetailsController = TextEditingController();
  final _neuroDetailsController = TextEditingController();
  final _digestiveDetailsController = TextEditingController();
  final _respiratoryDetailsController = TextEditingController();
  final _kidneyDetailsController = TextEditingController();
  final _cancerDetailsController = TextEditingController();
  final _currentMedicationsController = TextEditingController();
  final _surgeryHistoryController = TextEditingController();
  final _familyHistoryController = TextEditingController();
  final _lifestyleNotesController = TextEditingController();
  String _gender = 'Unspecified';
  String _bloodType = 'Unknown';
  String _pregnancyStatus = 'Prefer not to say';
  String _preferredLanguage = 'Simplified Chinese';
  String _contactPreference = 'Phone';
  String _smokingStatus = 'Never';
  String _alcoholConsumption = 'None or rare';
  bool _hasAllergies = false;
  bool _hasChronicCondition = false;
  bool _hasHeartIssue = false;
  bool _hasEndocrineIssue = false;
  bool _hasNeuroIssue = false;
  bool _hasDigestiveIssue = false;
  bool _hasRespiratoryIssue = false;
  bool _hasKidneyIssue = false;
  bool _hasCancerIssue = false;
  bool _seededFromBundle = false;

  @override
  void dispose() {
    _displayNameController.dispose();
    _birthDateController.dispose();
    _contactPhoneController.dispose();
    _emergencyNameController.dispose();
    _emergencyPhoneController.dispose();
    _heightController.dispose();
    _weightController.dispose();
    _systolicController.dispose();
    _diastolicController.dispose();
    _allergyLabelController.dispose();
    _allergyReactionController.dispose();
    _conditionNameController.dispose();
    _conditionNotesController.dispose();
    _heartDetailsController.dispose();
    _endocrineDetailsController.dispose();
    _neuroDetailsController.dispose();
    _digestiveDetailsController.dispose();
    _respiratoryDetailsController.dispose();
    _kidneyDetailsController.dispose();
    _cancerDetailsController.dispose();
    _currentMedicationsController.dispose();
    _surgeryHistoryController.dispose();
    _familyHistoryController.dispose();
    _lifestyleNotesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final onboardingState = ref.watch(patientOnboardingControllerProvider);
    return ColoredBox(
      color: DrAiColors.brandSoft,
      child: LayoutBuilder(
        builder: (context, constraints) {
          return Center(
            child: SizedBox(
              height: constraints.maxHeight,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 640),
                child: ListView(
                  key: const Key('patient-onboarding-list'),
                  padding: const EdgeInsets.all(DrAiSpacing.md),
                  children: <Widget>[
                    _PatientOnboardingPanel(
                      title: 'Complete your profile',
                      child: widget.care.when(
                        loading: () => const DashboardLoadingView(
                          label: 'Loading your profile',
                        ),
                        error: (error, stackTrace) => DashboardErrorView(
                          message: 'Unable to load your profile. Try again.',
                          onRetry: widget.onRetry,
                        ),
                        data: (bundle) {
                          _seedFields(bundle.patient);
                          return _surveyForm(context, bundle, onboardingState);
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  void _seedFields(PatientProfile patient) {
    if (_seededFromBundle) {
      return;
    }
    _seededFromBundle = true;
    _displayNameController.text = patient.displayName == 'New Patient'
        ? ''
        : patient.displayName;
    _birthDateController.text = patient.birthDate ?? '';
    _contactPhoneController.text = patient.contactPhone ?? '';
    _emergencyNameController.text = patient.emergencyContactName ?? '';
    _emergencyPhoneController.text = patient.emergencyContactPhone ?? '';
    final savedGender = patient.gender ?? patient.sex;
    _gender =
        savedGender == null || savedGender.toLowerCase() == 'not specified'
        ? 'Unspecified'
        : savedGender;
    _preferredLanguage = _knownOption(patient.preferredLanguage, <String>[
      'Simplified Chinese',
      'English',
    ], _preferredLanguage);
    _contactPreference = _knownOption(patient.contactPreference, <String>[
      'Phone',
      'In-app',
      'Email',
    ], _contactPreference);
  }

  Widget _surveyForm(
    BuildContext context,
    PatientCareBundle bundle,
    AsyncValue<void> onboardingState,
  ) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          DecoratedBox(
            decoration: BoxDecoration(
              color: DrAiColors.brandSoft,
              borderRadius: BorderRadius.circular(DrAiRadii.md),
            ),
            child: Padding(
              padding: const EdgeInsets.all(DrAiSpacing.md),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const Text(
                    'Medical intake',
                    style: TextStyle(
                      color: DrAiColors.brandDark,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Complete this once so your care team can review your profile before the first Clinical Event.',
                    style: TextStyle(color: DrAiColors.mutedInk),
                  ),
                  const SizedBox(height: DrAiSpacing.xs),
                  SelectableText(
                    'Patient ID: ${bundle.patient.syntheticIdentifier}',
                    key: const Key('patient-onboarding-code'),
                    style: const TextStyle(
                      color: DrAiColors.brand,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: DrAiSpacing.md),
          _requiredTextField(
            controller: _displayNameController,
            label: 'First and last name',
            keyName: 'onboarding-name-field',
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(child: _birthDateField()),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-gender-field'),
                  initialValue: _gender,
                  isExpanded: true,
                  menuMaxHeight: _menuMaxHeight,
                  borderRadius: _menuBorderRadius,
                  dropdownColor: DrAiColors.white,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded),
                  style: _menuTextStyle,
                  decoration: const InputDecoration(
                    labelText: 'Gender',
                    border: OutlineInputBorder(),
                  ),
                  items: _optionItems(<String>[
                    'Unspecified',
                    'Female',
                    'Male',
                    'Other',
                  ]),
                  onChanged: (value) =>
                      setState(() => _gender = value ?? _gender),
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          _optionalTextField(
            controller: _contactPhoneController,
            label: 'Phone number',
            keyName: 'onboarding-phone-field',
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(
                child: _optionalTextField(
                  controller: _emergencyNameController,
                  label: 'Emergency contact',
                  keyName: 'onboarding-emergency-name-field',
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: _optionalTextField(
                  controller: _emergencyPhoneController,
                  label: 'Emergency phone',
                  keyName: 'onboarding-emergency-phone-field',
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-language-field'),
                  initialValue: _preferredLanguage,
                  isExpanded: true,
                  menuMaxHeight: _menuMaxHeight,
                  borderRadius: _menuBorderRadius,
                  dropdownColor: DrAiColors.white,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded),
                  style: _menuTextStyle,
                  decoration: const InputDecoration(
                    labelText: 'Preferred language',
                    border: OutlineInputBorder(),
                  ),
                  items: _optionItems(<String>[
                    'Simplified Chinese',
                    'English',
                  ]),
                  onChanged: (value) => setState(
                    () => _preferredLanguage = value ?? _preferredLanguage,
                  ),
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-contact-preference-field'),
                  initialValue: _contactPreference,
                  isExpanded: true,
                  menuMaxHeight: _menuMaxHeight,
                  borderRadius: _menuBorderRadius,
                  dropdownColor: DrAiColors.white,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded),
                  style: _menuTextStyle,
                  decoration: const InputDecoration(
                    labelText: 'Contact preference',
                    border: OutlineInputBorder(),
                  ),
                  items: _optionItems(<String>['Phone', 'In-app', 'Email']),
                  onChanged: (value) => setState(
                    () => _contactPreference = value ?? _contactPreference,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(
                child: _decimalTextField(
                  controller: _heightController,
                  label: 'Height (cm)',
                  keyName: 'onboarding-height-field',
                  required: true,
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: _decimalTextField(
                  controller: _weightController,
                  label: 'Weight (kg)',
                  keyName: 'onboarding-weight-field',
                  required: true,
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          DropdownButtonFormField<String>(
            key: const Key('onboarding-blood-type-field'),
            initialValue: _bloodType,
            isExpanded: true,
            menuMaxHeight: _menuMaxHeight,
            borderRadius: _menuBorderRadius,
            dropdownColor: DrAiColors.white,
            icon: const Icon(Icons.keyboard_arrow_down_rounded),
            style: _menuTextStyle,
            decoration: const InputDecoration(
              labelText: 'Blood type',
              border: OutlineInputBorder(),
            ),
            items: _optionItems(<String>[
              'Unknown',
              'A+',
              'A-',
              'B+',
              'B-',
              'AB+',
              'AB-',
              'O+',
              'O-',
            ]),
            onChanged: (value) =>
                setState(() => _bloodType = value ?? _bloodType),
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(
                child: _decimalTextField(
                  controller: _systolicController,
                  label: 'Systolic BP',
                  keyName: 'onboarding-systolic-field',
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: _decimalTextField(
                  controller: _diastolicController,
                  label: 'Diastolic BP',
                  keyName: 'onboarding-diastolic-field',
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Row(
            children: <Widget>[
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-smoking-field'),
                  initialValue: _smokingStatus,
                  isExpanded: true,
                  menuMaxHeight: _menuMaxHeight,
                  borderRadius: _menuBorderRadius,
                  dropdownColor: DrAiColors.white,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded),
                  style: _menuTextStyle,
                  decoration: const InputDecoration(
                    labelText: 'Smoking status',
                    border: OutlineInputBorder(),
                  ),
                  items: _optionItems(<String>['Never', 'Former', 'Current']),
                  onChanged: (value) =>
                      setState(() => _smokingStatus = value ?? _smokingStatus),
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-alcohol-field'),
                  initialValue: _alcoholConsumption,
                  isExpanded: true,
                  menuMaxHeight: _menuMaxHeight,
                  borderRadius: _menuBorderRadius,
                  dropdownColor: DrAiColors.white,
                  icon: const Icon(Icons.keyboard_arrow_down_rounded),
                  style: _menuTextStyle,
                  decoration: const InputDecoration(
                    labelText: 'Alcohol',
                    border: OutlineInputBorder(),
                  ),
                  items: _optionItems(<String>[
                    'None or rare',
                    'Occasional',
                    'Weekly',
                    'Daily',
                  ]),
                  onChanged: (value) => setState(
                    () => _alcoholConsumption = value ?? _alcoholConsumption,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.md),
          Material(
            color: DrAiColors.white,
            child: SwitchListTile(
              key: const Key('onboarding-allergy-switch'),
              contentPadding: EdgeInsets.zero,
              title: const Text('Do you have any allergies?'),
              value: _hasAllergies,
              onChanged: (value) => setState(() => _hasAllergies = value),
            ),
          ),
          if (_hasAllergies) ...<Widget>[
            _requiredTextField(
              controller: _allergyLabelController,
              label: 'Allergy',
              keyName: 'onboarding-allergy-field',
            ),
            const SizedBox(height: DrAiSpacing.sm),
            _optionalTextField(
              controller: _allergyReactionController,
              label: 'Reaction',
              keyName: 'onboarding-allergy-reaction-field',
            ),
          ],
          Material(
            color: DrAiColors.white,
            child: SwitchListTile(
              key: const Key('onboarding-chronic-switch'),
              contentPadding: EdgeInsets.zero,
              title: const Text(
                'Do you have hereditary or long-term medical conditions?',
              ),
              value: _hasChronicCondition,
              onChanged: (value) =>
                  setState(() => _hasChronicCondition = value),
            ),
          ),
          if (_hasChronicCondition) ...<Widget>[
            _requiredTextField(
              controller: _conditionNameController,
              label: 'Condition',
              keyName: 'onboarding-condition-field',
            ),
            const SizedBox(height: DrAiSpacing.sm),
            _optionalTextField(
              controller: _conditionNotesController,
              label: 'Notes',
              keyName: 'onboarding-condition-notes-field',
            ),
          ],
          const SizedBox(height: DrAiSpacing.md),
          _conditionQuestion(
            keyName: 'onboarding-heart-switch',
            title: 'Heart or blood vessel history',
            detail:
                'Heart attack, stroke, irregular heartbeat, blood clots, or heart failure.',
            value: _hasHeartIssue,
            onChanged: (value) => setState(() => _hasHeartIssue = value),
            controller: _heartDetailsController,
            fieldKey: 'onboarding-heart-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-endocrine-switch',
            title: 'Diabetes, thyroid, or bone health',
            detail:
                'Diabetes including gestational diabetes, thyroid disorders, or osteoporosis.',
            value: _hasEndocrineIssue,
            onChanged: (value) => setState(() => _hasEndocrineIssue = value),
            controller: _endocrineDetailsController,
            fieldKey: 'onboarding-endocrine-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-neuro-switch',
            title: 'Brain, mood, or nervous system',
            detail:
                'Depression, severe anxiety, seizures, epilepsy, bipolar disorder, or chronic migraines.',
            value: _hasNeuroIssue,
            onChanged: (value) => setState(() => _hasNeuroIssue = value),
            controller: _neuroDetailsController,
            fieldKey: 'onboarding-neuro-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-digestive-switch',
            title: 'Stomach, bowel, or liver history',
            detail:
                'Ulcers, Crohn disease, ulcerative colitis, irritable bowel disease, hepatitis, or cirrhosis.',
            value: _hasDigestiveIssue,
            onChanged: (value) => setState(() => _hasDigestiveIssue = value),
            controller: _digestiveDetailsController,
            fieldKey: 'onboarding-digestive-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-respiratory-switch',
            title: 'Lung or breathing history',
            detail:
                'Asthma, COPD, emphysema, or severe pneumonia requiring hospitalization.',
            value: _hasRespiratoryIssue,
            onChanged: (value) => setState(() => _hasRespiratoryIssue = value),
            controller: _respiratoryDetailsController,
            fieldKey: 'onboarding-respiratory-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-kidney-switch',
            title: 'Kidney or urinary history',
            detail:
                'Chronic kidney disease, reduced kidney function, or severe kidney stones.',
            value: _hasKidneyIssue,
            onChanged: (value) => setState(() => _hasKidneyIssue = value),
            controller: _kidneyDetailsController,
            fieldKey: 'onboarding-kidney-details-field',
          ),
          _conditionQuestion(
            keyName: 'onboarding-cancer-switch',
            title: 'Cancer or active treatment',
            detail:
                'Any cancer including skin cancer, chemotherapy, radiation, or immunotherapy.',
            value: _hasCancerIssue,
            onChanged: (value) => setState(() => _hasCancerIssue = value),
            controller: _cancerDetailsController,
            fieldKey: 'onboarding-cancer-details-field',
          ),
          const SizedBox(height: DrAiSpacing.md),
          _optionalTextField(
            controller: _currentMedicationsController,
            label: 'Current medications and supplements',
            keyName: 'onboarding-current-medications-field',
            maxLines: 3,
          ),
          const SizedBox(height: DrAiSpacing.md),
          _optionalTextField(
            controller: _surgeryHistoryController,
            label: 'Past surgeries or hospitalizations',
            keyName: 'onboarding-surgery-history-field',
            maxLines: 3,
          ),
          const SizedBox(height: DrAiSpacing.md),
          _optionalTextField(
            controller: _familyHistoryController,
            label: 'Family medical history',
            keyName: 'onboarding-family-history-field',
            maxLines: 3,
          ),
          const SizedBox(height: DrAiSpacing.md),
          _optionalTextField(
            controller: _lifestyleNotesController,
            label: 'Smoking, alcohol, exercise, sleep',
            keyName: 'onboarding-lifestyle-field',
            maxLines: 3,
          ),
          const SizedBox(height: DrAiSpacing.md),
          DropdownButtonFormField<String>(
            key: const Key('onboarding-pregnancy-field'),
            initialValue: _pregnancyStatus,
            isExpanded: true,
            menuMaxHeight: _menuMaxHeight,
            borderRadius: _menuBorderRadius,
            dropdownColor: DrAiColors.white,
            icon: const Icon(Icons.keyboard_arrow_down_rounded),
            style: _menuTextStyle,
            decoration: const InputDecoration(
              labelText: 'Pregnancy status',
              border: OutlineInputBorder(),
            ),
            items: _optionItems(<String>[
              'Prefer not to say',
              'Not applicable',
              'No',
              'Yes',
              'Unsure',
            ]),
            onChanged: (value) =>
                setState(() => _pregnancyStatus = value ?? _pregnancyStatus),
          ),
          if (onboardingState.hasError) ...<Widget>[
            const SizedBox(height: DrAiSpacing.sm),
            const Text(
              'Unable to save your profile. Check the form and try again.',
              key: Key('patient-onboarding-error'),
              style: TextStyle(color: DrAiColors.danger),
            ),
          ],
          const SizedBox(height: DrAiSpacing.md),
          FilledButton.icon(
            key: const Key('patient-onboarding-submit'),
            onPressed: onboardingState.isLoading
                ? null
                : () => _submit(bundle.patient.patientId),
            icon: onboardingState.isLoading
                ? const SizedBox.square(
                    dimension: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: DrAiColors.white,
                    ),
                  )
                : const Icon(Icons.check_circle_outline),
            label: const Text('Finish setup'),
          ),
        ],
      ),
    );
  }

  void _submit(String patientId) {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    ref
        .read(patientOnboardingControllerProvider.notifier)
        .complete(
          patientId: patientId,
          displayName: _displayNameController.text,
          birthDate: _birthDateController.text,
          gender: _gender,
          contactPhone: _contactPhoneController.text,
          emergencyContactName: _emergencyNameController.text,
          emergencyContactPhone: _emergencyPhoneController.text,
          preferredLanguage: _preferredLanguage,
          contactPreference: _contactPreference,
          hasAllergies: _hasAllergies,
          allergyLabel: _allergyLabelController.text,
          allergyReaction: _allergyReactionController.text,
          hasChronicCondition: _hasChronicCondition,
          chronicConditionName: _conditionNameController.text,
          chronicConditionNotes: _conditionNotesController.text,
          heightCm: _heightController.text,
          weightKg: _weightController.text,
          bloodType: _bloodType,
          systolicBloodPressure: _systolicController.text,
          diastolicBloodPressure: _diastolicController.text,
          smokingStatus: _smokingStatus,
          alcoholConsumption: _alcoholConsumption,
          conditionDetails: <String, String>{
            if (_hasHeartIssue)
              'Heart or blood vessel history': _conditionDetail(
                _heartDetailsController,
              ),
            if (_hasEndocrineIssue)
              'Diabetes, thyroid, or bone health': _conditionDetail(
                _endocrineDetailsController,
              ),
            if (_hasNeuroIssue)
              'Brain, mood, or nervous system': _conditionDetail(
                _neuroDetailsController,
              ),
            if (_hasDigestiveIssue)
              'Stomach, bowel, or liver history': _conditionDetail(
                _digestiveDetailsController,
              ),
            if (_hasRespiratoryIssue)
              'Lung or breathing history': _conditionDetail(
                _respiratoryDetailsController,
              ),
            if (_hasKidneyIssue)
              'Kidney or urinary history': _conditionDetail(
                _kidneyDetailsController,
              ),
            if (_hasCancerIssue)
              'Cancer or active treatment': _conditionDetail(
                _cancerDetailsController,
              ),
          },
          currentMedications: _currentMedicationsController.text,
          surgeryHistory: _surgeryHistoryController.text,
          familyHistory: _familyHistoryController.text,
          lifestyleNotes: _lifestyleNotesController.text,
          pregnancyStatus: _pregnancyStatus,
        );
  }

  String _conditionDetail(TextEditingController controller) {
    final text = controller.text.trim();
    return text.isEmpty ? 'Yes' : text;
  }

  Widget _requiredTextField({
    required TextEditingController controller,
    required String label,
    required String keyName,
  }) {
    return _optionalTextField(
      controller: controller,
      label: label,
      keyName: keyName,
      validator: (value) {
        if ((value?.trim() ?? '').length < 2) {
          return 'Required.';
        }
        return null;
      },
    );
  }

  Widget _decimalTextField({
    required TextEditingController controller,
    required String label,
    required String keyName,
    bool required = false,
  }) {
    return TextFormField(
      key: Key(keyName),
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
      ),
      validator: (value) {
        final text = value?.trim() ?? '';
        if (required && text.isEmpty) {
          return 'Required.';
        }
        if (text.isNotEmpty && double.tryParse(text) == null) {
          return 'Use numbers only.';
        }
        return null;
      },
    );
  }

  Widget _conditionQuestion({
    required String keyName,
    required String title,
    required String detail,
    required bool value,
    required ValueChanged<bool> onChanged,
    required TextEditingController controller,
    required String fieldKey,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.sm),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: DrAiColors.surfaceSubtle,
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          border: Border.all(color: DrAiColors.outline),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: DrAiSpacing.xs),
          child: Column(
            children: <Widget>[
              Material(
                color: Colors.transparent,
                child: SwitchListTile(
                  key: Key(keyName),
                  contentPadding: EdgeInsets.zero,
                  title: Text(
                    title,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text(detail),
                  value: value,
                  onChanged: onChanged,
                ),
              ),
              if (value) ...<Widget>[
                _optionalTextField(
                  controller: controller,
                  label: 'Add diagnosis, date, treatment, or current status',
                  keyName: fieldKey,
                  maxLines: 2,
                ),
                const SizedBox(height: DrAiSpacing.xs),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _birthDateField() {
    return TextFormField(
      key: const Key('onboarding-birth-date-field'),
      controller: _birthDateController,
      keyboardType: TextInputType.datetime,
      decoration: InputDecoration(
        labelText: 'Birth date',
        hintText: 'YYYY-MM-DD',
        border: const OutlineInputBorder(),
        suffixIcon: IconButton(
          tooltip: 'Select date',
          onPressed: () => _showBirthDatePicker(_birthDateController),
          icon: const Icon(Icons.calendar_today_outlined),
        ),
      ),
      validator: _dateValidator,
    );
  }

  Widget _optionalTextField({
    required TextEditingController controller,
    required String label,
    required String keyName,
    String? hint,
    String? Function(String?)? validator,
    ValueChanged<String>? onChanged,
    int maxLines = 1,
  }) {
    return TextFormField(
      key: Key(keyName),
      controller: controller,
      maxLines: maxLines,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        border: const OutlineInputBorder(),
      ),
      validator: validator,
      onChanged: onChanged,
    );
  }

  List<DropdownMenuItem<String>> _optionItems(List<String> values) {
    return values
        .map(
          (value) => DropdownMenuItem<String>(value: value, child: Text(value)),
        )
        .toList();
  }

  String _knownOption(
    String? savedValue,
    List<String> values,
    String fallback,
  ) {
    final text = savedValue?.trim();
    if (text == null || text.isEmpty) {
      return fallback;
    }
    for (final value in values) {
      if (value.toLowerCase() == text.toLowerCase()) {
        return value;
      }
    }
    return fallback;
  }

  String? _dateValidator(String? value) {
    final text = value?.trim() ?? '';
    if (text.isEmpty) {
      return null;
    }
    if (_parseDate(text) == null) {
      return 'Use YYYY-MM-DD.';
    }
    return null;
  }

  Future<void> _showBirthDatePicker(TextEditingController controller) async {
    var selected =
        _parseDate(controller.text) ?? DateTime(DateTime.now().year - 25, 1, 1);
    await showModalBottomSheet<void>(
      context: context,
      backgroundColor: Colors.transparent,
      barrierColor: DrAiColors.black.withValues(alpha: 0.18),
      builder: (context) => SafeArea(
        top: false,
        child: DecoratedBox(
          decoration: const BoxDecoration(
            color: DrAiColors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: Color(0x240A0076),
                blurRadius: 30,
                offset: Offset(0, -10),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              const SizedBox(height: DrAiSpacing.sm),
              Container(
                width: 42,
                height: 4,
                decoration: BoxDecoration(
                  color: const Color(0xFFD8E1EF),
                  borderRadius: BorderRadius.circular(DrAiRadii.pill),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(
                  DrAiSpacing.md,
                  DrAiSpacing.sm,
                  DrAiSpacing.md,
                  DrAiSpacing.xs,
                ),
                child: Row(
                  children: <Widget>[
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Cancel'),
                    ),
                    const Spacer(),
                    Text(
                      'Birth date',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: DrAiColors.brandDark,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const Spacer(),
                    FilledButton(
                      style: FilledButton.styleFrom(
                        minimumSize: const Size(76, 38),
                        visualDensity: VisualDensity.compact,
                      ),
                      onPressed: () {
                        controller.text = _formatDate(selected);
                        Navigator.of(context).pop();
                      },
                      child: const Text('Done'),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1, color: Color(0xFFE3E8F2)),
              SizedBox(
                height: 244,
                child: CupertinoTheme(
                  data: const CupertinoThemeData(
                    brightness: Brightness.light,
                    textTheme: CupertinoTextThemeData(
                      dateTimePickerTextStyle: TextStyle(
                        color: DrAiColors.ink,
                        fontSize: 21,
                        height: 1.25,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  child: CupertinoDatePicker(
                    mode: CupertinoDatePickerMode.date,
                    initialDateTime: selected,
                    minimumYear: 1900,
                    maximumDate: DateTime.now(),
                    backgroundColor: DrAiColors.white,
                    onDateTimeChanged: (value) => selected = value,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PatientOnboardingPanel extends StatelessWidget {
  const _PatientOnboardingPanel({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
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
          Padding(padding: const EdgeInsets.all(DrAiSpacing.md), child: child),
        ],
      ),
    );
  }
}

class _PatientTodayCard extends ConsumerWidget {
  const _PatientTodayCard({
    required this.today,
    required this.care,
    required this.notifications,
    required this.onRetry,
  });

  final AsyncValue<PatientTodayData> today;
  final AsyncValue<PatientCareBundle> care;
  final AsyncValue<MedicationNotificationScheduleResult> notifications;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final completionState = ref.watch(recoveryTaskCompletionControllerProvider);
    final locallyCompleted = completionState.hasValue
        ? completionState.value ?? const <String>{}
        : const <String>{};
    return today.when(
      loading: () =>
          const DashboardLoadingView(label: 'Loading today recovery tasks'),
      error: (error, stackTrace) => DashboardErrorView(
        message: 'Unable to load today recovery tasks. Try again.',
        onRetry: onRetry,
      ),
      data: (data) {
        return ListView(
          key: const Key('patient-today-task-list'),
          children: <Widget>[
            if (data.activePlan != null) ...<Widget>[
              Text(
                data.activePlan!.title,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 2),
              Text(
                data.activePlan!.instructions,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                '${data.progressSummary.completedTaskCount}/'
                '${data.progressSummary.taskCount} tasks complete - '
                '${data.progressSummary.completionPercent}%',
                key: const Key('patient-today-progress-summary'),
                style: const TextStyle(
                  color: DrAiColors.brand,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: DrAiSpacing.xs),
            ],
            notifications.when(
              loading: () => const Text(
                'Preparing local medication notification shell...',
                style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
              ),
              error: (error, stackTrace) => const Text(
                'Local medication notification shell is unavailable.',
                style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
              ),
              data: (result) => Text(
                result.label,
                key: const Key('patient-medication-notification-shell'),
                style: const TextStyle(
                  color: DrAiColors.brand,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            _MedicationReminderTodayList(care: care),
            if (data.tasks.isEmpty)
              const Padding(
                padding: EdgeInsets.only(bottom: DrAiSpacing.xs),
                child: Text('No active recovery tasks for today.'),
              ),
            completionState.when(
              data: (_) => const SizedBox.shrink(),
              loading: () => const SizedBox.shrink(),
              error: (error, stackTrace) => const Padding(
                padding: EdgeInsets.only(top: DrAiSpacing.xs),
                child: Text(
                  'Completion could not sync. Your local tap is still visible; try again when the connection recovers.',
                  style: TextStyle(color: DrAiColors.danger, fontSize: 12),
                ),
              ),
            ),
            for (final task in data.tasks)
              _TodayTaskTile(
                task: task,
                locallyCompleted: locallyCompleted.contains(task.taskId),
                isPending: completionState.isLoading,
                onChanged: (completed) => ref
                    .read(recoveryTaskCompletionControllerProvider.notifier)
                    .setCompleted(task.taskId, completed: completed),
              ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              data.safetyLabel,
              style: const TextStyle(color: DrAiColors.mutedInk, fontSize: 11),
            ),
          ],
        );
      },
    );
  }
}

class _MedicationReminderTodayList extends StatelessWidget {
  const _MedicationReminderTodayList({required this.care});

  final AsyncValue<PatientCareBundle> care;

  @override
  Widget build(BuildContext context) {
    return care.when(
      loading: () => const Padding(
        padding: EdgeInsets.only(bottom: DrAiSpacing.xs),
        child: Text(
          'Loading medication reminders...',
          style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
        ),
      ),
      error: (error, stackTrace) => const Padding(
        padding: EdgeInsets.only(bottom: DrAiSpacing.xs),
        child: Text(
          'Medication reminders unavailable.',
          style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
        ),
      ),
      data: (bundle) {
        final active = bundle.medicationReminders
            .where((item) => item.status == 'active')
            .toList();
        if (active.isEmpty) {
          return const Padding(
            padding: EdgeInsets.only(bottom: DrAiSpacing.xs),
            child: Text(
              'No medication reminders due.',
              key: Key('patient-today-medication-reminders-empty'),
              style: TextStyle(fontSize: 12, color: DrAiColors.mutedInk),
            ),
          );
        }
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            const Text(
              'Medication reminders',
              style: TextStyle(
                color: DrAiColors.brandDark,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 4),
            for (final reminder in active.take(3))
              Container(
                key: Key('patient-today-reminder-${reminder.id}'),
                margin: const EdgeInsets.only(bottom: 4),
                padding: const EdgeInsets.all(DrAiSpacing.xs),
                decoration: BoxDecoration(
                  color: DrAiColors.surfaceSubtle,
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                ),
                child: Row(
                  children: <Widget>[
                    Icon(
                      reminder.reminderType == 'refill'
                          ? Icons.inventory_2_outlined
                          : Icons.medication_outlined,
                      color: DrAiColors.brand,
                      size: 18,
                    ),
                    const SizedBox(width: DrAiSpacing.xs),
                    Expanded(
                      child: Text(
                        '${reminder.reminderType == 'refill' ? 'Refill' : 'Medication'} - ${reminder.scheduleLabel}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: DrAiSpacing.xs),
          ],
        );
      },
    );
  }
}

class _EducationalChatCard extends ConsumerStatefulWidget {
  const _EducationalChatCard();

  @override
  ConsumerState<_EducationalChatCard> createState() =>
      _EducationalChatCardState();
}

class _EducationalChatCardState extends ConsumerState<_EducationalChatCard> {
  final _messageController = TextEditingController();
  final _chatScrollController = ScrollController();

  @override
  void dispose() {
    _messageController.dispose();
    _chatScrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(educationalChatControllerProvider);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_chatScrollController.hasClients) {
        _chatScrollController.jumpTo(
          _chatScrollController.position.maxScrollExtent,
        );
      }
    });
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        const Text(
          'Educational information only - not medical advice.',
          style: TextStyle(
            color: DrAiColors.danger,
            fontSize: 12,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        Expanded(
          child: ListView.builder(
            key: const Key('educational-chat-message-list'),
            controller: _chatScrollController,
            padding: const EdgeInsets.only(bottom: 2),
            itemCount: chat.messages.length,
            itemBuilder: (context, index) {
              final message = chat.messages[index];
              return _ChatBubble(message: message);
            },
          ),
        ),
        if (chat.errorMessage != null)
          Padding(
            padding: const EdgeInsets.only(top: DrAiSpacing.xs),
            child: Text(
              chat.errorMessage!,
              style: const TextStyle(color: DrAiColors.danger, fontSize: 12),
            ),
          ),
        const SizedBox(height: DrAiSpacing.xs),
        Row(
          children: <Widget>[
            Expanded(
              child: TextField(
                key: const Key('educational-chat-input'),
                controller: _messageController,
                minLines: 1,
                maxLines: 2,
                maxLength: 800,
                keyboardType: TextInputType.text,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _send(),
                decoration: const InputDecoration(
                  counterText: '',
                  isDense: true,
                  hintText: 'Prepare a question for your clinician',
                  prefixIcon: Icon(Icons.chat_bubble_outline),
                ),
              ),
            ),
            const SizedBox(width: DrAiSpacing.xs),
            IconButton.filled(
              key: const Key('educational-chat-send-button'),
              tooltip: 'Send educational question',
              onPressed: chat.isSending ? null : _send,
              icon: chat.isSending
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send_outlined),
            ),
          ],
        ),
      ],
    );
  }

  Future<void> _send() async {
    final sent = await ref
        .read(educationalChatControllerProvider.notifier)
        .send(_messageController.text);
    if (sent && mounted) {
      _messageController.clear();
    }
  }
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.message});

  final ChatDisplayMessage message;

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        key: Key('educational-chat-${message.role}-${message.id}'),
        constraints: const BoxConstraints(maxWidth: 520),
        margin: const EdgeInsets.only(bottom: DrAiSpacing.xs),
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        decoration: BoxDecoration(
          color: message.isRedFlag
              ? DrAiColors.patientAccent
              : isUser
              ? DrAiColors.brand
              : DrAiColors.surfaceSubtle,
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          border: Border.all(color: DrAiColors.outline),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            if (message.content.isEmpty)
              const Text(
                'Streaming response...',
                style: TextStyle(color: DrAiColors.mutedInk),
              )
            else
              Text(
                message.content,
                style: TextStyle(
                  color: isUser ? DrAiColors.white : DrAiColors.ink,
                  fontSize: 12,
                ),
              ),
            if (message.safetyLabel != null) ...<Widget>[
              const SizedBox(height: 2),
              Text(
                message.safetyLabel!,
                style: const TextStyle(
                  color: DrAiColors.danger,
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
            if (message.fallbackReason != null) ...<Widget>[
              const SizedBox(height: 2),
              Text(
                'Fallback: ${message.fallbackReason}',
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 10,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _TodayTaskTile extends StatelessWidget {
  const _TodayTaskTile({
    required this.task,
    required this.locallyCompleted,
    required this.isPending,
    required this.onChanged,
  });

  final RecoveryTaskItem task;
  final bool locallyCompleted;
  final bool isPending;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final completed = task.isCompleted || locallyCompleted;
    return Padding(
      padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
      child: Material(
        color: completed ? DrAiColors.patientAccent : DrAiColors.surfaceSubtle,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(DrAiRadii.md),
          side: const BorderSide(color: DrAiColors.outline),
        ),
        child: CheckboxListTile(
          key: Key('today-task-${task.category}'),
          value: completed,
          onChanged: isPending
              ? null
              : (value) => onChanged(value ?? !completed),
          controlAffinity: ListTileControlAffinity.leading,
          secondary: Icon(_taskIcon(task.category), color: DrAiColors.brand),
          title: Text(
            task.title,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
          subtitle: Text(
            '${_taskLabel(task.category)} - ${task.dueLabel}'
            '${task.notificationTime == null ? '' : ' - ${task.notificationTime}'}\n'
            '${task.detail}',
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ),
    );
  }
}

IconData _taskIcon(String category) {
  return switch (category) {
    'medication' => Icons.medication_outlined,
    'exercise' => Icons.directions_walk_outlined,
    'diet' => Icons.restaurant_outlined,
    'follow_up' => Icons.event_available_outlined,
    _ => Icons.check_circle_outline,
  };
}

String _taskLabel(String category) {
  return switch (category) {
    'medication' => 'Medication',
    'exercise' => 'Exercise',
    'diet' => 'Diet',
    'follow_up' => 'Follow-up',
    _ => 'Task',
  };
}

class _PatientEventUpdatePanel extends ConsumerStatefulWidget {
  const _PatientEventUpdatePanel({required this.bundle});

  final PatientCareBundle bundle;

  @override
  ConsumerState<_PatientEventUpdatePanel> createState() =>
      _PatientEventUpdatePanelState();
}

class _PatientEventUpdatePanelState
    extends ConsumerState<_PatientEventUpdatePanel> {
  final _summaryController = TextEditingController();
  String _updateType = 'general_update';
  String? _validationError;

  @override
  void dispose() {
    _summaryController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final event = widget.bundle.clinicalEvents.isEmpty
        ? null
        : widget.bundle.clinicalEvents.first;
    final state = ref.watch(clinicalEventUpdateControllerProvider);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              event == null
                  ? 'No Clinical Event available for patient update'
                  : 'Update: ${event.title}',
              key: const Key('patient-event-update-title'),
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 4),
            if (widget.bundle.clinicalEventUpdates.isNotEmpty)
              Text(
                'Latest patient update: ${widget.bundle.clinicalEventUpdates.first.summary}',
                key: const Key('patient-event-latest-update'),
              ),
            if (event != null) ...<Widget>[
              const SizedBox(height: 4),
              DropdownButtonFormField<String>(
                key: const Key('patient-event-update-type-field'),
                initialValue: _updateType,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Update type',
                  isDense: true,
                ),
                items: const <DropdownMenuItem<String>>[
                  DropdownMenuItem(
                    value: 'general_update',
                    child: Text('General update'),
                  ),
                  DropdownMenuItem(
                    value: 'symptom_update',
                    child: Text('Symptom update'),
                  ),
                  DropdownMenuItem(
                    value: 'medication_note',
                    child: Text('Medication note'),
                  ),
                  DropdownMenuItem(
                    value: 'recovery_check_in',
                    child: Text('Recovery check-in'),
                  ),
                ],
                onChanged: (value) =>
                    setState(() => _updateType = value ?? 'general_update'),
              ),
              const SizedBox(height: 4),
              TextField(
                key: const Key('patient-event-update-summary-field'),
                controller: _summaryController,
                maxLength: 1200,
                minLines: 1,
                maxLines: 2,
                decoration: const InputDecoration(
                  counterText: '',
                  labelText: 'Self-reported update',
                  isDense: true,
                ),
              ),
              if (_validationError != null)
                Text(
                  _validationError!,
                  style: const TextStyle(color: DrAiColors.danger),
                ),
              state.when(
                loading: () => const LinearProgressIndicator(),
                error: (error, stackTrace) =>
                    Text(_patientSafeErrorMessage(error)),
                data: (update) => update == null
                    ? const SizedBox.shrink()
                    : Text('Update submitted: ${update.updateType}'),
              ),
              const SizedBox(height: 4),
              FilledButton.icon(
                key: const Key('patient-event-update-submit-button'),
                onPressed: state.isLoading ? null : () => _submit(event.id),
                icon: const Icon(Icons.send_outlined),
                label: const Text('Send update'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _submit(String eventId) {
    if (_summaryController.text.trim().length < 3) {
      setState(() => _validationError = 'Enter a short update first.');
      return;
    }
    setState(() => _validationError = null);
    ref
        .read(clinicalEventUpdateControllerProvider.notifier)
        .submit(
          clinicalEventId: eventId,
          updateType: _updateType,
          summary: _summaryController.text.trim(),
        );
  }
}

String _patientHistorySummary(PatientCareBundle bundle) {
  return <String>[
    'Allergies: ${_patientLabelsOrEmpty(bundle.allergies)}',
    'Chronic diseases: ${_patientConditionsOrEmpty(bundle.chronicDiseases)}',
    'Visit history: ${bundle.visitHistory.length}',
    'Diagnoses: ${_patientDiagnosesOrEmpty(bundle.diagnoses)}',
  ].join('\n');
}

String _patientLabelsOrEmpty(List<PatientAllergyItem> items) {
  if (items.isEmpty) {
    return 'none recorded';
  }
  return items.map((item) => item.label).join(', ');
}

String _patientConditionsOrEmpty(List<ChronicDiseaseItem> items) {
  if (items.isEmpty) {
    return 'none recorded';
  }
  return items.map((item) => item.name).join(', ');
}

String _patientDiagnosesOrEmpty(List<DiagnosisItem> items) {
  if (items.isEmpty) {
    return 'none recorded';
  }
  return items.map((item) => item.label).join(', ');
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
          SizedBox(
            height: 32,
            child: Semantics(
              button: true,
              enabled: false,
              label: 'Pay now unavailable',
              child: ExcludeSemantics(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: DrAiColors.inkStrong,
                    borderRadius: BorderRadius.circular(DrAiRadii.md),
                  ),
                  child: const Center(
                    child: Text(
                      'Pay Now',
                      style: TextStyle(color: DrAiColors.outlineMuted),
                    ),
                  ),
                ),
              ),
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

DateTime? _parseDate(String value) {
  final match = RegExp(r'^(\d{4})-(\d{2})-(\d{2})$').firstMatch(value.trim());
  if (match == null) {
    return null;
  }
  final year = int.tryParse(match.group(1)!);
  final month = int.tryParse(match.group(2)!);
  final day = int.tryParse(match.group(3)!);
  if (year == null || month == null || day == null) {
    return null;
  }
  final parsed = DateTime(year, month, day);
  if (parsed.year != year || parsed.month != month || parsed.day != day) {
    return null;
  }
  if (year < 1900 || parsed.isAfter(DateTime.now())) {
    return null;
  }
  return parsed;
}

String _formatDate(DateTime date) {
  return '${date.year.toString().padLeft(4, '0')}-'
      '${date.month.toString().padLeft(2, '0')}-'
      '${date.day.toString().padLeft(2, '0')}';
}

const double _menuMaxHeight = 320;
const BorderRadius _menuBorderRadius = BorderRadius.all(
  Radius.circular(DrAiRadii.md),
);
const TextStyle _menuTextStyle = TextStyle(
  color: DrAiColors.ink,
  fontSize: 14,
  height: 20 / 14,
  fontWeight: FontWeight.w500,
);

String _patientSafeErrorMessage(Object error) {
  if (error is ApiError) {
    if (error.code == 'rate_limited') {
      return 'Educational chat is temporarily rate limited.';
    }
    if (error.code == 'service_unavailable') {
      return 'Unable to reach Dr. AI.';
    }
    return error.message;
  }
  return 'Unable to reach Dr. AI.';
}
