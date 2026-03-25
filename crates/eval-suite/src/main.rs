use std::collections::{BTreeMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Instant, SystemTime, UNIX_EPOCH};

use anyhow::{Context, Result, anyhow, bail};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};

fn main() -> Result<()> {
    let cli = Cli::parse();
    let root = std::env::current_dir().context("failed to determine current directory")?;
    let suite = Suite::load(&root)?;

    match cli.command {
        Commands::List { layer } => list_cases(&suite, layer.as_deref()),
        Commands::Validate { case } => validate_cases(&suite, case.as_deref()),
        Commands::Prepare { case, out, force } => prepare_case(&suite, &case, out.as_deref(), force),
        Commands::Run {
            case,
            submission,
            artifacts,
            fail_fast,
        } => run_case(&suite, &case, &submission, artifacts.as_deref(), fail_fast),
    }
}

#[derive(Parser, Debug)]
#[command(author, version, about = "Rust LLM evaluation suite runner")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    List {
        #[arg(long)]
        layer: Option<String>,
    },
    Validate {
        #[arg(long)]
        case: Option<String>,
    },
    Prepare {
        #[arg(long)]
        case: String,
        #[arg(long)]
        out: Option<PathBuf>,
        #[arg(long, default_value_t = false)]
        force: bool,
    },
    Run {
        #[arg(long)]
        case: String,
        #[arg(long)]
        submission: PathBuf,
        #[arg(long)]
        artifacts: Option<PathBuf>,
        #[arg(long, default_value_t = false)]
        fail_fast: bool,
    },
}

#[derive(Debug)]
struct Suite {
    root: PathBuf,
    config: SuiteConfig,
    cases: Vec<CaseDefinition>,
}

impl Suite {
    fn load(root: &Path) -> Result<Self> {
        let config_path = root.join("suite.toml");
        let config_text = fs::read_to_string(&config_path)
            .with_context(|| format!("failed to read {}", config_path.display()))?;
        let config: SuiteConfig = toml::from_str(&config_text)
            .with_context(|| format!("failed to parse {}", config_path.display()))?;

        let cases_root = root.join(&config.cases_dir);
        let mut metas = Vec::new();
        collect_meta_files(&cases_root, &mut metas)?;

        let mut cases = Vec::new();
        for meta_path in metas {
            let meta_text = fs::read_to_string(&meta_path)
                .with_context(|| format!("failed to read {}", meta_path.display()))?;
            let meta: CaseMeta = serde_yaml::from_str(&meta_text)
                .with_context(|| format!("failed to parse {}", meta_path.display()))?;
            let case_dir = meta_path
                .parent()
                .ok_or_else(|| anyhow!("case meta has no parent: {}", meta_path.display()))?
                .to_path_buf();
            cases.push(CaseDefinition::from_parts(case_dir, meta_path, meta));
        }

        cases.sort_by(|left, right| left.meta.id.cmp(&right.meta.id));

        Ok(Self {
            root: root.to_path_buf(),
            config,
            cases,
        })
    }

    fn find_case(&self, case_id: &str) -> Result<&CaseDefinition> {
        self.cases
            .iter()
            .find(|case| case.meta.id == case_id)
            .ok_or_else(|| anyhow!("case `{case_id}` not found"))
    }

    fn command_for(&self, check: &CheckKind) -> &CommandSpec {
        match check {
            CheckKind::Check => &self.config.commands.check,
            CheckKind::Clippy => &self.config.commands.clippy,
            CheckKind::Test => &self.config.commands.test,
            CheckKind::Fmt => &self.config.commands.fmt,
            CheckKind::Doc => &self.config.commands.doc,
            CheckKind::Doctest => &self.config.commands.doctest,
        }
    }

    fn resolved_checks(&self, case: &CaseDefinition) -> Result<Vec<CheckKind>> {
        if !case.meta.checks.is_empty() {
            return Ok(case.meta.checks.clone());
        }

        self.config
            .layer_defaults
            .get(&case.meta.layer)
            .map(|defaults| defaults.checks.clone())
            .ok_or_else(|| anyhow!("no default checks configured for layer `{}`", case.meta.layer))
    }

    fn runs_root(&self) -> PathBuf {
        self.root.join(&self.config.runs_dir)
    }
}

