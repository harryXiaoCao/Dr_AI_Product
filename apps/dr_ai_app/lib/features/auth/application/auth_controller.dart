import 'package:dio/dio.dart';
import 'package:dr_ai_app/core/api/api_error.dart';
import 'package:dr_ai_app/core/config/app_config.dart';
import 'package:dr_ai_app/features/auth/data/dr_ai_repository.dart';
import 'package:dr_ai_app/features/auth/domain/auth_models.dart';
import 'package:dr_ai_app/features/dashboard/domain/dashboard_data.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final repositoryProvider = Provider<DrAiRepository>((ref) {
  return DioDrAiRepository(
    client: Dio(
      BaseOptions(
        baseUrl: AppConfig.apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 15),
        headers: const <String, String>{'Accept': 'application/json'},
      ),
    ),
    secureStorage: const FlutterSecureStorage(),
  );
});

final authControllerProvider = AsyncNotifierProvider<AuthController, AuthState>(
  AuthController.new,
);

class AuthController extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    final session = await ref.read(repositoryProvider).restore();
    return session == null
        ? const AuthState.signedOut()
        : AuthState.signedIn(session.user);
  }

  Future<void> login(String email, String password) async {
    state = const AsyncLoading();
    try {
      final session = await ref.read(repositoryProvider).login(email, password);
      state = AsyncData(AuthState.signedIn(session.user));
    } on ApiError catch (error) {
      state = AsyncData(
        AuthState.signedOut(errorMessage: _loginErrorMessage(error)),
      );
    } on Exception {
      state = const AsyncData(
        AuthState.signedOut(
          errorMessage:
              'Unable to reach Dr. AI. Check your connection and try again.',
        ),
      );
    }
  }

  Future<void> logout() async {
    state = const AsyncLoading();
    try {
      await ref.read(repositoryProvider).logout();
      state = const AsyncData(
        AuthState.signedOut(noticeMessage: 'You have signed out.'),
      );
    } on Exception {
      state = const AsyncData(
        AuthState.signedOut(
          noticeMessage:
              'You have signed out locally. The server could not be reached.',
        ),
      );
    }
  }
}

String _loginErrorMessage(ApiError error) {
  if (error.code == 'unauthenticated') {
    return 'The email or password is incorrect.';
  }
  if (error.code == 'service_unavailable') {
    return 'Unable to reach Dr. AI. Check your connection and try again.';
  }
  return error.message;
}

final dashboardProvider = FutureProvider.autoDispose<DashboardData>((
  ref,
) async {
  final authState = ref.watch(authControllerProvider).value;
  final user = authState?.user;
  if (user == null) {
    throw const ApiError(
      code: 'unauthenticated',
      message: 'Your session has ended. Please sign in again.',
      statusCode: 401,
    );
  }
  return ref.read(repositoryProvider).loadDashboard(user.role);
});
