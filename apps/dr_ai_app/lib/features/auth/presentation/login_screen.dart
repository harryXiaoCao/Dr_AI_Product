import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/features/auth/data/dr_ai_repository.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/auth/presentation/signup_reference_data.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

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
  AppRole _selectedRole = AppRole.patient;
  String _gender = 'Unspecified';
  DialingCodeOption _dialingCode = dialingCodeOptions.firstWhere(
    (item) => item.isoCode == 'CN',
  );
  String _country = 'China';
  String _province = 'Guangdong';
  String _city = 'Shenzhen';

  @override
  void dispose() {
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
              'Welcome to Dr. AI',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: DrAiColors.ink,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: DrAiSpacing.xs),
            const Text(
              'Sign in with the phone number or email on your account.',
              textAlign: TextAlign.center,
              style: TextStyle(color: DrAiColors.mutedInk),
            ),
            const SizedBox(height: DrAiSpacing.lg),
            _loginAccountField(),
            const SizedBox(height: DrAiSpacing.md),
            _passwordField(),
            ..._statusMessages(errorMessage, noticeMessage),
            const SizedBox(height: DrAiSpacing.lg),
            _primaryButton(
              key: const Key('login-button'),
              auth: auth,
              text: 'Sign in',
              icon: Icons.arrow_forward,
            ),
            const SizedBox(height: DrAiSpacing.sm),
            _authModeButton(),
            TextButton.icon(
              key: const Key('login-privacy-support-link'),
              onPressed: () => context.go('/privacy'),
              icon: const Icon(Icons.privacy_tip_outlined),
              label: const Text('Privacy, consent, and support'),
            ),
            const SizedBox(height: DrAiSpacing.sm),
            const Text(
              'Staging environment: do not enter real patient data.',
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
                const Text(
                  'Already have an account?',
                  style: TextStyle(color: DrAiColors.inkSecondary),
                ),
                TextButton(onPressed: _toggleMode, child: const Text('Log in')),
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
                    isDoctor ? 'Doctor Registration' : 'Create your account',
                    textAlign: desktop ? TextAlign.start : TextAlign.center,
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                      color: DrAiColors.brandDark,
                    ),
                  ),
                  const SizedBox(height: DrAiSpacing.xs),
                  Text(
                    isDoctor
                        ? 'Create your account to join Dr. AI'
                        : 'Set up your account and continue to medical intake.',
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
          title: 'Account Information',
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
          title: 'Personal Information',
          icon: Icons.badge_outlined,
          children: <Widget>[
            _nameFields(desktop),
            const SizedBox(height: DrAiSpacing.md),
            _responsivePair(desktop, _birthDateField(), _genderField()),
          ],
        ),
        const SizedBox(height: DrAiSpacing.lg),
        _formSection(
          title: isDoctor ? 'Hospital Information' : 'Home Address',
          icon: isDoctor ? Icons.local_hospital_outlined : Icons.home_outlined,
          children: <Widget>[
            _locationFields(desktop),
            if (!isDoctor) ...<Widget>[
              const SizedBox(height: DrAiSpacing.md),
              _textField(
                controller: _homeAddressController,
                label: 'Specific home address',
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
              text: 'Next',
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
            decoration: const InputDecoration(
              labelText: 'Code',
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
                    child: Text(item.label, overflow: TextOverflow.ellipsis),
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
            decoration: const InputDecoration(
              labelText: 'Email or phone number',
              border: OutlineInputBorder(),
            ),
            validator: (value) {
              final account = value?.trim() ?? '';
              if (!_isEmail(account) &&
                  !_isPhone(_phoneWithDialCode(account))) {
                return 'Enter a valid email address or phone number.';
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
            decoration: const InputDecoration(
              labelText: 'Code',
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
                    child: Text(item.label, overflow: TextOverflow.ellipsis),
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
            decoration: const InputDecoration(
              labelText: 'Phone number',
              hintText: 'Enter phone number',
              border: OutlineInputBorder(),
            ),
            validator: (value) {
              final phone = value?.trim() ?? '';
              if (required && phone.isEmpty) {
                return 'Phone number is required.';
              }
              if (phone.isNotEmpty && !_isPhone(_fullPhoneNumber())) {
                return 'Enter a valid phone number.';
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
      decoration: const InputDecoration(
        labelText: 'Email (optional)',
        border: OutlineInputBorder(),
      ),
      validator: (value) {
        final email = value?.trim() ?? '';
        if (email.isNotEmpty && !_isEmail(email)) {
          return 'Enter a valid email address.';
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
        labelText: 'Password',
        helperText: _isRegistering
            ? '8-20 characters. Letters, numbers, and symbols are okay.'
            : null,
        helperMaxLines: 2,
        helperStyle: const TextStyle(
          color: DrAiColors.mutedInk,
          fontSize: 11,
          height: 1.25,
        ),
        border: const OutlineInputBorder(),
        suffixIcon: IconButton(
          tooltip: _obscurePassword ? 'Show password' : 'Hide password',
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
          return 'Enter your password.';
        }
        if (_isRegistering && (password.length < 8 || password.length > 20)) {
          return 'Use 8-20 characters.';
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
      decoration: const InputDecoration(
        labelText: 'Confirm password',
        border: OutlineInputBorder(),
      ),
      validator: (value) {
        if (value != _passwordController.text) {
          return 'Passwords do not match.';
        }
        return null;
      },
    );
  }

  Widget _verificationField() {
    return TextFormField(
      key: const Key('verification-code-field'),
      controller: _verificationCodeController,
      keyboardType: TextInputType.number,
      decoration: const InputDecoration(
        labelText: 'Verification code',
        hintText: 'Enter code',
        suffixIcon: Padding(
          padding: EdgeInsets.only(right: DrAiSpacing.sm),
          child: Center(
            widthFactor: 1,
            child: Text(
              'Send code',
              style: TextStyle(
                color: DrAiColors.brand,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ),
        border: OutlineInputBorder(),
      ),
      validator: (value) {
        if ((value?.trim() ?? '') != '123456') {
          return 'Use verification code 123456 for now.';
        }
        return null;
      },
    );
  }

  Widget _roleSelector() {
    return SegmentedButton<AppRole>(
      key: const Key('register-role-selector'),
      segments: const <ButtonSegment<AppRole>>[
        ButtonSegment<AppRole>(
          value: AppRole.patient,
          icon: Icon(Icons.person_outline),
          label: Text('Patient'),
        ),
        ButtonSegment<AppRole>(
          value: AppRole.doctor,
          icon: Icon(Icons.medical_services_outlined),
          label: Text('Doctor'),
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
        label: 'First name',
        keyName: 'signup-first-name-field',
        required: true,
      ),
      _textField(
        controller: _middleNameController,
        label: 'Middle name (optional)',
        keyName: 'signup-middle-name-field',
      ),
      _textField(
        controller: _lastNameController,
        label: 'Last name',
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
        labelText: 'Date of birth',
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
      decoration: const InputDecoration(
        labelText: 'Gender',
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
        decoration: const InputDecoration(
          labelText: 'Country/Region',
          border: OutlineInputBorder(),
        ),
        items: locationCountries
            .map(
              (item) =>
                  DropdownMenuItem(value: item.name, child: Text(item.name)),
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
        decoration: const InputDecoration(
          labelText: 'Province',
          border: OutlineInputBorder(),
        ),
        items: _regions(_country)
            .map(
              (item) =>
                  DropdownMenuItem(value: item.name, child: Text(item.name)),
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
        decoration: const InputDecoration(
          labelText: 'City',
          border: OutlineInputBorder(),
        ),
        items: _cities(_province)
            .map((item) => DropdownMenuItem(value: item, child: Text(item)))
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
      decoration: const InputDecoration(
        labelText: 'Hospital',
        border: OutlineInputBorder(),
      ),
      hint: const Text('No hospitals listed yet'),
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
            const Text(
              'Can’t find your hospital?',
              style: TextStyle(color: DrAiColors.inkSecondary),
            ),
            TextButton.icon(
              key: const Key('signup-add-hospital-button'),
              onPressed: () => setState(() => _customHospital = true),
              icon: const Icon(Icons.add),
              label: const Text('Add my hospital'),
            ),
          ],
        ),
      ),
    );
    final customField = _customHospital
        ? _textField(
            controller: _hospitalController,
            label: 'Hospital name',
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
      validator: (_) => _termsAccepted ? null : 'Accept the terms and policy.',
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
                      const Text('I have read and agree to the '),
                      _inlineLink('Terms of Service', '/terms'),
                      const Text(' and '),
                      _inlineLink('Privacy Policy', '/privacy-policy'),
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
      onTap: () => context.go(path),
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
              if ((value?.trim() ?? '').length < 2) {
                return 'Required.';
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
            ? 'Already have an account? Log in'
            : 'Create an account',
      ),
    );
  }

  List<Widget> _statusMessages(String? errorMessage, String? noticeMessage) {
    return <Widget>[
      if (noticeMessage != null) ...<Widget>[
        const SizedBox(height: DrAiSpacing.md),
        _StatusText(message: noticeMessage, keyName: 'login-notice'),
      ],
      if (errorMessage != null) ...<Widget>[
        const SizedBox(height: DrAiSpacing.md),
        _StatusText(
          message: errorMessage,
          keyName: 'login-error',
          color: DrAiColors.danger,
        ),
      ],
    ];
  }

  List<DropdownMenuItem<String>> _optionItems(List<String> values) {
    return values
        .map(
          (value) => DropdownMenuItem<String>(value: value, child: Text(value)),
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
    setState(() {
      _isRegistering = !_isRegistering;
      _termsAccepted = false;
      _formKey.currentState?.reset();
      _verificationCodeController.clear();
    });
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
                      'Date of birth',
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

class _RegistrationStepRail extends StatelessWidget {
  const _RegistrationStepRail();

  @override
  Widget build(BuildContext context) {
    const steps = <({IconData icon, String title, String subtitle})>[
      (
        icon: Icons.person,
        title: '1  Account',
        subtitle: 'Create your account',
      ),
      (
        icon: Icons.badge_outlined,
        title: '2  Profile',
        subtitle: 'Personal information',
      ),
      (
        icon: Icons.local_hospital_outlined,
        title: '3  Location',
        subtitle: 'Care and hospital details',
      ),
      (
        icon: Icons.check_circle_outline,
        title: '4  Complete',
        subtitle: 'Finish setup',
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
              child: const Padding(
                padding: EdgeInsets.all(DrAiSpacing.md),
                child: Row(
                  children: <Widget>[
                    Icon(Icons.shield_outlined, color: DrAiColors.brand),
                    SizedBox(width: DrAiSpacing.sm),
                    Expanded(
                      child: Text(
                        'Your information is secure\nWe protect your data and comply with healthcare privacy regulations.',
                        style: TextStyle(
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
