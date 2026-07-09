import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/doctor/domain/doctor_profile.dart';
import 'package:dr_ai_app/shared/avatar/avatar_upload.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final doctorProfileProvider = FutureProvider<DoctorProfile>((ref) {
  return ref.watch(repositoryProvider).loadOwnDoctorProfile();
});

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

class DoctorAccountScreen extends ConsumerWidget {
  const DoctorAccountScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(doctorProfileProvider);
    final auth = ref.watch(authControllerProvider);
    final email = auth.value?.user?.email ?? '';
    return ResponsiveAppShell(
      role: AppRole.doctor,
      selectedIndex: 5,
      child: profile.when(
        loading: () =>
            const DashboardLoadingView(label: 'Loading doctor account'),
        error: (error, stackTrace) => DashboardErrorView(
          message: error.toString(),
          onRetry: () => ref.invalidate(doctorProfileProvider),
        ),
        data: (profile) => _DoctorAccountView(profile: profile, email: email),
      ),
    );
  }
}

class _DoctorAccountView extends ConsumerStatefulWidget {
  const _DoctorAccountView({required this.profile, required this.email});

  final DoctorProfile profile;
  final String email;

  @override
  ConsumerState<_DoctorAccountView> createState() => _DoctorAccountViewState();
}

class _DoctorAccountViewState extends ConsumerState<_DoctorAccountView> {
  late final TextEditingController _displayNameController;
  late final TextEditingController _specialtyController;
  late final TextEditingController _titleController;
  late final TextEditingController _hospitalController;
  late final TextEditingController _departmentController;
  late final TextEditingController _phoneController;
  late final TextEditingController _countryController;
  late final TextEditingController _provinceController;
  late final TextEditingController _cityController;
  late String _preferredLanguage;
  bool _saving = false;
  String? _statusMessage;

  @override
  void initState() {
    super.initState();
    _displayNameController = TextEditingController();
    _specialtyController = TextEditingController();
    _titleController = TextEditingController();
    _hospitalController = TextEditingController();
    _departmentController = TextEditingController();
    _phoneController = TextEditingController();
    _countryController = TextEditingController();
    _provinceController = TextEditingController();
    _cityController = TextEditingController();
    _seedFields(widget.profile);
  }

