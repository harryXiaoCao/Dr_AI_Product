import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/shared/widgets/foundation_notice.dart';
import 'package:dr_ai_app/shared/widgets/section_card.dart';
import 'package:flutter/material.dart';

class DoctorDashboardScreen extends StatelessWidget {
  const DoctorDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dr. AI - Doctor'),
        actions: const <Widget>[
          Padding(
            padding: EdgeInsets.symmetric(horizontal: DrAiSpacing.md),
            child: Center(child: Text('Synthetic preview')),
          ),
        ],
      ),
      body: Column(
        children: <Widget>[
          if (MediaQuery.sizeOf(context).width >= DrAiBreakpoints.desktop)
            NavigationBar(
              selectedIndex: 0,
              destinations: const <NavigationDestination>[
                NavigationDestination(
                  icon: Icon(Icons.dashboard_outlined),
                  selectedIcon: Icon(Icons.dashboard),
                  label: 'Dashboard',
                ),
                NavigationDestination(
                  icon: Icon(Icons.science_outlined),
                  label: 'AI Diagnostic',
                ),
                NavigationDestination(
                  icon: Icon(Icons.monitor_heart_outlined),
                  label: 'AI Recovery Plan',
                ),
                NavigationDestination(
                  icon: Icon(Icons.medical_services_outlined),
                  label: 'Medical Resources',
                ),
                NavigationDestination(
                  icon: Icon(Icons.people_outline),
                  label: 'Patient Management',
                ),
              ],
            ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(DrAiSpacing.lg),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1120),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      Text(
                        'Doctor dashboard foundation',
                        style: Theme.of(context).textTheme.headlineMedium,
                      ),
                      const SizedBox(height: DrAiSpacing.md),
                      const FoundationNotice(),
                      const SizedBox(height: DrAiSpacing.lg),
                      const Wrap(
                        spacing: DrAiSpacing.md,
                        runSpacing: DrAiSpacing.md,
                        children: <Widget>[
                          SizedBox(
                            width: 320,
                            child: SectionCard(
                              title: 'Quick access',
                              child: Text(
                                'Patient records and imaging entry points',
                              ),
                            ),
                          ),
                          SizedBox(
                            width: 320,
                            child: SectionCard(
                              title: 'Recent activity',
                              child: Text(
                                'No activity in the foundation build',
                              ),
                            ),
                          ),
                          SizedBox(
                            width: 320,
                            child: SectionCard(
                              title: 'Team and resources',
                              child: Text('Read-only placeholders'),
                            ),
                          ),
                        ],
                      ),
                    ],
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