#[derive(Debug, Deserialize)]
struct SuiteConfig {
    version: u32,
    cases_dir: String,
    runs_dir: String,
    commands: CommandsConfig,
    layer_defaults: BTreeMap<String, LayerDefaults>,
}

#[derive(Debug, Deserialize)]
struct CommandsConfig {
    check: CommandSpec,
    clippy: CommandSpec,
    test: CommandSpec,
    fmt: CommandSpec,
    doc: CommandSpec,
    doctest: CommandSpec,
}

#[derive(Debug, Deserialize, Clone)]
struct CommandSpec {
    program: String,
    args: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct LayerDefaults {
    checks: Vec<CheckKind>,
}

#[derive(Debug)]
struct CaseDefinition {
    meta_path: PathBuf,
    prompt_path: PathBuf,
    starter_dir: PathBuf,
    oracle_overlay_dir: PathBuf,
    meta: CaseMeta,
}

impl CaseDefinition {
    fn from_parts(dir: PathBuf, meta_path: PathBuf, meta: CaseMeta) -> Self {
        let prompt_path = dir.join("prompt.md");
        let starter_dir = dir.join("starter");
        let oracle_overlay_dir = dir.join("oracle").join("overlay");
        Self {
            meta_path,
            prompt_path,
            starter_dir,
            oracle_overlay_dir,
            meta,
        }
    }
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct CaseMeta {
    id: String,
    title: String,
    layer: String,
    category: String,
    edition: String,
    difficulty: String,
    repair_vs_generate: String,
    #[serde(default)]
    checks: Vec<CheckKind>,
    #[serde(default)]
    tags: Vec<String>,
    #[serde(default)]
    requires_async: bool,
    #[serde(default, rename = "unsafe")]
    r#unsafe: bool,
    #[serde(default)]
    ffi: bool,
    #[serde(default, rename = "macro")]
    macro_case: bool,
}

#[derive(Debug, Deserialize, Serialize, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "snake_case")]
enum CheckKind {
    Check,
    Clippy,
    Test,
    Fmt,
    Doc,
    Doctest,
}

impl std::fmt::Display for CheckKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let value = match self {
            CheckKind::Check => "check",
            CheckKind::Clippy => "clippy",
            CheckKind::Test => "test",
            CheckKind::Fmt => "fmt",
            CheckKind::Doc => "doc",
            CheckKind::Doctest => "doctest",
        };
        write!(f, "{value}")
    }
}

#[derive(Debug, Serialize)]
struct RunReport {
    suite_version: u32,
    case_id: String,
    layer: String,
    submission_dir: String,
    artifacts_dir: String,
    success: bool,
    checks: Vec<CheckExecution>,
}

#[derive(Debug, Serialize)]
struct CheckExecution {
    check: CheckKind,
    program: String,
    args: Vec<String>,
    success: bool,
    exit_code: Option<i32>,
    duration_ms: u128,
    stdout_log: String,
    stderr_log: String,
    error: Option<String>,
}

fn list_cases(suite: &Suite, layer: Option<&str>) -> Result<()> {
    for case in &suite.cases {
        if layer.is_some_and(|value| value != case.meta.layer) {
            continue;
        }
        let checks = suite
            .resolved_checks(case)?
            .into_iter()
            .map(|check| check.to_string())
            .collect::<Vec<_>>()
            .join(",");
        println!(
            "{} [{}] {} | difficulty={} | checks={}",
            case.meta.id, case.meta.layer, case.meta.title, case.meta.difficulty, checks
        );
    }
    Ok(())
}

fn validate_cases(suite: &Suite, case_filter: Option<&str>) -> Result<()> {
    let mut seen_ids = HashSet::new();
    let mut validated = 0usize;

    for case in &suite.cases {
        if case_filter.is_some_and(|value| value != case.meta.id) {
            continue;
        }

        if !seen_ids.insert(case.meta.id.clone()) {
            bail!("duplicate case id `{}`", case.meta.id);
        }
        if !case.prompt_path.is_file() {
            bail!("missing prompt file for `{}` at {}", case.meta.id, case.prompt_path.display());
        }
        if !case.starter_dir.is_dir() {
            bail!(
                "missing starter directory for `{}` at {}",
                case.meta.id,
                case.starter_dir.display()
            );
        }
        if case.meta.edition != "2024" {
            bail!(
                "case `{}` targets edition `{}` instead of `2024`",
                case.meta.id,
                case.meta.edition
            );
        }

        let checks = suite.resolved_checks(case)?;
        if checks.contains(&CheckKind::Test) && !case.oracle_overlay_dir.exists() {
            bail!(
                "case `{}` requires `test` but has no oracle overlay at {}",
                case.meta.id,
                case.oracle_overlay_dir.display()
            );
        }

        validated += 1;
    }

    println!("validated {} case(s)", validated);
    Ok(())
}

