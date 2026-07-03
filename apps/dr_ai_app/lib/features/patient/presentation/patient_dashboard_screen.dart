import 'package:dr_ai_app/design_system/dr_ai_tokens.dart';
import 'package:dr_ai_app/shared/widgets/foundation_notice.dart';
import 'package:dr_ai_app/shared/widgets/section_card.dart';
import 'package:flutter/material.dart';

class PatientDashboardScreen extends StatelessWidget {
  const PatientDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dr. AI - Patient')),
      body: ListView(
        padding: const EdgeInsets.all(DrAiSpacing.md),
        children: const <Widget>[
          Text(
            'Today',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700),
          ),
          SizedBox(height: DrAiSpacing.md),
          FoundationNotice(),
          SizedBox(height: DrAiSpacing.md),
          SectionCard(
            title: 'Recovery plan',
            child: Text('No active plan in the foundation build'),
          ),
          SizedBox(height: DrAiSpacing.md),
          SectionCard(
            title: 'Contact doctor',
            child: Text('Contact actions are not enabled yet'),
          ),
          SizedBox(height: DrAiSpacing.md),
          SectionCard(
            title: 'Medical records and imaging',
            child: Text('No synthetic records have been added'),
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: 0,
        destinations: const <NavigationDestination>[
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.phone_outlined),
            label: 'Contact',
          ),
          NavigationDestination(
            icon: Icon(Icons.medical_services_outlined),
            label: 'Medical Service',
          ),
          NavigationDestination(
            icon: Icon(Icons.assignment_outlined),
            label: 'Recovery Plan',
          ),
        ],
      ),
    );
  }
}
