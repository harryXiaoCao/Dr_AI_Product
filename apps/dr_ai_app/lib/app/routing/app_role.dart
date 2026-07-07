enum AppRole {
  doctor,
  patient,
  unsupported;

  static AppRole fromWire(String value) {
    return switch (value.trim().toLowerCase()) {
      'doctor' => AppRole.doctor,
      'patient' => AppRole.patient,
      _ => AppRole.unsupported,
    };
  }

  String get wireValue => name;
}
