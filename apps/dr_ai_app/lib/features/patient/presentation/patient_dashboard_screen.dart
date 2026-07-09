import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/patient/application/patient_care_providers.dart';
import 'package:dr_ai_app/features/patient/domain/patient_care_data.dart';
import 'package:dr_ai_app/shared/avatar/avatar_upload.dart';
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

class _PatientDashboard extends ConsumerWidget {
  const _PatientDashboard({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final care = ref.watch(ownPatientCareProvider);
    final careBundle = care.asData?.value;
    if (careBundle != null &&
        !careBundle.patient.medicalHistorySetupCompleted) {
      return _PatientOnboardingDashboard(
        care: care,
        onRetry: () => ref.invalidate(ownPatientCareProvider),
      );
    }
    if (data.data.isEmpty) {
      return _PatientReadyEmptyDashboard(
        care: care,
        onRetry: () => ref.invalidate(ownPatientCareProvider),
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
    final today = ref.watch(patientTodayProvider);
    final notifications = ref.watch(medicationNotificationShellProvider);
    final consultations = ref.watch(consultationListProvider);
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
                height: 320 * cardScale,
                child: _PatientSection(
                  title: 'Today',
                  child: _PatientTodayCard(
                    today: today,
                    notifications: notifications,
                    onRetry: () {
                      ref.invalidate(patientTodayProvider);
                      ref.invalidate(medicationNotificationShellProvider);
                    },
                  ),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 192 * cardScale,
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
                height: 244 * cardScale,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Expanded(
                      child: _PatientSection(
                        title: 'Contact Doctor',
                        child: _ContactDoctor(
                          doctor: doctor,
                          consultations: consultations,
                        ),
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
                height: 334 * cardScale,
                child: const _PatientSection(
                  title: 'Ask Dr. AI',
                  child: _EducationalChatCard(),
                ),
              ),
              const SizedBox(height: 6),
              SizedBox(
                height: 198 * cardScale,
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Expanded(
                      child: _EmptyFeatureCard(
                        title: 'Check Medical Record',
                        icon: Icons.description_outlined,
                        emptyLabel: hasRecords
                            ? 'Records available'
                            : 'No Medical Records',
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: _EmptyFeatureCard(
                        title: 'Check Imaging Results',
                        icon: Icons.document_scanner_outlined,
                        emptyLabel: hasImages
                            ? 'Images available'
                            : 'No Imaging Results',
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              const SearchBar(
                hintText: 'Search your care dashboard',
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
              const SizedBox(height: 6),
              SizedBox(
                height: 260 * cardScale,
                child: _PatientSelfCareCard(
                  care: care,
                  onRetry: () => ref.invalidate(ownPatientCareProvider),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PatientReadyEmptyDashboard extends StatelessWidget {
  const _PatientReadyEmptyDashboard({
    required this.care,
    required this.onRetry,
  });

  final AsyncValue<PatientCareBundle> care;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: DrAiColors.brandSoft,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: Padding(
            padding: const EdgeInsets.all(DrAiSpacing.md),
            child: _PatientOnboardingPanel(
              title: 'Dashboard',
              child: care.when(
                loading: () =>
                    const DashboardLoadingView(label: 'Loading your profile'),
                error: (error, stackTrace) => DashboardErrorView(
                  message: 'Unable to load your profile. Try again.',
                  onRetry: onRetry,
                ),
                data: (bundle) => Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        CircleAvatar(
                          radius: 30,
                          backgroundColor: DrAiColors.brandSoft,
                          backgroundImage: bundle.patient.avatarUrl == null
                              ? null
                              : NetworkImage(bundle.patient.avatarUrl!),
                          child: bundle.patient.avatarUrl == null
                              ? const Icon(
                                  Icons.person_outline,
                                  color: DrAiColors.brand,
                                )
                              : null,
                        ),
                        const SizedBox(width: DrAiSpacing.md),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                bundle.patient.displayName,
                                style: Theme.of(context).textTheme.titleLarge
                                    ?.copyWith(fontWeight: FontWeight.w800),
                              ),
                              SelectableText(
                                'Patient ID: ${bundle.patient.syntheticIdentifier}',
                                style: const TextStyle(
                                  color: DrAiColors.brand,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: DrAiSpacing.lg),
                    const Text(
                      'Your profile and medical intake are saved.',
                      style: TextStyle(
                        color: DrAiColors.ink,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: DrAiSpacing.sm),
                    const Text(
                      'Share your patient ID with your doctor. Your care plan, medications, imaging, and consultation activity will appear here after a doctor connects to your account.',
                      style: TextStyle(
                        color: DrAiColors.inkSecondary,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _PatientOnboardingDashboard extends ConsumerStatefulWidget {
  const _PatientOnboardingDashboard({
    required this.care,
    required this.onRetry,
  });

  final AsyncValue<PatientCareBundle> care;
  final VoidCallback onRetry;

  @override
  ConsumerState<_PatientOnboardingDashboard> createState() =>
      _PatientOnboardingDashboardState();
}

class _PatientOnboardingDashboardState
    extends ConsumerState<_PatientOnboardingDashboard> {
  final _formKey = GlobalKey<FormState>();
  final _displayNameController = TextEditingController();
  final _birthDateController = TextEditingController();
  final _contactPhoneController = TextEditingController();
  final _emergencyNameController = TextEditingController();
  final _emergencyPhoneController = TextEditingController();
  final _avatarUrlController = TextEditingController();
  final _allergyLabelController = TextEditingController();
  final _allergyReactionController = TextEditingController();
  final _conditionNameController = TextEditingController();
  final _conditionNotesController = TextEditingController();
  final _currentMedicationsController = TextEditingController();
  final _surgeryHistoryController = TextEditingController();
  final _familyHistoryController = TextEditingController();
  final _lifestyleNotesController = TextEditingController();
  String _gender = 'Unspecified';
  String _bloodType = 'Unknown';
  String _pregnancyStatus = 'Prefer not to say';
  String _preferredLanguage = 'Simplified Chinese';
  String _contactPreference = 'Phone';
  bool _hasAllergies = false;
  bool _hasChronicCondition = false;
  bool _seededFromBundle = false;
  String? _avatarFileName;
  String? _avatarUploadError;

  @override
  void dispose() {
    _displayNameController.dispose();
    _birthDateController.dispose();
    _contactPhoneController.dispose();
    _emergencyNameController.dispose();
    _emergencyPhoneController.dispose();
    _avatarUrlController.dispose();
    _allergyLabelController.dispose();
    _allergyReactionController.dispose();
    _conditionNameController.dispose();
    _conditionNotesController.dispose();
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
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: ListView(
            key: const Key('patient-onboarding-list'),
            padding: const EdgeInsets.all(DrAiSpacing.md),
            children: <Widget>[
              _PatientOnboardingPanel(
                title: 'Complete your profile',
                child: widget.care.when(
                  loading: () =>
                      const DashboardLoadingView(label: 'Loading your profile'),
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
              const SizedBox(height: DrAiSpacing.md),
              SizedBox(
                height: 340,
                child: _PatientSelfCareCard(
                  care: widget.care,
                  onRetry: widget.onRetry,
                ),
              ),
            ],
          ),
        ),
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
    _avatarUrlController.text = patient.avatarUrl ?? '';
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
          Row(
            children: <Widget>[
              CircleAvatar(
                radius: 30,
                backgroundColor: DrAiColors.brandSoft,
                backgroundImage: _avatarUrlController.text.trim().isEmpty
                    ? null
                    : NetworkImage(_avatarUrlController.text.trim()),
                child: _avatarUrlController.text.trim().isEmpty
                    ? const Icon(Icons.person_outline, color: DrAiColors.brand)
                    : null,
              ),
              const SizedBox(width: DrAiSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    const Text(
                      'This information helps your doctor recognize your account.',
                      style: TextStyle(color: DrAiColors.mutedInk),
                    ),
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
            ],
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
              Expanded(
                child: _optionalTextField(
                  controller: _birthDateController,
                  label: 'Birth date',
                  hint: 'YYYY-MM-DD',
                  keyName: 'onboarding-birth-date-field',
                  validator: _dateValidator,
                ),
              ),
              const SizedBox(width: DrAiSpacing.sm),
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: const Key('onboarding-gender-field'),
                  initialValue: _gender,
                  isExpanded: true,
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
          _avatarUploadControl(),
          const SizedBox(height: DrAiSpacing.md),
          DropdownButtonFormField<String>(
            key: const Key('onboarding-blood-type-field'),
            initialValue: _bloodType,
            isExpanded: true,
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

  Widget _avatarUploadControl() {
    final hasAvatar = _avatarUrlController.text.trim().isNotEmpty;
    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: DrAiColors.outline),
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: Row(
          children: <Widget>[
            CircleAvatar(
              radius: 34,
              backgroundColor: DrAiColors.brandSoft,
              backgroundImage: hasAvatar
                  ? NetworkImage(_avatarUrlController.text.trim())
                  : null,
              child: hasAvatar
                  ? null
                  : const Icon(Icons.person_outline, color: DrAiColors.brand),
            ),
            const SizedBox(width: DrAiSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  OutlinedButton.icon(
                    key: const Key('onboarding-avatar-upload-button'),
                    onPressed: _pickAvatar,
                    icon: const Icon(Icons.photo_camera_outlined),
                    label: const Text('Upload avatar photo'),
                  ),
                  Text(
                    _avatarFileName ?? 'JPG or PNG up to 2 MB',
                    style: const TextStyle(
                      color: DrAiColors.mutedInk,
                      fontSize: 12,
                    ),
                  ),
                  if (_avatarUploadError != null)
                    Text(
                      _avatarUploadError!,
                      style: const TextStyle(
                        color: DrAiColors.danger,
                        fontSize: 12,
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickAvatar() async {
    try {
      final result = await pickAvatarImage();
      if (result == null) {
        return;
      }
      setState(() {
        _avatarUrlController.text = result.dataUrl;
        _avatarFileName = result.fileName;
        _avatarUploadError = null;
      });
    } on AvatarUploadException catch (error) {
      setState(() => _avatarUploadError = error.message);
    } on Exception {
      setState(
        () => _avatarUploadError = 'Photo upload is not available here.',
      );
    }
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
          avatarUrl: _avatarUrlController.text,
          hasAllergies: _hasAllergies,
          allergyLabel: _allergyLabelController.text,
          allergyReaction: _allergyReactionController.text,
          hasChronicCondition: _hasChronicCondition,
          chronicConditionName: _conditionNameController.text,
          chronicConditionNotes: _conditionNotesController.text,
          bloodType: _bloodType,
          currentMedications: _currentMedicationsController.text,
          surgeryHistory: _surgeryHistoryController.text,
          familyHistory: _familyHistoryController.text,
          lifestyleNotes: _lifestyleNotesController.text,
          pregnancyStatus: _pregnancyStatus,
        );
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
    if (!RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(text)) {
      return 'Use YYYY-MM-DD.';
    }
    return null;
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
    required this.notifications,
    required this.onRetry,
  });

  final AsyncValue<PatientTodayData> today;
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
        if (data.tasks.isEmpty) {
          return const Center(child: Text('No active tasks for today.'));
        }
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
                onComplete: () => ref
                    .read(recoveryTaskCompletionControllerProvider.notifier)
                    .complete(task.taskId),
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
    required this.onComplete,
  });

  final RecoveryTaskItem task;
  final bool locallyCompleted;
  final bool isPending;
  final VoidCallback onComplete;

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
          onChanged: completed || isPending ? null : (_) => onComplete(),
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

class _PatientSelfCareCard extends StatelessWidget {
  const _PatientSelfCareCard({required this.care, required this.onRetry});

  final AsyncValue<PatientCareBundle> care;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _PatientSection(
      title: 'Profile and Medications',
      child: care.when(
        loading: () =>
            const DashboardLoadingView(label: 'Loading your care profile'),
        error: (error, stackTrace) => DashboardErrorView(
          message: 'Unable to load your profile. Try again.',
          onRetry: onRetry,
        ),
        data: (bundle) => ListView(
          children: <Widget>[
            Text(
              bundle.patient.displayName,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            Text(
              'Patient code: ${bundle.patient.syntheticIdentifier}',
              style: const TextStyle(color: DrAiColors.brand, fontSize: 12),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(_patientDemographicsLine(bundle.patient)),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              bundle.records.isEmpty
                  ? 'No Medical Records'
                  : '${bundle.records.length} medical record(s)',
              key: const Key('patient-self-records'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              bundle.imagingAssets.isEmpty
                  ? 'No imaging assets'
                  : '${bundle.imagingAssets.length} imaging asset(s): '
                        '${bundle.imagingAssets.first.uploadStatus} / '
                        '${bundle.imagingAssets.first.reviewStatus}',
              key: const Key('patient-self-imaging-assets'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              _patientHistorySummary(bundle),
              key: const Key('patient-self-history-summary'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            _PatientEventUpdatePanel(bundle: bundle),
            const SizedBox(height: DrAiSpacing.xs),
            if (bundle.medications.isEmpty)
              const Text('No medications recorded')
            else
              for (final medication in bundle.medications)
                Padding(
                  padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: DrAiColors.surfaceSubtle,
                      borderRadius: BorderRadius.circular(DrAiRadii.md),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(DrAiSpacing.xs),
                      child: Text(
                        '${medication.name}\n${medication.dosage} - ${medication.schedule}',
                      ),
                    ),
                  ),
                ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              bundle.prescriptions.isEmpty
                  ? 'No prescriptions'
                  : '${bundle.prescriptions.length} prescription(s)',
              key: const Key('patient-self-prescriptions'),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            if (bundle.medicationReminders.isEmpty)
              const Text('No medication reminders')
            else
              for (final reminder in bundle.medicationReminders)
                Padding(
                  padding: const EdgeInsets.only(bottom: DrAiSpacing.xs),
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: DrAiColors.surfaceSubtle,
                      borderRadius: BorderRadius.circular(DrAiRadii.md),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(DrAiSpacing.xs),
                      child: Text(
                        '${reminder.reminderType == 'refill' ? 'Refill' : 'Medication'} reminder\n'
                        '${reminder.scheduleLabel} - ${reminder.status}',
                      ),
                    ),
                  ),
                ),
          ],
        ),
      ),
    );
  }
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
  final _summaryController = TextEditingController(
    text: 'Synthetic patient update for the care episode.',
  );
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

String _patientDemographicsLine(PatientProfile patient) {
  final values = <String>[
    if (patient.birthYear != null) 'Born ${patient.birthYear}',
    if (patient.sex != null) patient.sex!,
    if (patient.preferredLanguage != null) patient.preferredLanguage!,
    if (patient.contactPreference != null) patient.contactPreference!,
  ];
  return values.isEmpty ? 'Demographics not recorded' : values.join(' - ');
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
          SizedBox(
            height: 24,
            child: Semantics(
              button: true,
              enabled: false,
              label: 'See more recovery tasks unavailable in summary',
              child: ExcludeSemantics(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: DrAiColors.patientAccent,
                    borderRadius: BorderRadius.circular(DrAiRadii.pill),
                  ),
                  child: const Center(
                    child: Text(
                      '+  See More',
                      style: TextStyle(
                        fontSize: 10,
                        color: DrAiColors.brandDark,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ContactDoctor extends StatelessWidget {
  const _ContactDoctor({required this.doctor, required this.consultations});

  final Map<String, dynamic> doctor;
  final AsyncValue<ConsultationListData> consultations;

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
          const SizedBox(height: DrAiSpacing.xs),
          consultations.when(
            loading: () => const Text(
              'Checking specialist status...',
              style: TextStyle(color: DrAiColors.outlineMuted, fontSize: 11),
            ),
            error: (error, stackTrace) => Text(
              _patientSafeErrorMessage(error),
              style: const TextStyle(
                color: DrAiColors.outlineMuted,
                fontSize: 11,
              ),
            ),
            data: (data) {
              if (data.items.isEmpty) {
                return const Text(
                  'No specialist request yet',
                  style: TextStyle(
                    color: DrAiColors.outlineMuted,
                    fontSize: 11,
                  ),
                );
              }
              final latest = data.items.first;
              return Text(
                'Specialist: ${latest.status} - ${latest.specialty}',
                key: const Key('patient-consultation-status'),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: DrAiColors.patientAccent,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                ),
              );
            },
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
              label: 'Pay now unavailable in Week 1',
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
