/// Initialize environment variables needed before runtime startup.
pub fn bootstrap_env() {
    std::env::set_var("APP_MODE", "test");
    std::env::remove_var("LEGACY_MODE");
}

