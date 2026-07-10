import 'dart:async';

import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/data/dr_ai_repository.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/auth/presentation/signup_reference_data.dart';
import 'package:dr_ai_app/l10n/l10n.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({this.initiallyRegistering = false, super.key});

  final bool initiallyRegistering;

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _accountController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _verificationCodeController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _middleNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _birthDateController = TextEditingController();
  final _homeAddressController = TextEditingController();
  final _hospitalController = TextEditingController();
  bool _obscurePassword = true;
  bool _isRegistering = false;
  bool _termsAccepted = false;
  bool _customHospital = false;
  bool _registrationCodeRequesting = false;
  String? _registrationCodeStatus;
  AppRole _selectedRole = AppRole.patient;
  String _gender = 'Unspecified';
  DialingCodeOption _dialingCode = dialingCodeOptions.firstWhere(
    (item) => item.isoCode == 'CN',
  );
  String _country = 'China';
  String _province = 'Guangdong';
  String _city = 'Shenzhen';
  Timer? _feedbackTimer;
  String? _scheduledFeedback;

  @override
  void initState() {
    super.initState();
    _isRegistering = widget.initiallyRegistering;
  }

  @override
  void dispose() {
    _feedbackTimer?.cancel();
    _accountController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _verificationCodeController.dispose();
    _firstNameController.dispose();
    _middleNameController.dispose();
    _lastNameController.dispose();
    _birthDateController.dispose();
    _homeAddressController.dispose();
    _hospitalController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    final controller = ref.read(authControllerProvider.notifier);
    if (_isRegistering) {
      final displayName = _displayName();
      final phone = _fullPhoneNumber();
      await controller.register(
        phoneNumber: phone,
        email: _emailController.text,
        password: _passwordController.text,
        role: _selectedRole,
        verificationCode: _verificationCodeController.text,
        termsAccepted: _termsAccepted,
        patientProfile: _selectedRole == AppRole.patient
            ? PatientSignupProfile(
                displayName: displayName,
                birthDate: _birthDateController.text,
                gender: _gender,
                contactPhone: phone,
                country: _country,
                province: _province,
                city: _city,
                homeAddress: _homeAddressController.text,
              )
            : null,
        doctorProfile: _selectedRole == AppRole.doctor
            ? DoctorSignupProfile(
                displayName: displayName,
                birthDate: _birthDateController.text,
                gender: _gender,
                contactPhone: phone,
                country: _country,
                province: _province,
                city: _city,
                hospitalName: _hospitalController.text,
                customHospital: _customHospital,
              )
            : null,
      );
    } else {
      await controller.login(_loginAccount(), _passwordController.text);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final errorMessage = auth.value?.errorMessage;
    final noticeMessage = auth.value?.noticeMessage;
    _ensureFeedbackTimer(errorMessage ?? noticeMessage);
    final desktop = MediaQuery.sizeOf(context).width >= 980;
    return Scaffold(
      backgroundColor: DrAiColors.white,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: EdgeInsets.symmetric(
              horizontal: desktop ? DrAiSpacing.xxl : DrAiSpacing.md,
              vertical: desktop ? DrAiSpacing.lg : DrAiSpacing.md,
            ),
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: desktop ? 1180 : 430),
              child: Form(
                key: _formKey,
                child: _isRegistering
                    ? _registrationShell(
                        auth,
                        errorMessage,
                        noticeMessage,
                        desktop,
                      )
                    : _loginShell(auth, errorMessage, noticeMessage, desktop),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _loginShell(
    AsyncValue<AuthState> auth,
    String? errorMessage,
    String? noticeMessage,
    bool desktop,
  ) {
    return DecoratedBox(
      decoration: _panelDecoration(),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            const Center(child: _AuthWordmark()),
            const SizedBox(height: DrAiSpacing.md),
            Text(
              context.l10n.welcome,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: DrAiColors.ink,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            Text(
              context.l10n.signInDescription,
              textAlign: TextAlign.center,
              style: TextStyle(color: DrAiColors.mutedInk),
            ),
            const SizedBox(height: DrAiSpacing.lg),
            _loginAccountField(),
            const SizedBox(height: DrAiSpacing.md),
            _passwordField(),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                key: const Key('forgot-password-button'),
                onPressed: _showForgotPassword,
                child: Text(context.l10n.forgotPassword),
              ),
            ),
            ..._statusMessages(errorMessage, noticeMessage),
            const SizedBox(height: DrAiSpacing.lg),
            _primaryButton(
              key: const Key('login-button'),
              auth: auth,
              text: context.l10n.signIn,
              icon: Icons.arrow_forward,
            ),
            const SizedBox(height: DrAiSpacing.sm),
            _authModeButton(),
            TextButton.icon(
              key: const Key('login-privacy-support-link'),
              onPressed: () {
                ref.read(authControllerProvider.notifier).clearFeedback();
                context.go('/privacy');
              },
              icon: const Icon(Icons.privacy_tip_outlined),
              label: Text(context.l10n.privacySupport),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            Text(
              context.l10n.stagingNotice,
              textAlign: TextAlign.center,
              style: TextStyle(color: DrAiColors.mutedInk, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _registrationShell(
    AsyncValue<AuthState> auth,
    String? errorMessage,
    String? noticeMessage,
    bool desktop,
  ) {
    final form = _registrationForm(auth, errorMessage, noticeMessage, desktop);
    if (!desktop) {
      return DecoratedBox(
        decoration: _panelDecoration(),
        child: Padding(
          padding: const EdgeInsets.all(DrAiSpacing.md),
          child: form,
        ),
      );
    }
    return DecoratedBox(
      decoration: BoxDecoration(
        color: DrAiColors.white,
        border: Border.all(color: const Color(0xFFCED3DC), width: 2),
        borderRadius: BorderRadius.circular(DrAiRadii.xl),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Color(0x160A0076),
            blurRadius: 42,
            offset: Offset(0, 20),
          ),
        ],
      ),
      child: Column(
        children: <Widget>[
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: DrAiSpacing.xl,
              vertical: DrAiSpacing.md,
            ),
            child: Row(
              children: <Widget>[
                const _AuthWordmark(size: 30),
                const Spacer(),
                Text(
                  context.l10n.alreadyHaveAccount,
                  style: TextStyle(color: DrAiColors.inkSecondary),
                ),
                TextButton(
                  onPressed: _toggleMode,
                  child: Text(context.l10n.logIn),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                const SizedBox(width: 250, child: _RegistrationStepRail()),
                const VerticalDivider(width: 1),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(34, 30, 34, 34),
                    child: form,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _registrationForm(
    AsyncValue<AuthState> auth,
    String? errorMessage,
    String? noticeMessage,
    bool desktop,
  ) {
    final isDoctor = _selectedRole == AppRole.doctor;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Expanded(
              child: Column(
                crossAxisAlignment: desktop
                    ? CrossAxisAlignment.start
                    : CrossAxisAlignment.center,
                children: <Widget>[
                  Text(
                    isDoctor
                        ? context.l10n.doctorRegistration
                        : context.l10n.createAccount,
                    textAlign: desktop ? TextAlign.start : TextAlign.center,
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                      color: DrAiColors.brandDark,
                    ),
                  ),
                  const SizedBox(height: DrAiSpacing.xs),
                  Text(
                    isDoctor
                        ? context.l10n.createAccountDoctorDescription
                        : context.l10n.createAccountPatientDescription,
                    textAlign: desktop ? TextAlign.start : TextAlign.center,
                    style: const TextStyle(color: DrAiColors.inkSecondary),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _roleSelector(),
        const SizedBox(height: DrAiSpacing.lg),
        _formSection(
          title: context.l10n.accountInformation,
          icon: Icons.person,
          children: <Widget>[
            _responsivePair(
              desktop,
              _phoneField(required: true),
              _optionalEmailField(),
            ),
            const SizedBox(height: DrAiSpacing.md),
            _responsivePair(desktop, _verificationField(), _passwordField()),
            const SizedBox(height: DrAiSpacing.md),
            _confirmPasswordField(),
          ],
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _formSection(
          title: context.l10n.personalInformation,
          icon: Icons.badge_outlined,
          children: <Widget>[
            _nameFields(desktop),
            const SizedBox(height: DrAiSpacing.md),
            _responsivePair(desktop, _birthDateField(), _genderField()),
          ],
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _formSection(
          title: isDoctor
              ? context.l10n.hospitalInformation
              : context.l10n.homeAddress,
          icon: isDoctor ? Icons.local_hospital_outlined : Icons.home_outlined,
          children: <Widget>[
            _locationFields(desktop),
            if (!isDoctor) ...<Widget>[
              const SizedBox(height: DrAiSpacing.md),
              _textField(
                controller: _homeAddressController,
                label: context.l10n.specificHomeAddress,
                keyName: 'signup-home-address-field',
                minLines: 1,
                maxLines: 2,
                required: true,
              ),
            ],
            if (isDoctor) ...<Widget>[
              const SizedBox(height: DrAiSpacing.md),
              _hospitalFields(desktop),
            ],
          ],
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _termsRow(),
        ..._statusMessages(errorMessage, noticeMessage),
        const SizedBox(height: DrAiSpacing.lg),
        Align(
          alignment: desktop ? Alignment.centerRight : Alignment.center,
          child: SizedBox(
            width: desktop ? 220 : double.infinity,
            child: _primaryButton(
              key: const Key('login-button'),
              auth: auth,
              text: context.l10n.next,
              icon: Icons.arrow_forward,
            ),
          ),
        ),
        if (!desktop) ...<Widget>[
          const SizedBox(height: DrAiSpacing.sm),
          _authModeButton(),
        ],
      ],
    );
  }

  Widget _loginAccountField() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        SizedBox(
          width: 130,
          child: DropdownButtonFormField<DialingCodeOption>(
            key: const Key('login-country-code-field'),
            initialValue: _dialingCode,
            isExpanded: true,
            menuMaxHeight: 360,
            borderRadius: _menuBorderRadius,
            dropdownColor: DrAiColors.white,
            icon: const Icon(Icons.keyboard_arrow_down_rounded),
            style: _menuTextStyle,
            decoration: InputDecoration(
              labelText: context.l10n.code,
              border: OutlineInputBorder(),
            ),
            selectedItemBuilder: (context) => dialingCodeOptions
                .map(
                  (item) =>
                      Text(item.dialCode, overflow: TextOverflow.ellipsis),
                )
                .toList(),
            items: dialingCodeOptions
                .map(
                  (item) => DropdownMenuItem<DialingCodeOption>(
                    value: item,
                    child: Text('${item.isoCode} ${item.dialCode}'),
                  ),
                )
                .toList(),
            onChanged: (value) {
              if (value != null) {
                setState(() => _dialingCode = value);
              }
            },
          ),
        ),
        const SizedBox(width: DrAiSpacing.sm),
        Expanded(
          child: TextFormField(
            key: const Key('email-field'),
            controller: _accountController,
            autofillHints: const <String>[
              AutofillHints.email,
              AutofillHints.telephoneNumber,
            ],
            keyboardType: TextInputType.emailAddress,
            decoration: InputDecoration(
              labelText: context.l10n.emailOrPhone,
              border: OutlineInputBorder(),
            ),
            validator: (value) {
              final account = value?.trim() ?? '';
              if (!_isEmail(account) &&
                  !_isPhone(_phoneWithDialCode(account))) {
                return context.l10n.invalidAccount;
              }
              return null;
            },
          ),
        ),
      ],
    );
  }

  Widget _phoneField({required bool required}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        SizedBox(
          width: 130,
          child: DropdownButtonFormField<DialingCodeOption>(
            key: const Key('signup-country-code-field'),
            initialValue: _dialingCode,
            isExpanded: true,
            menuMaxHeight: 360,
            borderRadius: _menuBorderRadius,
            dropdownColor: DrAiColors.white,
            icon: const Icon(Icons.keyboard_arrow_down_rounded),
            style: _menuTextStyle,
            decoration: InputDecoration(
              labelText: context.l10n.code,
              border: OutlineInputBorder(),
            ),
            selectedItemBuilder: (context) => dialingCodeOptions
                .map(
                  (item) =>
                      Text(item.dialCode, overflow: TextOverflow.ellipsis),
                )
                .toList(),
            items: dialingCodeOptions
                .map(
                  (item) => DropdownMenuItem<DialingCodeOption>(
                    value: item,
                    child: Text('${item.isoCode} ${item.dialCode}'),
                  ),
                )
                .toList(),
            onChanged: (value) {
              if (value != null) {
                setState(() => _dialingCode = value);
              }
            },
          ),
        ),
        const SizedBox(width: DrAiSpacing.sm),
        Expanded(
          child: TextFormField(
            key: const Key('signup-phone-field'),
            controller: _phoneController,
            keyboardType: TextInputType.phone,
            decoration: InputDecoration(
              labelText: context.l10n.phoneNumber,
              hintText: context.l10n.enterPhoneNumber,
              border: OutlineInputBorder(),
            ),
            validator: (value) {
              final phone = value?.trim() ?? '';
              if (required && phone.isEmpty) {
                return context.l10n.phoneRequired;
              }
              if (phone.isNotEmpty && !_isPhone(_fullPhoneNumber())) {
                return context.l10n.invalidPhone;
              }
              return null;
            },
          ),
        ),
      ],
    );
  }

  Widget _optionalEmailField() {
    return TextFormField(
      key: const Key('signup-email-field'),
      controller: _emailController,
      keyboardType: TextInputType.emailAddress,
      decoration: InputDecoration(
        labelText: context.l10n.emailOptional,
        border: OutlineInputBorder(),
      ),
      validator: (value) {
        final email = value?.trim() ?? '';
        if (email.isNotEmpty && !_isEmail(email)) {
          return context.l10n.invalidEmail;
        }
        return null;
      },
    );
  }

  Widget _passwordField() {
    return TextFormField(
      key: const Key('password-field'),
      controller: _passwordController,
      autofillHints: const <String>[AutofillHints.password],
      obscureText: _obscurePassword,
      decoration: InputDecoration(
        labelText: context.l10n.password,
        helperText: _isRegistering ? context.l10n.passwordGuidance : null,
        helperMaxLines: 2,
        helperStyle: const TextStyle(
          color: DrAiColors.mutedInk,
          fontSize: 11,
          height: 1.25,
        ),
        border: const OutlineInputBorder(),
        suffixIcon: IconButton(
          tooltip: _obscurePassword
              ? context.l10n.showPassword
              : context.l10n.hidePassword,
          onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
          icon: Icon(
            _obscurePassword
                ? Icons.visibility_outlined
                : Icons.visibility_off_outlined,
          ),
        ),
      ),
      validator: (value) {
        final password = value ?? '';
        if (password.isEmpty) {
          return context.l10n.enterPassword;
        }
        if (_isRegistering && (password.length < 8 || password.length > 20)) {
          return context.l10n.passwordLength;
        }
        return null;
      },
      onFieldSubmitted: (_) => _submit(),
    );
  }

  Widget _confirmPasswordField() {
    return TextFormField(
      key: const Key('confirm-password-field'),
      controller: _confirmPasswordController,
      obscureText: _obscurePassword,
      decoration: InputDecoration(
        labelText: context.l10n.confirmPassword,
        border: OutlineInputBorder(),
      ),
      validator: (value) {
        if (value != _passwordController.text) {
          return context.l10n.passwordMismatch;
        }
        return null;
      },
    );
  }

  Widget _verificationField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        TextFormField(
          key: const Key('verification-code-field'),
          controller: _verificationCodeController,
          keyboardType: TextInputType.number,
          maxLength: 6,
          decoration: InputDecoration(
            labelText: context.l10n.verificationCode,
            hintText: context.l10n.enterVerificationCode,
            counterText: '',
            border: OutlineInputBorder(),
          ),
          validator: (value) => RegExp(r'^\d{6}$').hasMatch(value?.trim() ?? '')
              ? null
              : context.l10n.enterSixDigitCode,
        ),
        const SizedBox(height: DrAiSpacing.xs),
        OutlinedButton.icon(
          key: const Key('registration-send-code-button'),
          onPressed: _registrationCodeRequesting
              ? null
              : _requestRegistrationCode,
          icon: _registrationCodeRequesting
              ? const SizedBox.square(
                  dimension: 14,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.sms_outlined, size: 18),
          label: Text(context.l10n.sendCode),
        ),
        if (_registrationCodeStatus != null) ...<Widget>[
          const SizedBox(height: DrAiSpacing.xs),
          Text(
            _registrationCodeStatus!,
            key: const Key('registration-code-status'),
            style: const TextStyle(color: DrAiColors.mutedInk, fontSize: 12),
          ),
        ],
      ],
    );
  }

  Future<void> _requestRegistrationCode() async {
    if (_phoneController.text.trim().length < 5) {
      setState(() {
        _registrationCodeStatus = context.l10n.enterPhoneFirst;
      });
      return;
    }
    setState(() {
      _registrationCodeRequesting = true;
      _registrationCodeStatus = null;
    });
    try {
      final result = await ref
          .read(repositoryProvider)
          .requestRegistrationCode(_fullPhoneNumber());
      if (!mounted) {
        return;
      }
      if (result.debugCode != null) {
        _verificationCodeController.text = result.debugCode!;
      }
      setState(() {
        _registrationCodeRequesting = false;
        _registrationCodeStatus = result.debugCode == null
            ? result.message
            : context.l10n.localDevelopmentCodeFilled(result.message);
      });
    } on ApiError catch (error) {
      if (mounted) {
        setState(() {
          _registrationCodeRequesting = false;
          _registrationCodeStatus = error.message;
        });
      }
    } on Exception {
      if (mounted) {
        setState(() {
          _registrationCodeRequesting = false;
          _registrationCodeStatus = context.l10n.unableToRequestCode;
        });
      }
    }
  }

  Widget _roleSelector() {
    return SegmentedButton<AppRole>(
      key: const Key('register-role-selector'),
      segments: <ButtonSegment<AppRole>>[
        ButtonSegment<AppRole>(
          value: AppRole.patient,
          icon: const Icon(Icons.person_outline),
          label: Text(context.l10n.patient),
        ),
        ButtonSegment<AppRole>(
          value: AppRole.doctor,
          icon: const Icon(Icons.medical_services_outlined),
          label: Text(context.l10n.doctor),
        ),
      ],
      selected: <AppRole>{_selectedRole},
      onSelectionChanged: (roles) => setState(() {
        _selectedRole = roles.first;
        _customHospital = _selectedRole == AppRole.doctor;
      }),
    );
  }

  Widget _nameFields(bool desktop) {
    final fields = <Widget>[
      _textField(
        controller: _firstNameController,
        label: context.l10n.firstName,
        keyName: 'signup-first-name-field',
        required: true,
      ),
      _textField(
        controller: _middleNameController,
        label: context.l10n.middleNameOptional,
        keyName: 'signup-middle-name-field',
      ),
      _textField(
        controller: _lastNameController,
        label: context.l10n.lastName,
        keyName: 'signup-last-name-field',
        required: true,
      ),
    ];
    if (!desktop) {
      return Column(
        children: fields
            .expand(
              (field) => <Widget>[
                field,
                const SizedBox(height: DrAiSpacing.md),
              ],
            )
            .take(fields.length * 2 - 1)
            .toList(),
      );
    }
    return Row(
      children: <Widget>[
        for (var index = 0; index < fields.length; index++) ...<Widget>[
          Expanded(child: fields[index]),
          if (index != fields.length - 1) const SizedBox(width: DrAiSpacing.sm),
        ],
      ],
    );
  }

  Widget _birthDateField() {
    return TextFormField(
      key: const Key('signup-birth-date-field'),
      controller: _birthDateController,
      keyboardType: TextInputType.datetime,
      decoration: InputDecoration(
        labelText: context.l10n.dateOfBirth,
        hintText: 'YYYY-MM-DD',
        border: const OutlineInputBorder(),
        suffixIcon: IconButton(
          tooltip: context.l10n.selectDate,
          onPressed: () => _showBirthDatePicker(_birthDateController),
          icon: const Icon(Icons.calendar_today_outlined),
        ),
      ),
      validator: (value) => _dateValidator(context, value),
    );
  }

  Widget _genderField() {
    return DropdownButtonFormField<String>(
      key: const Key('signup-gender-field'),
      initialValue: _gender,
      isExpanded: true,
      menuMaxHeight: _menuMaxHeight,
      borderRadius: _menuBorderRadius,
      dropdownColor: DrAiColors.white,
      icon: const Icon(Icons.keyboard_arrow_down_rounded),
      style: _menuTextStyle,
      decoration: InputDecoration(
        labelText: context.l10n.gender,
        border: OutlineInputBorder(),
      ),
      items: _optionItems(<String>['Unspecified', 'Female', 'Male', 'Other']),
      onChanged: (value) => setState(() => _gender = value ?? _gender),
    );
  }

  Widget _locationFields(bool desktop) {
    final fields = <Widget>[
      DropdownButtonFormField<String>(
        key: const Key('signup-country-field'),
        initialValue: _country,
        isExpanded: true,
        menuMaxHeight: _menuMaxHeight,
        borderRadius: _menuBorderRadius,
        dropdownColor: DrAiColors.white,
        icon: const Icon(Icons.keyboard_arrow_down_rounded),
        style: _menuTextStyle,
        decoration: InputDecoration(
          labelText: context.l10n.countryRegion,
          border: OutlineInputBorder(),
        ),
        items: locationCountries
            .map(
              (item) => DropdownMenuItem(
                value: item.name,
                child: Text(context.l10n.stableValue(item.name)),
              ),
            )
            .toList(),
        onChanged: (value) {
          if (value == null) {
            return;
          }
          final firstRegion = _regions(value).first;
          setState(() {
            _country = value;
            _province = firstRegion.name;
            _city = firstRegion.cities.first;
          });
        },
      ),
      DropdownButtonFormField<String>(
        key: const Key('signup-province-field'),
        initialValue: _province,
        isExpanded: true,
        menuMaxHeight: _menuMaxHeight,
        borderRadius: _menuBorderRadius,
        dropdownColor: DrAiColors.white,
        icon: const Icon(Icons.keyboard_arrow_down_rounded),
        style: _menuTextStyle,
        decoration: InputDecoration(
          labelText: context.l10n.province,
          border: OutlineInputBorder(),
        ),
        items: _regions(_country)
            .map(
              (item) => DropdownMenuItem(
                value: item.name,
                child: Text(context.l10n.stableValue(item.name)),
              ),
            )
            .toList(),
        onChanged: (value) {
          if (value == null) {
            return;
          }
          setState(() {
            _province = value;
            _city = _cities(value).first;
          });
        },
      ),
      DropdownButtonFormField<String>(
        key: const Key('signup-city-field'),
        initialValue: _city,
        isExpanded: true,
        menuMaxHeight: _menuMaxHeight,
        borderRadius: _menuBorderRadius,
        dropdownColor: DrAiColors.white,
        icon: const Icon(Icons.keyboard_arrow_down_rounded),
        style: _menuTextStyle,
        decoration: InputDecoration(
          labelText: context.l10n.city,
          border: OutlineInputBorder(),
        ),
        items: _cities(_province)
            .map(
              (item) => DropdownMenuItem(
                value: item,
                child: Text(context.l10n.stableValue(item)),
              ),
            )
            .toList(),
        onChanged: (value) => setState(() => _city = value ?? _city),
      ),
    ];
    if (!desktop) {
      return Column(
        children: fields
            .expand(
              (field) => <Widget>[
                field,
                const SizedBox(height: DrAiSpacing.md),
              ],
            )
            .take(fields.length * 2 - 1)
            .toList(),
      );
    }
    return Row(
      children: <Widget>[
        for (var index = 0; index < fields.length; index++) ...<Widget>[
          Expanded(child: fields[index]),
          if (index != fields.length - 1) const SizedBox(width: DrAiSpacing.sm),
        ],
      ],
    );
  }

  Widget _hospitalFields(bool desktop) {
    final selector = DropdownButtonFormField<String>(
      key: const Key('signup-hospital-field'),
      isExpanded: true,
      menuMaxHeight: _menuMaxHeight,
      borderRadius: _menuBorderRadius,
      dropdownColor: DrAiColors.white,
      icon: const Icon(Icons.keyboard_arrow_down_rounded),
      style: _menuTextStyle,
      decoration: InputDecoration(
        labelText: context.l10n.hospital,
        border: OutlineInputBorder(),
      ),
      hint: Text(context.l10n.hospitalEmpty),
      items: const <DropdownMenuItem<String>>[],
      onChanged: null,
    );
    final addHospital = DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: const Color(0xFFD4DCE8)),
        borderRadius: BorderRadius.circular(DrAiRadii.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              context.l10n.hospitalMissing,
              style: TextStyle(color: DrAiColors.inkSecondary),
            ),
            TextButton.icon(
              key: const Key('signup-add-hospital-button'),
              onPressed: () => setState(() => _customHospital = true),
              icon: const Icon(Icons.add),
              label: Text(context.l10n.addHospital),
            ),
          ],
        ),
      ),
    );
    final customField = _customHospital
        ? _textField(
            controller: _hospitalController,
            label: context.l10n.hospitalName,
            keyName: 'signup-custom-hospital-field',
            required: true,
          )
        : const SizedBox.shrink();
    if (!desktop) {
      return Column(
        children: <Widget>[
          selector,
          const SizedBox(height: DrAiSpacing.md),
          addHospital,
          const SizedBox(height: DrAiSpacing.md),
          customField,
        ],
      );
    }
    return Column(
      children: <Widget>[
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Expanded(child: selector),
            const SizedBox(width: DrAiSpacing.md),
            Expanded(child: addHospital),
          ],
        ),
        const SizedBox(height: DrAiSpacing.md),
        customField,
      ],
    );
  }

  Widget _termsRow() {
    return FormField<bool>(
      validator: (_) =>
          _termsAccepted ? null : context.l10n.acceptTermsValidation,
      builder: (field) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: <Widget>[
                Checkbox(
                  key: const Key('terms-checkbox'),
                  value: _termsAccepted,
                  onChanged: (value) {
                    setState(() => _termsAccepted = value ?? false);
                    field.didChange(_termsAccepted);
                  },
                ),
                Expanded(
                  child: Wrap(
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: <Widget>[
                      Text(context.l10n.termsConsentPrefix),
                      _inlineLink(context.l10n.termsOfService, '/terms'),
                      Text(context.l10n.termsConsentJoiner),
                      _inlineLink(
                        context.l10n.privacyPolicy,
                        '/privacy-policy',
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (field.hasError)
              Padding(
                padding: const EdgeInsets.only(left: DrAiSpacing.md),
                child: Text(
                  field.errorText!,
                  style: const TextStyle(
                    color: DrAiColors.danger,
                    fontSize: 12,
                  ),
                ),
              ),
          ],
        );
      },
    );
  }

  Widget _inlineLink(String label, String path) {
    return InkWell(
      onTap: () {
        ref.read(authControllerProvider.notifier).clearFeedback();
        context.go(path);
      },
      child: Text(
        label,
        style: const TextStyle(
          color: DrAiColors.brand,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  Widget _formSection({
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Row(
          children: <Widget>[
            CircleAvatar(
              radius: 18,
              backgroundColor: DrAiColors.brand,
              child: Icon(icon, color: DrAiColors.white, size: 18),
            ),
            const SizedBox(width: DrAiSpacing.sm),
            Expanded(
              child: Text(
                title,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: DrAiColors.brandDark,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: DrAiSpacing.md),
        ...children,
      ],
    );
  }

  Widget _responsivePair(bool desktop, Widget first, Widget second) {
    if (!desktop) {
      return Column(
        children: <Widget>[
          first,
          if (second is! SizedBox) ...<Widget>[
            const SizedBox(height: DrAiSpacing.md),
            second,
          ],
        ],
      );
    }
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Expanded(child: first),
        const SizedBox(width: DrAiSpacing.md),
        Expanded(child: second),
      ],
    );
  }

  Widget _textField({
    required TextEditingController controller,
    required String label,
    required String keyName,
    bool required = false,
    int minLines = 1,
    int maxLines = 1,
  }) {
    return TextFormField(
      key: Key(keyName),
      controller: controller,
      minLines: minLines,
      maxLines: maxLines,
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
      ),
      validator: required
          ? (value) {
              if ((value?.trim() ?? '').isEmpty) {
                return context.l10n.required;
              }
              return null;
            }
          : null,
    );
  }

  Widget _primaryButton({
    required Key key,
    required AsyncValue<AuthState> auth,
    required String text,
    required IconData icon,
  }) {
    return FilledButton.icon(
      key: key,
      onPressed: auth.isLoading ? null : _submit,
      icon: auth.isLoading
          ? const SizedBox.square(
              dimension: 18,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: DrAiColors.white,
              ),
            )
          : Icon(icon),
      label: Text(text),
    );
  }

  Widget _authModeButton() {
    return TextButton(
      key: const Key('auth-mode-toggle'),
      onPressed: _toggleMode,
      child: Text(
        _isRegistering
            ? context.l10n.alreadyHaveAccountLogIn
            : context.l10n.createAnAccount,
      ),
    );
  }

  List<Widget> _statusMessages(String? errorMessage, String? noticeMessage) {
    return <Widget>[
      if (noticeMessage != null) ...<Widget>[
        const SizedBox(height: DrAiSpacing.md),
        _StatusText(
          message: context.l10n.stableValue(noticeMessage),
          keyName: 'login-notice',
        ),
      ],
      if (errorMessage != null) ...<Widget>[
        const SizedBox(height: DrAiSpacing.md),
        _StatusText(
          message: context.l10n.stableValue(errorMessage),
          keyName: 'login-error',
          color: DrAiColors.danger,
        ),
      ],
    ];
  }

  List<DropdownMenuItem<String>> _optionItems(List<String> values) {
    return values
        .map(
          (value) => DropdownMenuItem<String>(
            value: value,
            child: Text(context.l10n.stableValue(value)),
          ),
        )
        .toList();
  }

  BoxDecoration _panelDecoration() {
    return BoxDecoration(
      color: DrAiColors.white,
      border: Border.all(color: DrAiColors.outline),
      borderRadius: BorderRadius.circular(DrAiRadii.lg),
      boxShadow: const <BoxShadow>[
        BoxShadow(
          color: Color(0x120A0076),
          blurRadius: 32,
          offset: Offset(0, 18),
        ),
      ],
    );
  }

  List<LocationRegion> _regions(String country) {
    return locationCountries.firstWhere((item) => item.name == country).regions;
  }

  List<String> _cities(String province) {
    return _regions(
      _country,
    ).firstWhere((item) => item.name == province).cities;
  }

  String _displayName() {
    return <String>[
      _firstNameController.text.trim(),
      _middleNameController.text.trim(),
      _lastNameController.text.trim(),
    ].where((item) => item.isNotEmpty).join(' ');
  }

  String _fullPhoneNumber() {
    return _phoneWithDialCode(_phoneController.text);
  }

  String _loginAccount() {
    final account = _accountController.text.trim();
    if (_isEmail(account)) {
      return account;
    }
    return _phoneWithDialCode(account);
  }

  String _phoneWithDialCode(String value) {
    final local = value.replaceAll(RegExp(r'[\s()-]'), '');
    if (local.startsWith('+')) {
      return local;
    }
    return '${_dialingCode.dialCode.replaceAll('-', '')}$local';
  }

  void _toggleMode() {
    ref.read(authControllerProvider.notifier).clearFeedback();
    context.go(_isRegistering ? '/login' : '/register');
  }

  void _ensureFeedbackTimer(String? message) {
    if (_scheduledFeedback == message) {
      return;
    }
    _feedbackTimer?.cancel();
    _scheduledFeedback = message;
    if (message == null) {
      return;
    }
    _feedbackTimer = Timer(const Duration(seconds: 2), () {
      if (!mounted) {
        return;
      }
      ref.read(authControllerProvider.notifier).clearFeedback();
    });
  }

  Future<void> _showForgotPassword() {
    return showDialog<void>(
      context: context,
      builder: (context) => const _ForgotPasswordDialog(),
    );
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
                      child: Text(context.l10n.cancel),
                    ),
                    const Spacer(),
                    Text(
                      context.l10n.dateOfBirth,
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
                      child: Text(context.l10n.done),
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

class _ForgotPasswordDialog extends ConsumerStatefulWidget {
  const _ForgotPasswordDialog();

  @override
  ConsumerState<_ForgotPasswordDialog> createState() =>
      _ForgotPasswordDialogState();
}

class _ForgotPasswordDialogState extends ConsumerState<_ForgotPasswordDialog> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _codeController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  DialingCodeOption _dialingCode = dialingCodeOptions.firstWhere(
    (item) => item.isoCode == 'CN',
  );
  bool _requesting = false;
  bool _resetting = false;
  bool _complete = false;
  bool _obscure = true;
  String? _statusMessage;
  String? _errorMessage;

  @override
  void dispose() {
    _phoneController.dispose();
    _codeController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(
        _complete ? context.l10n.passwordUpdated : context.l10n.resetPassword,
      ),
      content: SizedBox(
        width: 460,
        child: _complete
            ? Text(context.l10n.passwordChangedSignIn)
            : Form(
                key: _formKey,
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      Text(
                        context.l10n.verifyPhoneReset,
                        style: TextStyle(color: DrAiColors.inkSecondary),
                      ),
                      const SizedBox(height: DrAiSpacing.md),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          SizedBox(
                            width: 126,
                            child: DropdownButtonFormField<DialingCodeOption>(
                              key: const Key('forgot-password-country-code'),
                              initialValue: _dialingCode,
                              isExpanded: true,
                              decoration: InputDecoration(
                                labelText: context.l10n.code,
                                border: const OutlineInputBorder(),
                              ),
                              selectedItemBuilder: (context) =>
                                  dialingCodeOptions
                                      .map((item) => Text(item.dialCode))
                                      .toList(),
                              items: dialingCodeOptions
                                  .map(
                                    (item) => DropdownMenuItem(
                                      value: item,
                                      child: Text(
                                        '${item.isoCode} ${item.dialCode}',
                                      ),
                                    ),
                                  )
                                  .toList(),
                              onChanged: (value) {
                                if (value != null) {
                                  setState(() => _dialingCode = value);
                                }
                              },
                            ),
                          ),
                          const SizedBox(width: DrAiSpacing.sm),
                          Expanded(
                            child: TextFormField(
                              key: const Key('forgot-password-phone-field'),
                              controller: _phoneController,
                              keyboardType: TextInputType.phone,
                              decoration: InputDecoration(
                                labelText: context.l10n.phoneNumber,
                                border: const OutlineInputBorder(),
                              ),
                              validator: (value) =>
                                  (value?.trim().length ?? 0) < 5
                                  ? context.l10n.enterYourPhone
                                  : null,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: DrAiSpacing.sm),
                      OutlinedButton.icon(
                        key: const Key('forgot-password-send-code'),
                        onPressed: _requesting ? null : _requestCode,
                        icon: _requesting
                            ? const SizedBox.square(
                                dimension: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(Icons.sms_outlined),
                        label: Text(context.l10n.sendVerificationCode),
                      ),
                      const SizedBox(height: DrAiSpacing.md),
                      TextFormField(
                        key: const Key('forgot-password-code-field'),
                        controller: _codeController,
                        keyboardType: TextInputType.number,
                        maxLength: 6,
                        decoration: InputDecoration(
                          labelText: context.l10n.sixDigitVerificationCode,
                          counterText: '',
                          border: const OutlineInputBorder(),
                        ),
                        validator: (value) =>
                            RegExp(r'^\d{6}$').hasMatch(value?.trim() ?? '')
                            ? null
                            : context.l10n.enterSixDigitCode,
                      ),
                      const SizedBox(height: DrAiSpacing.sm),
                      _passwordField(
                        controller: _passwordController,
                        label: context.l10n.newPassword,
                        keyName: 'forgot-password-new-field',
                      ),
                      const SizedBox(height: DrAiSpacing.sm),
                      _passwordField(
                        controller: _confirmController,
                        label: context.l10n.confirmNewPassword,
                        keyName: 'forgot-password-confirm-field',
                        confirmation: true,
                      ),
                      if (_statusMessage != null) ...<Widget>[
                        const SizedBox(height: DrAiSpacing.sm),
                        Text(
                          context.l10n.stableValue(_statusMessage!),
                          key: const Key('forgot-password-status'),
                          style: const TextStyle(color: DrAiColors.brand),
                        ),
                      ],
                      if (_errorMessage != null) ...<Widget>[
                        const SizedBox(height: DrAiSpacing.sm),
                        Text(
                          context.l10n.stableValue(_errorMessage!),
                          key: const Key('forgot-password-error'),
                          style: const TextStyle(color: DrAiColors.danger),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
      ),
      actions: <Widget>[
        if (_complete)
          FilledButton(
            key: const Key('forgot-password-done'),
            onPressed: () => Navigator.of(context).pop(),
            child: Text(context.l10n.backToSignIn),
          )
        else ...<Widget>[
          TextButton(
            onPressed: _resetting ? null : () => Navigator.of(context).pop(),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            key: const Key('forgot-password-reset'),
            onPressed: _resetting ? null : _resetPassword,
            child: _resetting
                ? const SizedBox.square(
                    dimension: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: DrAiColors.white,
                    ),
                  )
                : Text(context.l10n.resetPassword),
          ),
        ],
      ],
    );
  }

  TextFormField _passwordField({
    required TextEditingController controller,
    required String label,
    required String keyName,
    bool confirmation = false,
  }) {
    return TextFormField(
      key: Key(keyName),
      controller: controller,
      obscureText: _obscure,
      autofillHints: const <String>[AutofillHints.newPassword],
      decoration: InputDecoration(
        labelText: label,
        helperText: confirmation ? null : context.l10n.passwordLength,
        border: const OutlineInputBorder(),
        suffixIcon: IconButton(
          tooltip: _obscure
              ? context.l10n.showPasswords
              : context.l10n.hidePasswords,
          onPressed: () => setState(() => _obscure = !_obscure),
          icon: Icon(
            _obscure
                ? Icons.visibility_outlined
                : Icons.visibility_off_outlined,
          ),
        ),
      ),
      validator: (value) {
        if (confirmation) {
          return value != _passwordController.text
              ? context.l10n.passwordMismatch
              : null;
        }
        final password = value ?? '';
        return password.length < 8 || password.length > 20
            ? context.l10n.passwordLength
            : null;
      },
    );
  }

  String _phoneNumber() {
    final local = _phoneController.text.replaceAll(RegExp(r'[\s()-]'), '');
    if (local.startsWith('+')) {
      return local;
    }
    return '${_dialingCode.dialCode.replaceAll('-', '')}$local';
  }

  Future<void> _requestCode() async {
    if ((_phoneController.text.trim()).length < 5) {
      setState(() => _errorMessage = context.l10n.enterPhoneFirst);
      return;
    }
    setState(() {
      _requesting = true;
      _errorMessage = null;
      _statusMessage = null;
    });
    try {
      final result = await ref
          .read(repositoryProvider)
          .requestPasswordReset(_phoneNumber());
      if (!mounted) {
        return;
      }
      if (result.debugCode != null) {
        _codeController.text = result.debugCode!;
      }
      setState(() {
        _requesting = false;
        _statusMessage = result.debugCode == null
            ? result.message
            : context.l10n.localDevelopmentCodeFilled(result.message);
      });
    } on ApiError catch (error) {
      if (mounted) {
        setState(() {
          _requesting = false;
          _errorMessage = error.message;
        });
      }
    } on Exception {
      if (mounted) {
        setState(() {
          _requesting = false;
          _errorMessage = context.l10n.unableToRequestCode;
        });
      }
    }
  }

  Future<void> _resetPassword() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    setState(() {
      _resetting = true;
      _errorMessage = null;
    });
    try {
      await ref
          .read(repositoryProvider)
          .resetPassword(
            phoneNumber: _phoneNumber(),
            verificationCode: _codeController.text,
            newPassword: _passwordController.text,
          );
      if (mounted) {
        setState(() {
          _resetting = false;
          _complete = true;
        });
      }
    } on ApiError catch (error) {
      if (mounted) {
        setState(() {
          _resetting = false;
          _errorMessage = error.message;
        });
      }
    } on Exception {
      if (mounted) {
        setState(() {
          _resetting = false;
          _errorMessage = context.l10n.resetPasswordFailed;
        });
      }
    }
  }
}

class _RegistrationStepRail extends StatelessWidget {
  const _RegistrationStepRail();

  @override
  Widget build(BuildContext context) {
    final steps = <({IconData icon, String title, String subtitle})>[
      (
        icon: Icons.person,
        title: context.l10n.stepAccount,
        subtitle: context.l10n.createAccount,
      ),
      (
        icon: Icons.badge_outlined,
        title: context.l10n.stepProfile,
        subtitle: context.l10n.personalInformation,
      ),
      (
        icon: Icons.local_hospital_outlined,
        title: context.l10n.stepLocation,
        subtitle: context.l10n.careHospitalDetails,
      ),
      (
        icon: Icons.check_circle_outline,
        title: context.l10n.stepComplete,
        subtitle: context.l10n.finishSetup,
      ),
    ];
    return ColoredBox(
      color: const Color(0xFFF8FBFF),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(28, 40, 28, 28),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            for (var index = 0; index < steps.length; index++) ...<Widget>[
              _RailStep(step: steps[index], active: index == 0),
              if (index != steps.length - 1)
                Container(
                  width: 1,
                  height: 38,
                  margin: const EdgeInsets.only(left: 17),
                  color: const Color(0xFFD8E1EF),
                ),
            ],
            const Spacer(),
            DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0xFFEAF4FF),
                borderRadius: BorderRadius.circular(DrAiRadii.md),
              ),
              child: Padding(
                padding: const EdgeInsets.all(DrAiSpacing.md),
                child: Row(
                  children: <Widget>[
                    const Icon(Icons.shield_outlined, color: DrAiColors.brand),
                    const SizedBox(width: DrAiSpacing.sm),
                    Expanded(
                      child: Text(
                        '${context.l10n.secureInformationTitle}\n${context.l10n.secureInformationBody}',
                        style: const TextStyle(
                          color: DrAiColors.inkSecondary,
                          height: 1.55,
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
    );
  }
}

class _RailStep extends StatelessWidget {
  const _RailStep({required this.step, required this.active});

  final ({IconData icon, String title, String subtitle}) step;
  final bool active;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        CircleAvatar(
          radius: 18,
          backgroundColor: active ? DrAiColors.brand : DrAiColors.white,
          foregroundColor: active ? DrAiColors.white : DrAiColors.mutedInk,
          child: Icon(step.icon, size: 18),
        ),
        const SizedBox(width: DrAiSpacing.sm),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                step.title,
                style: TextStyle(
                  color: active ? DrAiColors.brand : DrAiColors.inkSecondary,
                  fontWeight: FontWeight.w800,
                ),
              ),
              Text(
                step.subtitle,
                style: const TextStyle(
                  color: DrAiColors.mutedInk,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _AuthWordmark extends StatelessWidget {
  const _AuthWordmark({this.size = 28});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Text(
      'Dr. AI',
      style: TextStyle(
        color: DrAiColors.brand,
        fontSize: size,
        fontWeight: FontWeight.w900,
        letterSpacing: 0,
      ),
    );
  }
}

class _StatusText extends StatelessWidget {
  const _StatusText({
    required this.message,
    required this.keyName,
    this.color = DrAiColors.mutedInk,
  });

  final String message;
  final String keyName;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Text(
        message,
        key: Key(keyName),
        textAlign: TextAlign.center,
        style: TextStyle(color: color),
      ),
    );
  }
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

String? _dateValidator(BuildContext context, String? value) {
  final text = value?.trim() ?? '';
  if (text.isEmpty) {
    return null;
  }
  if (_parseDate(text) == null) {
    return context.l10n.useDateFormat;
  }
  return null;
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

bool _isEmail(String value) {
  return RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value);
}

bool _isPhone(String value) {
  final normalized = value.replaceAll(RegExp(r'[\s()-]'), '');
  return RegExp(r'^\+?\d{6,22}$').hasMatch(normalized);
}
