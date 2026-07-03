enum AppRole {
  doctor,
  patient;

  static AppRole fromEnvironment(String value) {
    return switch (value.trim().toLowerCase()) {
      'patient' => AppRole.patient,
      _ => AppRole.doctor,
    };
  }
}
