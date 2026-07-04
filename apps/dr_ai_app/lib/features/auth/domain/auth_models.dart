import 'package:dr_ai_app/app/routing/app_role.dart';

class SessionUser {
  const SessionUser({
    required this.id,
    required this.email,
    required this.role,
    required this.displayName,
  });

  factory SessionUser.fromJson(Map<String, dynamic> json) {
    return SessionUser(
      id: json['id'] as String,
      email: json['email'] as String,
      role: AppRole.fromWire(json['role'] as String),
      displayName: json['display_name'] as String,
    );
  }

  final String id;
  final String email;
  final AppRole role;
  final String displayName;
}

class AuthSession {
  const AuthSession({
    required this.accessToken,
    required this.refreshToken,
    required this.user,
  });

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    return AuthSession(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      user: SessionUser.fromJson(json['user'] as Map<String, dynamic>),
    );
  }

  final String accessToken;
  final String refreshToken;
  final SessionUser user;
}

enum AuthStatus { signedOut, signedIn }

class AuthState {
  const AuthState._({required this.status, this.user, this.errorMessage});

  const AuthState.signedOut({String? errorMessage})
    : this._(status: AuthStatus.signedOut, errorMessage: errorMessage);

  const AuthState.signedIn(SessionUser user)
    : this._(status: AuthStatus.signedIn, user: user);

  final AuthStatus status;
  final SessionUser? user;
  final String? errorMessage;
}