  @override
  void didUpdateWidget(covariant _DoctorAccountView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.profile != widget.profile) {
      _seedFields(widget.profile);
    }
  }

  @override
  void dispose() {
    _displayNameController.dispose();
    _specialtyController.dispose();
    _titleController.dispose();
    _hospitalController.dispose();
    _departmentController.dispose();
    _phoneController.dispose();
    _countryController.dispose();
    _provinceController.dispose();
    _cityController.dispose();
    super.dispose();
  }

  void _seedFields(DoctorProfile profile) {
    _displayNameController.text = profile.displayName;
    _specialtyController.text = profile.specialty ?? '';
    _titleController.text = profile.title;
    _hospitalController.text = profile.hospitalName;
    _departmentController.text = profile.department ?? '';
    _phoneController.text = profile.contactPhone ?? '';
    _countryController.text = profile.country ?? '';
    _provinceController.text = profile.province ?? '';
    _cityController.text = profile.city ?? '';
    _preferredLanguage = profile.preferredLanguage ?? 'English';
  }

  Future<void> _saveProfile() async {
    final profile = widget.profile;
    final payload = _currentPayload();
    final hasChanges =
        payload.displayName != profile.displayName ||
        payload.specialty != (profile.specialty ?? '') ||
        payload.title != profile.title ||
        payload.hospitalName != profile.hospitalName ||
        payload.department != (profile.department ?? '') ||
        payload.contactPhone != (profile.contactPhone ?? '') ||
        payload.country != (profile.country ?? '') ||
        payload.province != (profile.province ?? '') ||
        payload.city != (profile.city ?? '') ||
        payload.preferredLanguage != (profile.preferredLanguage ?? 'English');
    if (!hasChanges) {
      setState(() => _statusMessage = 'No account changes to save.');
      return;
    }
    if (payload.displayName.isEmpty ||
        payload.title.isEmpty ||
        payload.hospitalName.isEmpty) {
      setState(() {
        _statusMessage =
            'Display name, title, and hospital are required before saving.';
      });
      return;
    }
    setState(() {
      _saving = true;
      _statusMessage = null;
    });
    try {
      await ref
          .read(repositoryProvider)
          .updateOwnDoctorProfile(
            displayName: payload.displayName,
            specialty: payload.specialty,
            title: payload.title,
            hospitalName: payload.hospitalName,
            department: payload.department,
            contactPhone: payload.contactPhone,
            country: payload.country,
            province: payload.province,
            city: payload.city,
            preferredLanguage: payload.preferredLanguage,
          );
      ref.invalidate(doctorProfileProvider);
      if (mounted) {
        setState(() {
          _saving = false;
          _statusMessage = 'Account changes saved.';
        });
      }
    } on ApiError catch (error) {
      if (mounted) {
        setState(() {
          _saving = false;
          _statusMessage = error.message;
        });
      }
    } on Exception {
      if (mounted) {
        setState(() {
          _saving = false;
          _statusMessage =
              'Unable to save account changes. Check your connection and try again.';
        });
      }
    }
  }

  void _cancelChanges() {
    setState(() {
      _seedFields(widget.profile);
      _statusMessage = null;
    });
  }

  _DoctorAccountPayload _currentPayload() {
    return _DoctorAccountPayload(
      displayName: _displayNameController.text.trim(),
      specialty: _specialtyController.text.trim(),
      title: _titleController.text.trim(),
      hospitalName: _hospitalController.text.trim(),
      department: _departmentController.text.trim(),
      contactPhone: _phoneController.text.trim(),
      country: _countryController.text.trim(),
      province: _provinceController.text.trim(),
      city: _cityController.text.trim(),
      preferredLanguage: _preferredLanguage.trim(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final desktop = MediaQuery.sizeOf(context).width >= 1080;
    final profile = widget.profile;
    return ColoredBox(
      color: DrAiColors.brandSoft,
      child: ListView(
        key: const Key('doctor-account-list'),
        padding: EdgeInsets.fromLTRB(
          desktop ? DrAiSpacing.xxl : DrAiSpacing.md,
          DrAiSpacing.lg,
          desktop ? DrAiSpacing.xxl : DrAiSpacing.md,
          DrAiSpacing.xxl,
        ),
        children: <Widget>[
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1320),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'Doctor Account',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: DrAiColors.brandDark,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: DrAiSpacing.xs),
                const Text(
                  'Manage your profile, language preferences, and account settings.',
                  style: TextStyle(color: DrAiColors.inkSecondary),
                ),
                const SizedBox(height: DrAiSpacing.lg),
                if (desktop)
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      SizedBox(
                        width: 300,
                        child: _DoctorAccountProfileCard(
                          profile: profile,
                          email: widget.email,
                        ),
                      ),
                      const SizedBox(width: DrAiSpacing.lg),
                      Expanded(child: _formPanel()),
                    ],
                  )
                else
                  Column(
                    children: <Widget>[
                      _DoctorAccountProfileCard(
                        profile: profile,
                        email: widget.email,
                      ),
                      const SizedBox(height: DrAiSpacing.md),
                      _formPanel(),
                    ],
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _formPanel() {
    return _DoctorAccountFormPanel(
      saving: _saving,
      statusMessage: _statusMessage,
      preferredLanguage: _preferredLanguage,
      onPreferredLanguageChanged: (value) {
        if (value == null) {
          return;
        }
        setState(() => _preferredLanguage = value);
      },
      onCancel: _saving ? null : _cancelChanges,
      onSave: _saving ? null : _saveProfile,
      displayNameController: _displayNameController,
      specialtyController: _specialtyController,
      titleController: _titleController,
      hospitalController: _hospitalController,
      departmentController: _departmentController,
      phoneController: _phoneController,
      email: widget.email,
      countryController: _countryController,
      provinceController: _provinceController,
      cityController: _cityController,
    );
  }
}

class _DoctorAccountPayload {
  const _DoctorAccountPayload({
    required this.displayName,
    required this.specialty,
    required this.title,
    required this.hospitalName,
    required this.department,
    required this.contactPhone,
    required this.country,
    required this.province,
    required this.city,
    required this.preferredLanguage,
  });

  final String displayName;
  final String specialty;
  final String title;
  final String hospitalName;
  final String department;
  final String contactPhone;
  final String country;
  final String province;
  final String city;
  final String preferredLanguage;
}

class _DoctorAccountProfileCard extends StatelessWidget {
  const _DoctorAccountProfileCard({required this.profile, required this.email});

  final DoctorProfile profile;
  final String email;

  @override
  Widget build(BuildContext context) {
    final location = _joinRecorded(<String?>[
      profile.city,
      profile.province,
      profile.country,
    ]);
    final avatar = avatarImageProvider(profile.avatarUrl);
    return _DoctorAccountCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Center(
            child: Stack(
              clipBehavior: Clip.none,
              children: <Widget>[
                CircleAvatar(
                  radius: 64,
                  backgroundColor: const Color(0xFFE9EDF8),
                  backgroundImage: avatar,
                  child: avatar == null
                      ? const Icon(
                          Icons.person_outline,
                          size: 58,
                          color: DrAiColors.brand,
                        )
                      : null,
                ),
                Positioned(
                  right: 2,
                  bottom: 8,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: DrAiColors.accentIndigo,
                      border: Border.all(color: DrAiColors.white, width: 2),
                      borderRadius: BorderRadius.circular(DrAiRadii.pill),
                    ),
                    child: const Padding(
                      padding: EdgeInsets.all(7),
                      child: Icon(
                        Icons.photo_camera_outlined,
                        size: 16,
                        color: DrAiColors.white,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: DrAiSpacing.lg),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Flexible(
                child: Text(
                  profile.displayName,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: DrAiColors.brandDark,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              const SizedBox(width: DrAiSpacing.xs),
              const Icon(
                Icons.verified_rounded,
                color: DrAiColors.accentIndigo,
                size: 20,
              ),
            ],
          ),
          const SizedBox(height: DrAiSpacing.xs),
          Text(
            _recorded(profile.title),
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: DrAiColors.inkSecondary,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: DrAiSpacing.lg),
          const Divider(color: DrAiColors.outline),
          const SizedBox(height: DrAiSpacing.md),
          _ProfileSummaryRow(
            icon: Icons.local_hospital_outlined,
            title: _recorded(profile.hospitalName),
            subtitle: location,
            tag: _emptyToNull(profile.department),
          ),
          const SizedBox(height: DrAiSpacing.lg),
          const Divider(color: DrAiColors.outline),
          const SizedBox(height: DrAiSpacing.md),
          _ProfileSummaryRow(
            icon: Icons.verified_user_outlined,
            title: 'Verification status',
            subtitle: 'Active doctor account',
            accent: DrAiColors.accentMint,
          ),
          const SizedBox(height: DrAiSpacing.lg),
          const Divider(color: DrAiColors.outline),
          const SizedBox(height: DrAiSpacing.md),
          _ProfileSummaryRow(
            icon: Icons.alternate_email_outlined,
            title: 'Account contact',
            subtitle: _accountEmail(email),
          ),
        ],
      ),
    );
  }
}

class _DoctorAccountFormPanel extends StatelessWidget {
  const _DoctorAccountFormPanel({
    required this.saving,
    required this.statusMessage,
    required this.preferredLanguage,
    required this.onPreferredLanguageChanged,
    required this.onCancel,
    required this.onSave,
    required this.displayNameController,
    required this.specialtyController,
    required this.titleController,
    required this.hospitalController,
    required this.departmentController,
    required this.phoneController,
    required this.email,
    required this.countryController,
    required this.provinceController,
    required this.cityController,
  });

  final bool saving;
  final String? statusMessage;
  final String preferredLanguage;
  final ValueChanged<String?> onPreferredLanguageChanged;
  final VoidCallback? onCancel;
  final VoidCallback? onSave;
  final TextEditingController displayNameController;
  final TextEditingController specialtyController;
  final TextEditingController titleController;
  final TextEditingController hospitalController;
  final TextEditingController departmentController;
  final TextEditingController phoneController;
  final String email;
  final TextEditingController countryController;
  final TextEditingController provinceController;
  final TextEditingController cityController;

  @override
  Widget build(BuildContext context) {
    return _DoctorAccountCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          _DoctorAccountSection(
            icon: Icons.person_outline,
            title: 'Clinical identity',
            child: _ResponsiveFieldGrid(
              children: <Widget>[
                _DoctorAccountTextField(
                  controller: displayNameController,
                  label: 'Display name',
                  keyName: 'doctor-account-display-name-field',
                ),
                _DoctorAccountTextField(
                  controller: specialtyController,
                  label: 'Specialty',
                  keyName: 'doctor-account-specialty-field',
                ),
                _DoctorAccountTextField(
                  controller: titleController,
                  label: 'Title',
                  keyName: 'doctor-account-title-field',
                ),
              ],
            ),
          ),
          const _AccountDivider(),
          _DoctorAccountSection(
            icon: Icons.apartment_outlined,
            title: 'Hospital & location',
            child: Column(
              children: <Widget>[
                _ResponsiveFieldGrid(
                  children: <Widget>[
                    _DoctorAccountTextField(
                      controller: hospitalController,
                      label: 'Hospital',
                      keyName: 'doctor-account-hospital-field',
                    ),
                    _DoctorAccountTextField(
                      controller: departmentController,
                      label: 'Department',
                      keyName: 'doctor-account-department-field',
                    ),
                  ],
                ),
                const SizedBox(height: DrAiSpacing.md),
                _ResponsiveFieldGrid(
                  children: <Widget>[
                    _DoctorAccountTextField(
                      controller: countryController,
                      label: 'Country / Region',
                      keyName: 'doctor-account-country-field',
                    ),
                    _DoctorAccountTextField(
                      controller: provinceController,
                      label: 'Province',
                      keyName: 'doctor-account-province-field',
                    ),
                    _DoctorAccountTextField(
                      controller: cityController,
                      label: 'City',
                      keyName: 'doctor-account-city-field',
                    ),
                  ],
                ),
              ],
            ),
          ),
          const _AccountDivider(),
          _DoctorAccountSection(
            icon: Icons.phone_outlined,
            title: 'Contact',
            child: _ResponsiveFieldGrid(
              children: <Widget>[
                _DoctorAccountTextField(
                  controller: phoneController,
                  label: 'Phone',
                  keyName: 'doctor-account-phone-field',
                ),
                _ReadOnlyAccountField(
                  label: 'Email',
                  value: _accountEmail(email),
                ),
              ],
            ),
          ),
          const _AccountDivider(),
          _DoctorAccountSection(
            icon: Icons.lock_outline,
            title: 'Security',
            child: _ResponsiveFieldGrid(
              children: <Widget>[
                _ReadOnlyAccountField(label: 'Password', value: '••••••••••••'),
                Align(
                  alignment: Alignment.bottomLeft,
                  child: OutlinedButton(
                    onPressed: null,
                    child: const Text('Change password'),
                  ),
                ),
              ],
            ),
          ),
          const _AccountDivider(),
          _DoctorAccountSection(
            icon: Icons.settings_outlined,
            title: 'Language preferences',
            child: _ResponsiveFieldGrid(
              children: <Widget>[
                DropdownButtonFormField<String>(
                  key: const Key('doctor-account-language-field'),
                  initialValue: preferredLanguage,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: 'Preferred language',
                  ),
                  items: _languageOptions(preferredLanguage)
                      .map(
                        (language) => DropdownMenuItem<String>(
                          value: language,
                          child: Text(language),
                        ),
                      )
                      .toList(),
                  onChanged: saving ? null : onPreferredLanguageChanged,
                ),
              ],
            ),
          ),
          const SizedBox(height: DrAiSpacing.lg),
          if (statusMessage != null) ...<Widget>[
            Text(
              statusMessage!,
              key: const Key('doctor-account-save-status'),
              textAlign: TextAlign.right,
              style: TextStyle(
                color: statusMessage == 'Account changes saved.'
                    ? DrAiColors.accentMint
                    : DrAiColors.inkSecondary,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: DrAiSpacing.sm),
          ],
          Wrap(
            alignment: WrapAlignment.end,
            spacing: DrAiSpacing.sm,
            runSpacing: DrAiSpacing.sm,
            children: <Widget>[
              OutlinedButton(
                key: const Key('doctor-account-cancel-button'),
                onPressed: onCancel,
                child: const Text('Cancel'),
              ),
              FilledButton(
                key: const Key('doctor-account-save-button'),
                onPressed: onSave,
                child: saving
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: DrAiColors.white,
                        ),
                      )
                    : const Text('Save changes'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _DoctorAccountCard extends StatelessWidget {
  const _DoctorAccountCard({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        border: Border.all(color: const Color(0xFFDCE1EE)),
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Color(0x0D030025),
            blurRadius: 24,
            offset: Offset(0, 12),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.lg),
        child: child,
      ),
    );
  }
}

class _DoctorAccountSection extends StatelessWidget {
  const _DoctorAccountSection({
    required this.icon,
    required this.title,
    required this.child,
  });

  final IconData icon;
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        _AccountIcon(icon: icon),
        const SizedBox(width: DrAiSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Text(
                title,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: DrAiColors.brandDark,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: DrAiSpacing.md),
              child,
            ],
          ),
        ),
      ],
    );
  }
}

