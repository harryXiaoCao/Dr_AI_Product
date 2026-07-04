import 'package:dr_ai_app/app/routing/app_role.dart';

class DashboardData {
  const DashboardData({required this.role, required this.data});

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    return DashboardData(
      role: AppRole.fromWire(json['role'] as String),
      data: json['data'] as Map<String, dynamic>,
    );
  }

  final AppRole role;
  final Map<String, dynamic> data;
}
