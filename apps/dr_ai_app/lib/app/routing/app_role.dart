enum AppRole {
  doctor,
  patient,
  payer,
  admin,
  unsupported;

  static AppRole fromWire(String value) {
    return switch (value.trim().toLowerCase()) {
      'doctor' => AppRole.doctor,
      'patient' => AppRole.patient,
      'payer' => AppRole.payer,
      'admin' => AppRole.admin,
      _ => AppRole.unsupported,
    };
  }

  String get wireValue => name;
}