class _AccountIcon extends StatelessWidget {
  const _AccountIcon({required this.icon});

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: const Color(0xFFF0EEFF),
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.xs),
        child: Icon(icon, color: DrAiColors.accentIndigo, size: 22),
      ),
    );
  }
}

class _ResponsiveFieldGrid extends StatelessWidget {
  const _ResponsiveFieldGrid({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 820
            ? 3
            : constraints.maxWidth >= 540
            ? 2
            : 1;
        return Wrap(
          spacing: DrAiSpacing.md,
          runSpacing: DrAiSpacing.md,
          children: children
              .map(
                (child) => SizedBox(
                  width:
                      (constraints.maxWidth -
                          (DrAiSpacing.md * (columns - 1))) /
                      columns,
                  child: child,
                ),
              )
              .toList(),
        );
      },
    );
  }
}

class _DoctorAccountTextField extends StatelessWidget {
  const _DoctorAccountTextField({
    required this.controller,
    required this.label,
    required this.keyName,
  });

  final TextEditingController controller;
  final String label;
  final String keyName;

  @override
  Widget build(BuildContext context) {
    return TextField(
      key: Key(keyName),
      controller: controller,
      decoration: InputDecoration(labelText: label),
      style: const TextStyle(
        fontSize: 14,
        height: 20 / 14,
        fontWeight: FontWeight.w600,
      ),
    );
  }
}

