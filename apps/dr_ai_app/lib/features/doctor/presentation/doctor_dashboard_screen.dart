import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/presentation/signup_reference_data.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:dr_ai_app/features/doctor/domain/doctor_profile.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:dr_ai_app/l10n/locale_controller.dart';
import 'package:dr_ai_app/shared/avatar/avatar_upload.dart';
import 'package:dr_ai_app/shared/widgets/account_request_center.dart';
import 'package:dr_ai_app/shared/widgets/account_security.dart';
import 'package:dr_ai_app/shared/widgets/dashboard_states.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:dr_ai_app/shared/widgets/sign_out_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

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
          message: context.l10n.pageLoadFailed,
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
        loading: () => ListView(
          padding: const EdgeInsets.all(DrAiSpacing.md),
          children: <Widget>[
            SizedBox(
              height: 180,
              child: DashboardLoadingView(
                label: context.l10n.loadingDoctorAccount,
              ),
            ),
            const AccountRequestCenter(role: AppRole.doctor),
          ],
        ),
        error: (error, stackTrace) => ListView(
          padding: const EdgeInsets.all(DrAiSpacing.md),
          children: <Widget>[
            SizedBox(
              height: 220,
              child: DashboardErrorView(
                message: context.l10n.loadAccountFailed,
                onRetry: () => ref.invalidate(doctorProfileProvider),
              ),
            ),
            const AccountRequestCenter(role: AppRole.doctor),
          ],
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
  late final TextEditingController _departmentController;
  late final TextEditingController _phoneController;
  late final TextEditingController _emailController;
  late String _country;
  late String _province;
  late String _city;
  late String _preferredLanguage;
  late String _avatarUrl;
  late String _persistedAvatarUrl;
  bool _saving = false;
  String? _statusMessage;

  @override
  void initState() {
    super.initState();
    _displayNameController = TextEditingController();
    _specialtyController = TextEditingController();
    _titleController = TextEditingController();
    _departmentController = TextEditingController();
    _phoneController = TextEditingController();
    _emailController = TextEditingController();
    _seedFields(widget.profile);
  }

  @override
  void didUpdateWidget(covariant _DoctorAccountView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.profile != widget.profile ||
        oldWidget.email != widget.email) {
      _seedFields(widget.profile);
    }
  }

  @override
  void dispose() {
    _displayNameController.dispose();
    _specialtyController.dispose();
    _titleController.dispose();
    _departmentController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  void _seedFields(DoctorProfile profile) {
    _displayNameController.text = profile.displayName;
    _specialtyController.text = profile.specialty ?? '';
    _titleController.text = profile.title;
    _departmentController.text = profile.department ?? '';
    _phoneController.text = profile.contactPhone ?? '';
    _emailController.text = widget.email;
    _country = _knownCountry(profile.country);
    _province = _knownProvince(_country, profile.province);
    _city = _knownCity(_country, _province, profile.city);
    _preferredLanguage = profile.preferredLanguage ?? 'English';
    _persistedAvatarUrl = profile.avatarUrl ?? '';
    _avatarUrl = _persistedAvatarUrl;
  }

  Future<void> _saveProfile() async {
    final profile = widget.profile;
    final payload = _currentPayload();
    final profileChanged =
        payload.displayName != profile.displayName ||
        payload.specialty != (profile.specialty ?? '') ||
        payload.title != profile.title ||
        payload.department != (profile.department ?? '') ||
        payload.contactPhone != (profile.contactPhone ?? '') ||
        payload.country != (profile.country ?? '') ||
        payload.province != (profile.province ?? '') ||
        payload.city != (profile.city ?? '') ||
        payload.preferredLanguage != (profile.preferredLanguage ?? 'English') ||
        payload.avatarUrl != (profile.avatarUrl ?? '');
    final emailChanged = payload.email != widget.email;
    if (!profileChanged && !emailChanged) {
      setState(() => _statusMessage = context.l10n.noAccountChanges);
      return;
    }
    if (payload.displayName.isEmpty || payload.title.isEmpty) {
      setState(() {
        _statusMessage = context.l10n.doctorIdentityRequired;
      });
      return;
    }
    if (payload.email.isNotEmpty && !_looksLikeEmail(payload.email)) {
      setState(() => _statusMessage = context.l10n.invalidEmail);
      return;
    }
    setState(() {
      _saving = true;
      _statusMessage = null;
    });
    try {
      if (emailChanged) {
        await ref
            .read(authControllerProvider.notifier)
            .updateAccountEmail(payload.email);
      }
      if (profileChanged) {
        await ref
            .read(repositoryProvider)
            .updateOwnDoctorProfile(
              displayName: payload.displayName,
              specialty: payload.specialty,
              title: payload.title,
              department: payload.department,
              contactPhone: payload.contactPhone,
              country: payload.country,
              province: payload.province,
              city: payload.city,
              preferredLanguage: payload.preferredLanguage,
              avatarUrl: payload.avatarUrl,
            );
        ref.invalidate(doctorProfileProvider);
      }
      if (mounted) {
        await ref
            .read(localeControllerProvider.notifier)
            .applyProfilePreference(payload.preferredLanguage);
      }
      if (mounted) {
        setState(() {
          _saving = false;
          _statusMessage = context.l10n.accountSaved;
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
          _statusMessage = context.l10n.accountSaveFailed;
        });
      }
    }
  }

  void _cancelChanges() {
    setState(() {
      final persistedAvatarUrl = _persistedAvatarUrl;
      _seedFields(widget.profile);
      _persistedAvatarUrl = persistedAvatarUrl;
      _avatarUrl = persistedAvatarUrl;
      _statusMessage = null;
    });
  }

  _DoctorAccountPayload _currentPayload() {
    return _DoctorAccountPayload(
      displayName: _displayNameController.text.trim(),
      specialty: _specialtyController.text.trim(),
      title: _titleController.text.trim(),
      department: _departmentController.text.trim(),
      contactPhone: _phoneController.text.trim(),
      email: _emailController.text.trim().toLowerCase(),
      country: _country.trim(),
      province: _province.trim(),
      city: _city.trim(),
      preferredLanguage: _preferredLanguage.trim(),
      avatarUrl: _avatarUrl.trim(),
    );
  }

  Future<void> _pickAvatar() async {
    try {
      final result = await pickAvatarImage();
      if (result == null || !mounted) {
        return;
      }
      setState(() {
        _saving = true;
        _statusMessage = null;
      });
      final profile = widget.profile;
      await ref
          .read(repositoryProvider)
          .updateOwnDoctorProfile(
            displayName: profile.displayName,
            specialty: profile.specialty ?? '',
            title: profile.title,
            department: profile.department ?? '',
            contactPhone: profile.contactPhone ?? '',
            country: profile.country ?? '',
            province: profile.province ?? '',
            city: profile.city ?? '',
            preferredLanguage: profile.preferredLanguage ?? 'English',
            avatarUrl: result.dataUrl,
          );
      if (mounted) {
        setState(() {
          _persistedAvatarUrl = result.dataUrl;
          _avatarUrl = result.dataUrl;
          _saving = false;
        });
      }
    } on AvatarUploadException catch (error) {
      if (mounted) {
        setState(() {
          _saving = false;
          _statusMessage = error.message;
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
          _statusMessage = context.l10n.accountSaveFailed;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final desktop = MediaQuery.sizeOf(context).width >= 1080;
    final profile = widget.profile;
    return ColoredBox(
      color: DrAiColors.pageBackground,
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
                  context.l10n.doctorAccount,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: DrAiColors.brandDark,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: DrAiSpacing.xs),
                Text(
                  context.l10n.doctorAccountDescription,
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
                          avatarUrl: _avatarUrl,
                          onAvatarPressed: _pickAvatar,
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
                        avatarUrl: _avatarUrl,
                        onAvatarPressed: _pickAvatar,
                      ),
                      const SizedBox(height: DrAiSpacing.md),
                      _formPanel(),
                    ],
                  ),
                const SizedBox(height: DrAiSpacing.lg),
                const AccountRequestCenter(role: AppRole.doctor),
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
      hospitalName: widget.profile.hospitalName,
      departmentController: _departmentController,
      phoneController: _phoneController,
      emailController: _emailController,
      country: _country,
      province: _province,
      city: _city,
      onCountryChanged: _saving ? null : _setCountry,
      onProvinceChanged: _saving ? null : _setProvince,
      onCityChanged: _saving ? null : _setCity,
    );
  }

  void _setCountry(String? value) {
    if (value == null) {
      return;
    }
    final province = _knownProvince(value, null);
    setState(() {
      _country = value;
      _province = province;
      _city = _knownCity(value, province, null);
    });
  }

  void _setProvince(String? value) {
    if (value == null) {
      return;
    }
    setState(() {
      _province = value;
      _city = _knownCity(_country, value, null);
    });
  }

  void _setCity(String? value) {
    if (value != null) {
      setState(() => _city = value);
    }
  }
}

class _DoctorAccountPayload {
  const _DoctorAccountPayload({
    required this.displayName,
    required this.specialty,
    required this.title,
    required this.department,
    required this.contactPhone,
    required this.email,
    required this.country,
    required this.province,
    required this.city,
    required this.preferredLanguage,
    required this.avatarUrl,
  });

  final String displayName;
  final String specialty;
  final String title;
  final String department;
  final String contactPhone;
  final String email;
  final String country;
  final String province;
  final String city;
  final String preferredLanguage;
  final String avatarUrl;
}

class _DoctorAccountProfileCard extends StatelessWidget {
  const _DoctorAccountProfileCard({
    required this.profile,
    required this.email,
    required this.avatarUrl,
    required this.onAvatarPressed,
  });

  final DoctorProfile profile;
  final String email;
  final String avatarUrl;
  final VoidCallback onAvatarPressed;

  @override
  Widget build(BuildContext context) {
    final location = _joinRecorded(context, <String?>[
      profile.city,
      profile.province,
      profile.country,
    ]);
    final avatar = avatarImageProvider(avatarUrl);
    return _DoctorAccountCard(
      title: context.l10n.doctorProfile,
      icon: Icons.badge_outlined,
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
                  child: IconButton.filled(
                    key: const Key('doctor-account-avatar-upload-button'),
                    tooltip: context.l10n.uploadAvatar,
                    onPressed: onAvatarPressed,
                    icon: const Icon(Icons.photo_camera_outlined, size: 16),
                    style: IconButton.styleFrom(
                      backgroundColor: DrAiColors.accentIndigo,
                      foregroundColor: DrAiColors.white,
                      side: const BorderSide(color: DrAiColors.white, width: 2),
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
            _recorded(context, profile.title),
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
            title: _recorded(context, profile.hospitalName),
            subtitle: location,
            tag: _emptyToNull(profile.department),
          ),
          const SizedBox(height: DrAiSpacing.lg),
          const Divider(color: DrAiColors.outline),
          const SizedBox(height: DrAiSpacing.md),
          _ProfileSummaryRow(
            icon: Icons.verified_user_outlined,
            title: context.l10n.verificationStatus,
            subtitle: profile.isRecentlyActive
                ? context.l10n.activeDoctorAccount
                : _doctorActivityLabel(context, profile.lastActiveAt),
            accent: profile.isRecentlyActive
                ? DrAiColors.accentMint
                : DrAiColors.mutedInk,
          ),
          const SizedBox(height: DrAiSpacing.lg),
          const Divider(color: DrAiColors.outline),
          const SizedBox(height: DrAiSpacing.md),
          _ProfileSummaryRow(
            icon: Icons.alternate_email_outlined,
            title: context.l10n.contact,
            subtitle: _doctorContact(
              context,
              phone: profile.contactPhone,
              email: email,
            ),
          ),
          const SizedBox(height: DrAiSpacing.lg),
          const SignOutButton(),
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
    required this.hospitalName,
    required this.departmentController,
    required this.phoneController,
    required this.emailController,
    required this.country,
    required this.province,
    required this.city,
    required this.onCountryChanged,
    required this.onProvinceChanged,
    required this.onCityChanged,
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
  final String hospitalName;
  final TextEditingController departmentController;
  final TextEditingController phoneController;
  final TextEditingController emailController;
  final String country;
  final String province;
  final String city;
  final ValueChanged<String?>? onCountryChanged;
  final ValueChanged<String?>? onProvinceChanged;
  final ValueChanged<String?>? onCityChanged;

  @override
  Widget build(BuildContext context) {
    return _DoctorAccountCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          _DoctorAccountSection(
            icon: Icons.person_outline,
            title: context.l10n.clinicalIdentity,
            child: _ResponsiveFieldGrid(
              children: <Widget>[
                _DoctorAccountTextField(
                  controller: displayNameController,
                  label: context.l10n.displayName,
                  keyName: 'doctor-account-display-name-field',
                ),
                _DoctorAccountTextField(
                  controller: specialtyController,
                  label: context.l10n.specialty,
                  keyName: 'doctor-account-specialty-field',
                ),
                _DoctorAccountTextField(
                  controller: titleController,
                  label: context.l10n.title,
                  keyName: 'doctor-account-title-field',
                ),
              ],
            ),
          ),
          const _AccountDivider(),
          _DoctorAccountSection(
            icon: Icons.apartment_outlined,
            title: context.l10n.hospitalLocation,
            child: Column(
              children: <Widget>[
                _ResponsiveFieldGrid(
                  children: <Widget>[
                    _ReadOnlyAccountField(
                      label: context.l10n.hospitalManaged,
                      value: _recorded(context, hospitalName),
                      keyName: 'doctor-account-hospital-read-only',
                    ),
                    _DoctorAccountTextField(
                      controller: departmentController,
                      label: context.l10n.department,
                      keyName: 'doctor-account-department-field',
                    ),
                  ],
                ),
                const SizedBox(height: DrAiSpacing.md),
                _ResponsiveFieldGrid(
                  children: <Widget>[
                    _DoctorAccountDropdown(
                      value: country,
                      items: _countryOptions(country),
                      label: context.l10n.countryRegion,
                      keyName: 'doctor-account-country-field',
                      onChanged: onCountryChanged,
                    ),
                    _DoctorAccountDropdown(
                      value: province,
                      items: _provinceOptions(country, province),
                      label: context.l10n.province,
                      keyName: 'doctor-account-province-field',
                      onChanged: onProvinceChanged,
                    ),
                    _DoctorAccountDropdown(
                      value: city,
                      items: _cityOptions(country, province, city),
                      label: context.l10n.city,
                      keyName: 'doctor-account-city-field',
                      onChanged: onCityChanged,
                    ),
                  ],
                ),
              ],
            ),
          ),
          const _AccountDivider(),
          _DoctorAccountSection(
            icon: Icons.phone_outlined,
            title: context.l10n.contact,
            child: _ResponsiveFieldGrid(
              children: <Widget>[
                _DoctorAccountTextField(
                  controller: phoneController,
                  label: context.l10n.phone,
                  keyName: 'doctor-account-phone-field',
                ),
                _DoctorAccountTextField(
                  controller: emailController,
                  label: context.l10n.emailOptional,
                  keyName: 'doctor-account-email-field',
                ),
              ],
            ),
          ),
          const _AccountDivider(),
          _DoctorAccountSection(
            icon: Icons.lock_outline,
            title: context.l10n.security,
            child: const AccountSecuritySection(keyPrefix: 'doctor-account'),
          ),
          const _AccountDivider(),
          _DoctorAccountSection(
            icon: Icons.settings_outlined,
            title: context.l10n.languagePreferences,
            child: _ResponsiveFieldGrid(
              children: <Widget>[
                DropdownButtonFormField<String>(
                  key: const Key('doctor-account-language-field'),
                  initialValue: preferredLanguage,
                  isExpanded: true,
                  decoration: InputDecoration(
                    labelText: context.l10n.interfaceLanguage,
                  ),
                  items: _languageOptions(preferredLanguage)
                      .map(
                        (language) => DropdownMenuItem<String>(
                          value: language,
                          child: Text(
                            language == 'Simplified Chinese'
                                ? context.l10n.simplifiedChinese
                                : context.l10n.english,
                          ),
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
                color: statusMessage == context.l10n.accountSaved
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
                child: Text(context.l10n.cancel),
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
                    : Text(context.l10n.saveChanges),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _DoctorAccountCard extends StatelessWidget {
  const _DoctorAccountCard({required this.child, this.title, this.icon});

  final Widget child;
  final String? title;
  final IconData? icon;

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
      child: ClipRRect(
        borderRadius: BorderRadius.circular(DrAiRadii.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            if (title != null)
              Container(
                color: DrAiColors.sectionHeader,
                padding: const EdgeInsets.symmetric(
                  horizontal: DrAiSpacing.md,
                  vertical: DrAiSpacing.sm,
                ),
                child: Row(
                  children: <Widget>[
                    if (icon != null) ...<Widget>[
                      Icon(icon, color: DrAiColors.white, size: 21),
                      const SizedBox(width: DrAiSpacing.xs),
                    ],
                    Expanded(
                      child: Text(
                        title!,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(
                              color: DrAiColors.white,
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                    ),
                  ],
                ),
              ),
            Padding(
              padding: const EdgeInsets.all(DrAiSpacing.lg),
              child: child,
            ),
          ],
        ),
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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Container(
          decoration: BoxDecoration(
            color: DrAiColors.sectionHeader,
            borderRadius: BorderRadius.circular(DrAiRadii.md),
          ),
          padding: const EdgeInsets.symmetric(
            horizontal: DrAiSpacing.md,
            vertical: DrAiSpacing.sm,
          ),
          child: Row(
            children: <Widget>[
              Icon(icon, color: DrAiColors.white, size: 21),
              const SizedBox(width: DrAiSpacing.xs),
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: DrAiColors.white,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: DrAiSpacing.md),
        child,
      ],
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

class _DoctorAccountDropdown extends StatelessWidget {
  const _DoctorAccountDropdown({
    required this.value,
    required this.items,
    required this.label,
    required this.keyName,
    required this.onChanged,
  });

  final String value;
  final List<String> items;
  final String label;
  final String keyName;
  final ValueChanged<String?>? onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String>(
      key: Key(keyName),
      initialValue: value,
      isExpanded: true,
      decoration: InputDecoration(labelText: label),
      items: items
          .map(
            (item) => DropdownMenuItem<String>(
              value: item,
              child: Text(
                item.isEmpty
                    ? context.l10n.notRecorded
                    : context.l10n.stableValue(item),
              ),
            ),
          )
          .toList(),
      onChanged: onChanged,
    );
  }
}

class _ReadOnlyAccountField extends StatelessWidget {
  const _ReadOnlyAccountField({
    required this.label,
    required this.value,
    this.keyName,
  });

  final String label;
  final String value;
  final String? keyName;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      key: keyName == null ? null : Key(keyName!),
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

String _recorded(BuildContext context, String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return context.l10n.notRecorded;
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

String _joinRecorded(BuildContext context, List<String?> values) {
  final recorded = values
      .map((value) => value?.trim())
      .whereType<String>()
      .where((value) => value.isNotEmpty)
      .toList();
  if (recorded.isEmpty) {
    return context.l10n.notRecorded;
  }
  return recorded.join(', ');
}

String _doctorContact(
  BuildContext context, {
  required String? phone,
  required String email,
}) {
  final rows = <String>[
    if (_emptyToNull(phone) case final value?) '${context.l10n.phone}: $value',
    if (_emptyToNull(email) case final value?) '${context.l10n.email}: $value',
  ];
  return rows.isEmpty ? context.l10n.notRecorded : rows.join('\n');
}

String _doctorActivityLabel(BuildContext context, DateTime? lastActiveAt) {
  if (lastActiveAt == null) {
    return context.l10n.inactiveDoctorAccount;
  }
  final local = lastActiveAt.toLocal();
  final date =
      '${local.year.toString().padLeft(4, '0')}-'
      '${local.month.toString().padLeft(2, '0')}-'
      '${local.day.toString().padLeft(2, '0')}';
  return context.l10n.doctorLastOnline(date);
}

bool _looksLikeEmail(String value) {
  return RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value);
}

List<String> _languageOptions(String selected) {
  final options = <String>['English', 'Simplified Chinese'];
  if (selected.trim().isNotEmpty && !options.contains(selected)) {
    options.add(selected);
  }
  return options;
}

String _knownCountry(String? saved) {
  final value = _emptyToNull(saved);
  return value ?? locationCountries.first.name;
}

String _knownProvince(String country, String? saved) {
  final value = _emptyToNull(saved);
  final regions = _regions(country);
  return value ?? (regions.isEmpty ? '' : regions.first.name);
}

String _knownCity(String country, String province, String? saved) {
  final value = _emptyToNull(saved);
  final cities = _cities(country, province);
  return value ?? (cities.isEmpty ? '' : cities.first);
}

List<String> _countryOptions(String selected) {
  return _withSelected(
    locationCountries.map((country) => country.name),
    selected,
  );
}

List<String> _provinceOptions(String country, String selected) {
  return _withSelected(
    _regions(country).map((region) => region.name),
    selected,
  );
}

List<String> _cityOptions(String country, String province, String selected) {
  return _withSelected(_cities(country, province), selected);
}

List<LocationRegion> _regions(String country) {
  for (final item in locationCountries) {
    if (item.name == country) {
      return item.regions;
    }
  }
  return const <LocationRegion>[];
}

List<String> _cities(String country, String province) {
  for (final region in _regions(country)) {
    if (region.name == province) {
      return region.cities;
    }
  }
  return const <String>[];
}

List<String> _withSelected(Iterable<String> values, String selected) {
  final options = values.toList();
  if (selected.trim().isNotEmpty && !options.contains(selected)) {
    options.add(selected);
  }
  if (options.isEmpty) {
    options.add('');
  }
  return options;
}

class _DoctorDashboard extends StatelessWidget {
  const _DoctorDashboard({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context) {
    final dashboardData = _doctorDashboardData(context, data.data);
    return ColoredBox(
      color: DrAiColors.pageBackground,
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

Map<String, dynamic> _doctorDashboardData(
  BuildContext context,
  Map<String, dynamic> source,
) {
  if (source.containsKey('hospital') && source.containsKey('doctor')) {
    return source;
  }
  return <String, dynamic>{
    'safety_label': context.l10n.stagingNotice,
    'hospital': <String, dynamic>{
      'name': context.l10n.hospitalProfilePending,
      'location': context.l10n.completeHospitalDetails,
      'summary': context.l10n.careWorkspaceReady,
    },
    'doctor': <String, dynamic>{
      'name': context.l10n.doctorProfile,
      'title': context.l10n.clinician,
      'expertise': context.l10n.connectPatientsEpisodes,
      'rating': 4,
    },
    'recent_activity': <String, dynamic>{
      'title': context.l10n.noPatientActivity,
      'time': '--:--',
    },
    'resources': <Map<String, dynamic>>[
      <String, dynamic>{'name': 'CT', 'available': 0, 'total': 0},
      <String, dynamic>{'name': 'MRI', 'available': 0, 'total': 0},
      <String, dynamic>{'name': context.l10n.xray, 'available': 0, 'total': 0},
      <String, dynamic>{
        'name': context.l10n.ultrasound,
        'available': 0,
        'total': 0,
      },
    ],
    'team': <String>[
      context.l10n.inviteTeamMember,
      context.l10n.connectPatient,
      context.l10n.createEvent,
    ],
    ...source,
  };
}

class _DoctorIdentityColumn extends StatelessWidget {
  const _DoctorIdentityColumn({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final team = List<String>.from(data['team'] as List);
    return _DoctorPanel(
      title: context.l10n.teamManagement,
      icon: Icons.groups_outlined,
      child: Column(
        children: <Widget>[
          for (final member in team) ...<Widget>[
            _TeamManagementTile(label: context.l10n.stableValue(member)),
            const SizedBox(height: DrAiSpacing.xs),
          ],
          Text(
            Localizations.localeOf(context).languageCode == 'zh'
                ? '团队信息由机构管理员维护；医生工作区仅供查看。'
                : 'Team membership is administrator-managed and read-only here.',
            style: const TextStyle(color: DrAiColors.inkSecondary),
          ),
        ],
      ),
    );
  }
}

class _TeamManagementTile extends StatelessWidget {
  const _TeamManagementTile({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      constraints: const BoxConstraints(minHeight: 82),
      padding: const EdgeInsets.all(DrAiSpacing.sm),
      decoration: BoxDecoration(
        color: DrAiColors.ink,
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Row(
        children: <Widget>[
          Icon(
            Icons.account_circle_outlined,
            color: DrAiColors.white,
            size: 30,
          ),
          const SizedBox(width: DrAiSpacing.sm),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: DrAiColors.white,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DoctorMainColumn extends StatelessWidget {
  const _DoctorMainColumn({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final quickAccess = <_DoctorQuickAccessItem>[
      _DoctorQuickAccessItem(
        keyName: 'imaging',
        title: context.l10n.imagingRecordsManualReview,
        description: context.l10n.imagingRecordsManualReviewDescription,
        icon: Icons.image_search_outlined,
        destination: '/doctor/patients?section=imaging',
      ),
      _DoctorQuickAccessItem(
        keyName: 'medical-records',
        title: context.l10n.patientMedicalRecords,
        description: context.l10n.patientMedicalRecordsDescription,
        icon: Icons.description_outlined,
        destination: '/doctor/patients?section=medicalHistory',
      ),
      _DoctorQuickAccessItem(
        keyName: 'recovery-plans',
        title: context.l10n.patientRecoveryPlans,
        description: context.l10n.patientRecoveryPlansDescription,
        icon: Icons.assignment_outlined,
        destination: '/doctor/patients?section=recoveryPlans',
      ),
      _DoctorQuickAccessItem(
        keyName: 'resources',
        title: context.l10n.medicalResourcesReadOnly,
        description: context.l10n.medicalResourcesReadOnlyDescription,
        icon: Icons.medical_services_outlined,
        destination: '/doctor/resources',
      ),
      _DoctorQuickAccessItem(
        keyName: 'hospital-availability',
        title: Localizations.localeOf(context).languageCode == 'zh'
            ? '科室资源可用情况' : 'Department availability',
        description: Localizations.localeOf(context).languageCode == 'zh'
            ? '查看已授权科室的运营资源状态' : 'View operational resources in your assigned departments',
        icon: Icons.inventory_2_outlined,
        destination: '/doctor/hospital-resources',
      ),
      _DoctorQuickAccessItem(
        keyName: 'payer-requests',
        title: context.l10n.payerRequests,
        description: context.l10n.payerRequestsDescription,
        icon: Icons.outbox_outlined,
        destination: '/doctor/payer-requests',
      ),
    ];
    return Column(
      children: <Widget>[
        _DoctorPanel(
          title: context.l10n.quickAccess,
          icon: Icons.adjust,
          child: GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: MediaQuery.sizeOf(context).width >= 1120 ? 2 : 1,
              childAspectRatio: 2.25,
              crossAxisSpacing: DrAiSpacing.xs,
              mainAxisSpacing: DrAiSpacing.xs,
            ),
            itemCount: quickAccess.length,
            itemBuilder: (context, index) {
              final item = quickAccess[index];
              return Semantics(
                button: true,
                label: '${item.title}. ${item.description}',
                child: InkWell(
                  key: Key('doctor-quick-access-${item.keyName}'),
                  borderRadius: BorderRadius.circular(DrAiRadii.md),
                  onTap: () => context.go(item.destination),
                  child: Container(
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
                            item.icon,
                            size: 44,
                            color: DrAiColors.brand.withValues(alpha: 0.22),
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.all(DrAiSpacing.md),
                          child: Align(
                            alignment: Alignment.centerLeft,
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: <Widget>[
                                Text(
                                  item.title,
                                  style: const TextStyle(
                                    color: DrAiColors.brandDark,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Padding(
                                  padding: const EdgeInsets.only(right: 44),
                                  child: Text(
                                    item.description,
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      color: DrAiColors.inkSecondary,
                                      fontSize: 12,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _DoctorQuickAccessItem {
  const _DoctorQuickAccessItem({
    required this.keyName,
    required this.title,
    required this.description,
    required this.icon,
    required this.destination,
  });

  final String keyName;
  final String title;
  final String description;
  final IconData icon;
  final String destination;
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
          title: context.l10n.recentActivities,
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
                  context.l10n.stableValue(activity['title'] as String),
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
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: <Widget>[
                    Text(
                      context.l10n.cancel,
                      style: const TextStyle(color: DrAiColors.patientAccent),
                    ),
                    const SizedBox(width: DrAiSpacing.lg),
                    Text(
                      context.l10n.ok,
                      style: const TextStyle(color: DrAiColors.patientAccent),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: DrAiSpacing.xs),
        _DoctorPanel(
          title: context.l10n.resourceOverview,
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
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        context.l10n.medicalEquipment,
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    for (final resource in resources)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2),
                        child: Row(
                          children: <Widget>[
                            Expanded(
                              child: Text(
                                context.l10n.stableValue(
                                  resource['name'] as String,
                                ),
                              ),
                            ),
                            Text(
                              context.l10n.resourceAvailable(
                                resource['available'] as int,
                                resource['total'] as int,
                              ),
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
                context.l10n.medicationStocks,
                context.l10n.staffingLevels,
                context.l10n.bedAvailability,
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
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  context.l10n.operationalSummary,
                  style: const TextStyle(
                    fontSize: 11,
                    color: DrAiColors.mutedInk,
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