fn prepare_case(suite: &Suite, case_id: &str, out: Option<&Path>, force: bool) -> Result<()> {
    let case = suite.find_case(case_id)?;
    let target = out
        .map(Path::to_path_buf)
        .unwrap_or_else(|| suite.runs_root().join("prepared").join(sanitize_case_id(case_id)));

    reset_directory(&target, force)?;
    copy_dir_contents(&case.starter_dir, &target)?;
    ensure_standalone_cargo_manifest(&target)?;

    let eval_dir = target.join(".eval");
    fs::create_dir_all(&eval_dir)
        .with_context(|| format!("failed to create {}", eval_dir.display()))?;
    fs::copy(&case.prompt_path, eval_dir.join("prompt.md"))
        .with_context(|| format!("failed to copy {}", case.prompt_path.display()))?;
    fs::copy(&case.meta_path, eval_dir.join("meta.yaml"))
        .with_context(|| format!("failed to copy {}", case.meta_path.display()))?;

    println!(
        "prepared `{}` into {}",
        case.meta.id,
        target.canonicalize().unwrap_or(target).display()
    );
    Ok(())
}

fn run_case(
    suite: &Suite,
    case_id: &str,
    submission: &Path,
    artifacts: Option<&Path>,
    fail_fast: bool,
) -> Result<()> {
    let case = suite.find_case(case_id)?;
    if !submission.is_dir() {
        bail!("submission directory does not exist: {}", submission.display());
    }

    let artifact_dir = artifacts
        .map(Path::to_path_buf)
        .unwrap_or_else(|| suite.runs_root().join("executions").join(run_directory_name(case_id)));
    reset_directory(&artifact_dir, true)?;
    copy_dir_contents(submission, &artifact_dir)?;

    if case.oracle_overlay_dir.exists() {
        copy_dir_contents(&case.oracle_overlay_dir, &artifact_dir)?;
    }
    ensure_standalone_cargo_manifest(&artifact_dir)?;

    let logs_dir = artifact_dir.join(".eval-logs");
    fs::create_dir_all(&logs_dir)
        .with_context(|| format!("failed to create {}", logs_dir.display()))?;

    let mut executions = Vec::new();
    let mut overall_success = true;
    let checks = suite.resolved_checks(case)?;

    for check in checks {
        let spec = suite.command_for(&check).clone();
        let stdout_log = format!("{check}.stdout.log");
        let stderr_log = format!("{check}.stderr.log");
        let stdout_path = logs_dir.join(&stdout_log);
        let stderr_path = logs_dir.join(&stderr_log);

        println!("running `{}` for `{}`", check, case.meta.id);

        let started = Instant::now();
        let output = Command::new(&spec.program)
            .args(&spec.args)
            .current_dir(&artifact_dir)
            .output();
        let duration_ms = started.elapsed().as_millis();

        let execution = match output {
            Ok(output) => {
                fs::write(&stdout_path, &output.stdout)
                    .with_context(|| format!("failed to write {}", stdout_path.display()))?;
                fs::write(&stderr_path, &output.stderr)
                    .with_context(|| format!("failed to write {}", stderr_path.display()))?;

                let success = output.status.success();
                if !success {
                    overall_success = false;
                }

                CheckExecution {
                    check,
                    program: spec.program.clone(),
                    args: spec.args.clone(),
                    success,
                    exit_code: output.status.code(),
                    duration_ms,
                    stdout_log,
                    stderr_log,
                    error: None,
                }
            }
            Err(error) => {
                overall_success = false;
                fs::write(&stdout_path, b"")
                    .with_context(|| format!("failed to write {}", stdout_path.display()))?;
                fs::write(&stderr_path, error.to_string().as_bytes())
                    .with_context(|| format!("failed to write {}", stderr_path.display()))?;

                CheckExecution {
                    check,
                    program: spec.program.clone(),
                    args: spec.args.clone(),
                    success: false,
                    exit_code: None,
                    duration_ms,
                    stdout_log,
                    stderr_log,
                    error: Some(error.to_string()),
                }
            }
        };

        let failed = !execution.success;
        executions.push(execution);

        if failed && fail_fast {
            break;
        }
    }

    let report = RunReport {
        suite_version: suite.config.version,
        case_id: case.meta.id.clone(),
        layer: case.meta.layer.clone(),
        submission_dir: submission.display().to_string(),
        artifacts_dir: artifact_dir.display().to_string(),
        success: overall_success,
        checks: executions,
    };

    let report_path = artifact_dir.join("report.json");
    let report_body = serde_json::to_string_pretty(&report).context("failed to serialize report")?;
    fs::write(&report_path, report_body)
        .with_context(|| format!("failed to write {}", report_path.display()))?;

    println!(
        "finished `{}` success={} artifacts={}",
        case.meta.id,
        report.success,
        artifact_dir.display()
    );

    Ok(())
}