class _ReadOnlyAccountField extends StatelessWidget {
  const _ReadOnlyAccountField({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      initialValue: value,
      readOnly: true,
      decoration: InputDecoration(labelText: label),
      style: const TextStyle(
        fontSize: 14,
        height: 20 / 14,
        fontWeight: FontWeight.w600,
      ),
    );
  }
}

class _ProfileSummaryRow extends StatelessWidget {
  const _ProfileSummaryRow({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.tag,
    this.accent = DrAiColors.accentIndigo,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final String? tag;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(icon, color: accent, size: 30),
        const SizedBox(width: DrAiSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                title,
                style: const TextStyle(
                  color: DrAiColors.brandDark,
                  fontWeight: FontWeight.w800,
                ),
              ),
              if (tag != null) ...<Widget>[
                const SizedBox(height: DrAiSpacing.xs),
                Align(
                  alignment: Alignment.centerLeft,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: const Color(0xFFDDF8F0),
                      borderRadius: BorderRadius.circular(DrAiRadii.sm),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: DrAiSpacing.xs,
                        vertical: DrAiSpacing.xxs,
                      ),
                      child: Text(
                        tag!,
                        style: const TextStyle(
                          color: Color(0xFF087A61),
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
              const SizedBox(height: DrAiSpacing.xs),
              Text(
                subtitle,
                style: const TextStyle(
                  color: DrAiColors.inkSecondary,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _AccountDivider extends StatelessWidget {
  const _AccountDivider();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: DrAiSpacing.lg),
      child: Divider(height: 1, color: DrAiColors.outline),
    );
  }
}

String _recorded(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return 'Not recorded';
  }
  return trimmed;
}

String? _emptyToNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}

String _joinRecorded(List<String?> values) {
  final recorded = values
      .map((value) => value?.trim())
      .whereType<String>()
      .where((value) => value.isNotEmpty)
      .toList();
  if (recorded.isEmpty) {
    return 'Not recorded';
  }
  return recorded.join(', ');
}

String _accountEmail(String value) {
  final trimmed = value.trim();
  if (trimmed.isEmpty || !trimmed.contains('@')) {
    return 'Not recorded';
  }
  return trimmed;
}

List<String> _languageOptions(String selected) {
  final options = <String>['English', 'Simplified Chinese'];
  if (selected.trim().isNotEmpty && !options.contains(selected)) {
    options.add(selected);
  }
  return options;
}

class _DoctorDashboard extends StatelessWidget {
  const _DoctorDashboard({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context) {
    final dashboardData = _doctorDashboardData(data.data);
    return ColoredBox(
      color: DrAiColors.brandSoft,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final desktop = constraints.maxWidth >= DrAiBreakpoints.desktop;
          return SingleChildScrollView(
            padding: const EdgeInsets.all(DrAiSpacing.sm),
            child: desktop
                ? Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      SizedBox(
                        width: 258,
                        child: _DoctorIdentityColumn(data: dashboardData),
                      ),
                      const SizedBox(width: DrAiSpacing.xs),
                      Expanded(child: _DoctorMainColumn(data: dashboardData)),
                      const SizedBox(width: DrAiSpacing.xs),
                      SizedBox(
                        width: 326,
                        child: _DoctorSideColumn(data: dashboardData),
                      ),
                    ],
                  )
                : Column(
                    children: <Widget>[
                      _DoctorIdentityColumn(data: dashboardData),
                      const SizedBox(height: DrAiSpacing.xs),
                      _DoctorMainColumn(data: dashboardData),
                      const SizedBox(height: DrAiSpacing.xs),
                      _DoctorSideColumn(data: dashboardData),
                    ],
                  ),
          );
        },
      ),
    );
  }
}

