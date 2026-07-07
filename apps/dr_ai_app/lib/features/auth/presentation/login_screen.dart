import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/shared/widgets/brand_mark.dart';
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
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    await ref
        .read(authControllerProvider.notifier)
        .login(_emailController.text, _passwordController.text);
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final errorMessage = auth.value?.errorMessage;
    final noticeMessage = auth.value?.noticeMessage;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(DrAiSpacing.lg),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    const DrAiBrandMark(size: 76),
                    const SizedBox(height: DrAiSpacing.md),
                    Text(
                      'Welcome to Dr. AI',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    const Text(
                      'Sign in to your invited beta account.',
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: DrAiSpacing.lg),
                    TextFormField(
                      key: const Key('email-field'),
                      controller: _emailController,
                      autofillHints: const <String>[AutofillHints.email],
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) {
                        final email = value?.trim() ?? '';
                        if (email.isEmpty || !email.contains('@')) {
                          return 'Enter a valid email address.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: DrAiSpacing.md),
                    TextFormField(
                      key: const Key('password-field'),
                      controller: _passwordController,
                      autofillHints: const <String>[AutofillHints.password],
                      obscureText: _obscurePassword,
                      decoration: InputDecoration(
                        labelText: 'Password',
                        border: const OutlineInputBorder(),
                        suffixIcon: IconButton(
                          tooltip: _obscurePassword
                              ? 'Show password'
                              : 'Hide password',
                          onPressed: () => setState(
                            () => _obscurePassword = !_obscurePassword,
                          ),
                          icon: Icon(
                            _obscurePassword
                                ? Icons.visibility_outlined
                                : Icons.visibility_off_outlined,
                          ),
                        ),
                      ),
                      validator: (value) =>
                          (value ?? '').isEmpty ? 'Enter your password.' : null,
                      onFieldSubmitted: (_) => _submit(),
                    ),
                    if (noticeMessage != null) ...<Widget>[
                      const SizedBox(height: DrAiSpacing.md),
                      Semantics(
                        liveRegion: true,
                        child: Text(
                          noticeMessage,
                          key: const Key('login-notice'),
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: DrAiColors.mutedInk),
                        ),
                      ),
                    ],
                    if (errorMessage != null) ...<Widget>[
                      const SizedBox(height: DrAiSpacing.md),
                      Semantics(
                        liveRegion: true,
                        child: Text(
                          errorMessage,
                          key: const Key('login-error'),
                          style: const TextStyle(color: DrAiColors.danger),
                        ),
                      ),
                    ],
                    const SizedBox(height: DrAiSpacing.lg),
                    FilledButton(
                      key: const Key('login-button'),
                      onPressed: auth.isLoading ? null : _submit,
                      child: auth.isLoading
                          ? const SizedBox.square(
                              dimension: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: DrAiColors.white,
                              ),
                            )
                          : const Text('Sign in'),
                    ),
                    const SizedBox(height: DrAiSpacing.sm),
                    TextButton(
                      onPressed: null,
                      child: const Text('Password reset unavailable in Week 1'),
                    ),
                    TextButton.icon(
                      key: const Key('login-beta-support-link'),
                      onPressed: () => context.go('/beta-support'),
                      icon: const Icon(Icons.privacy_tip_outlined),
                      label: const Text('Beta privacy and support'),
                    ),
                    const SizedBox(height: DrAiSpacing.lg),
                    const Text(
                      'Synthetic demonstration data only. '
                      'Do not enter real patient data.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: DrAiColors.mutedInk),
                    ),
                    const SizedBox(height: DrAiSpacing.xs),
                    const Text(
                      'Dr. AI is a non-clinical invited beta.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: DrAiColors.mutedInk),
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