fn collect_meta_files(dir: &Path, metas: &mut Vec<PathBuf>) -> Result<()> {
    if !dir.exists() {
        return Ok(());
    }

    for entry in fs::read_dir(dir).with_context(|| format!("failed to read {}", dir.display()))? {
        let entry = entry.with_context(|| format!("failed to inspect {}", dir.display()))?;
        let path = entry.path();
        if path.is_dir() {
            if path
                .file_name()
                .and_then(|value| value.to_str())
                .is_some_and(|value| value.starts_with('_'))
            {
                continue;
            }
            collect_meta_files(&path, metas)?;
            continue;
        }
        if path
            .file_name()
            .and_then(|value| value.to_str())
            .is_some_and(|value| value == "meta.yaml")
        {
            metas.push(path);
        }
    }

    Ok(())
}

fn reset_directory(path: &Path, force: bool) -> Result<()> {
    if path.exists() {
        if !force {
            bail!(
                "directory already exists: {} (pass --force or choose another path)",
                path.display()
            );
        }
        fs::remove_dir_all(path)
            .with_context(|| format!("failed to remove {}", path.display()))?;
    }
    fs::create_dir_all(path).with_context(|| format!("failed to create {}", path.display()))?;
    Ok(())
}

fn copy_dir_contents(source: &Path, destination: &Path) -> Result<()> {
    fs::create_dir_all(destination)
        .with_context(|| format!("failed to create {}", destination.display()))?;

    for entry in fs::read_dir(source).with_context(|| format!("failed to read {}", source.display()))?
    {
        let entry = entry.with_context(|| format!("failed to inspect {}", source.display()))?;
        let from = entry.path();
        let to = destination.join(entry.file_name());
        if from.is_dir() {
            copy_dir_contents(&from, &to)?;
        } else {
            if let Some(parent) = to.parent() {
                fs::create_dir_all(parent)
                    .with_context(|| format!("failed to create {}", parent.display()))?;
            }
            fs::copy(&from, &to)
                .with_context(|| format!("failed to copy {} to {}", from.display(), to.display()))?;
        }
    }

    Ok(())
}

fn ensure_standalone_cargo_manifest(dir: &Path) -> Result<()> {
    let manifest_path = dir.join("Cargo.toml");
    if !manifest_path.is_file() {
        return Ok(());
    }

    let manifest = fs::read_to_string(&manifest_path)
        .with_context(|| format!("failed to read {}", manifest_path.display()))?;
    if manifest.contains("[workspace]") {
        return Ok(());
    }

    let separator = if manifest.ends_with('\n') { "" } else { "\n" };
    let updated_manifest = format!("{manifest}{separator}\n[workspace]\n");
    fs::write(&manifest_path, updated_manifest)
        .with_context(|| format!("failed to write {}", manifest_path.display()))?;
    Ok(())
}

fn sanitize_case_id(case_id: &str) -> String {
    case_id
        .chars()
        .map(|ch| if ch == '/' || ch == '\\' { '_' } else { ch })
        .collect()
}

fn run_directory_name(case_id: &str) -> String {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    format!("{}-{}", sanitize_case_id(case_id), timestamp)
}