Map<String, dynamic> _doctorDashboardData(Map<String, dynamic> source) {
  if (source.containsKey('hospital') &&
      source.containsKey('doctor') &&
      source.containsKey('quick_access')) {
    return source;
  }
  return <String, dynamic>{
    'safety_label': 'Staging environment: do not enter real patient data.',
    'hospital': <String, dynamic>{
      'name': 'Hospital profile pending',
      'location': 'Complete hospital details',
      'summary': 'Your care workspace is ready for patient-code connection.',
    },
    'doctor': <String, dynamic>{
      'name': 'Doctor profile',
      'title': 'Clinician',
      'expertise': 'Connect patients by code to start care episodes',
      'rating': 4,
    },
    'quick_access': <String>[
      'AI Supported CT Image Diagnose',
      'AI Supported X-ray Image Diagnose',
      'AI Supported MRI Image Diagnose',
      'Check Patient Medical Records',
      'Check Patient Recovery Plans',
      'Check Imaging Results',
      'Book Medical Equipment',
    ],
    'recent_activity': <String, dynamic>{
      'title': 'No patient activity yet',
      'time': '--:--',
    },
    'resources': <Map<String, dynamic>>[
      <String, dynamic>{'name': 'CT', 'available': 0, 'total': 0},
      <String, dynamic>{'name': 'MRI', 'available': 0, 'total': 0},
      <String, dynamic>{'name': 'X-ray', 'available': 0, 'total': 0},
      <String, dynamic>{'name': 'Ultrasound', 'available': 0, 'total': 0},
    ],
    'team': <String>['Invite team member', 'Connect patient', 'Create event'],
    ...source,
  };
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
                  const Icon(
                    Icons.verified_user_outlined,
                    color: DrAiColors.white,
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
                          const Icon(
                            Icons.account_circle_outlined,
                            color: DrAiColors.white,
                            size: 30,
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
                  'Operational summaries update as clinic data becomes available.',
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
      key: Key('doctor-panel-$title'),
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
    return SizedBox(
      height: 32,
      child: Semantics(
        button: true,
        enabled: false,
        label: '$label unavailable',
        child: ExcludeSemantics(
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: DrAiColors.inkStrong,
              borderRadius: BorderRadius.circular(DrAiRadii.md),
            ),
            child: Center(
              child: Text(
                label,
                style: const TextStyle(color: DrAiColors.outlineMuted),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
