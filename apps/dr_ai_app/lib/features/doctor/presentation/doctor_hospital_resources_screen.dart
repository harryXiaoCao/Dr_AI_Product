import 'package:dr_ai_app/app/routing/app_role.dart';
import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/features/auth/application/auth_controller.dart';
import 'package:dr_ai_app/shared/widgets/responsive_app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final doctorHospitalResourcesProvider = FutureProvider<Map<String, dynamic>>(
  (ref) => ref.watch(repositoryProvider).loadDoctorHospitalResources(),
);

class DoctorHospitalResourcesScreen extends ConsumerWidget {
  const DoctorHospitalResourcesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final zh = Localizations.localeOf(context).languageCode == 'zh';
    final data = ref.watch(doctorHospitalResourcesProvider);
    return ResponsiveAppShell(
      role: AppRole.doctor,
      child: ColoredBox(
        color: DrAiColors.pageBackground,
        child: ListView(
          padding: const EdgeInsets.all(DrAiSpacing.md),
          children: <Widget>[
            Text(
              zh ? '科室资源可用情况' : 'Department availability',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              zh
                  ? '仅显示您已获授权科室的运营资源状态。实际安排请与科室确认。'
                  : 'Operational availability for your assigned departments. Confirm scheduling with the department.',
            ),
            const SizedBox(height: 16),
            data.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stack) => Card(
                child: Padding(
                  padding: const EdgeInsets.all(DrAiSpacing.md),
                  child: Column(
                    children: <Widget>[
                      Text(zh ? '无法加载资源。' : 'Unable to load resources.'),
                      TextButton(
                        onPressed: () =>
                            ref.invalidate(doctorHospitalResourcesProvider),
                        child: Text(zh ? '重试' : 'Retry'),
                      ),
                    ],
                  ),
                ),
              ),
              data: (value) {
                final resources = (value['resources'] as List?) ?? const [];
                if (resources.isEmpty) {
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(DrAiSpacing.md),
                      child: Text(
                        zh
                            ? '尚无已授权科室的资源记录。'
                            : 'No resources are recorded for your assigned departments.',
                      ),
                    ),
                  );
                }
                return Column(
                  children: <Widget>[
                    for (final raw in resources)
                      Card(
                        child: ListTile(
                          title: Text((raw as Map)['name'].toString()),
                          subtitle: Text(
                            '${raw['clinic_name']} · ${switch (raw['status']) {
                              'available' => zh ? '可用' : 'Available',
                              'limited' => zh ? '受限' : 'Limited',
                              'unavailable' => zh ? '不可用' : 'Unavailable',
                              _ => raw['status'],
                            }}',
                          ),
                          trailing: Text(
                            '${raw['capacity_current'] ?? '—'} / ${raw['capacity_total'] ?? '—'}',
                          ),
                        ),
                      ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
