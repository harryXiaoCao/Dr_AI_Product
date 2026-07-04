enum AppRole {
  doctor,
  patient;

  static AppRole fromWire(String value) {
    return switch (value.trim().toLowerCase()) {
      'patient' => AppRole.patient,
      _ => AppRole.doctor,
    };
  }

  String get wireValue => name;
}
