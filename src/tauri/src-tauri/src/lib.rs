use notify::{recommended_watcher, Event, RecursiveMode, Watcher};
use percent_encoding::percent_decode_str;
use portable_pty::{native_pty_system, CommandBuilder, PtySize};
use serde::{Deserialize, Serialize};
use std::io::{Read as IoRead, Write as IoWrite};
use std::path::PathBuf;
use std::sync::Mutex;
use tauri::{AppHandle, Emitter, Manager};
use tokio::sync::mpsc;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputFile {
    pub filename: String,
    pub path: String,
    pub size: u64,
    pub modified: u64,
    pub file_type: String,
    pub folder: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineConfig {
    pub ticker: String,
    pub sector: String,
    pub auto_mode: bool,
    pub sources_dir: Option<String>,
    pub reference_peers: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GateDecision {
    pub step_index: usize,
    pub approved: bool,
    pub notes: String,
}

struct WatcherState {
    watcher: Option<Box<dyn Watcher + Send>>,
}

struct WatcherHolder(Mutex<WatcherState>);

#[tauri::command]
fn get_project_root() -> String {
    // Walk up from the executable to find the project root
    let mut dir = std::env::current_dir().unwrap_or_default();
    loop {
        if dir.join("CLAUDE.md").exists() {
            return dir.to_string_lossy().to_string();
        }
        if !dir.pop() {
            break;
        }
    }
    std::env::current_dir()
        .unwrap_or_default()
        .to_string_lossy()
        .to_string()
}

/// Check if a directory name matches YYYY-MM-DD or YYYY-MM-DD-runN
fn is_run_dir(name: &str) -> bool {
    if name.len() < 10 {
        return false;
    }
    // Validate calendar date via chrono (rejects invalid dates like 2026-13-01)
    if chrono::NaiveDate::parse_from_str(&name[..10], "%Y-%m-%d").is_err() {
        return false;
    }
    // Exact YYYY-MM-DD
    if name.len() == 10 {
        return true;
    }
    // YYYY-MM-DD-runN
    name.get(10..).map_or(false, |suffix| {
        suffix.starts_with("-run")
            && suffix.len() > 4
            && suffix[4..].chars().all(|c| c.is_ascii_digit())
    })
}

/// List all date-stamped analysis runs for a ticker
#[tauri::command]
fn list_analysis_runs(ticker: String) -> Vec<String> {
    let root = get_project_root();
    let dir = PathBuf::from(&root)
        .join("data")
        .join("processed")
        .join(ticker.to_lowercase());
    let mut runs: Vec<String> = std::fs::read_dir(&dir)
        .map(|entries| {
            entries
                .flatten()
                .filter(|e| e.file_type().map(|t| t.is_dir()).unwrap_or(false))
                .filter_map(|e| {
                    let name = e.file_name().to_string_lossy().to_string();
                    if is_run_dir(&name) {
                        Some(name)
                    } else {
                        None
                    }
                })
                .collect()
        })
        .unwrap_or_default();
    runs.sort();
    runs.reverse(); // newest first
    runs
}

/// Resolve the next available run directory name for today
#[tauri::command]
fn resolve_next_run_dir(ticker: String) -> String {
    let today = chrono::Local::now().format("%Y-%m-%d").to_string();
    let existing = list_analysis_runs(ticker);
    // Filter to today's runs: "2026-03-07", "2026-03-07-run2", etc.
    let today_runs: Vec<&String> = existing.iter().filter(|r| r.starts_with(&today)).collect();
    if today_runs.is_empty() {
        return today;
    }
    // Find highest -runN among today's runs
    let max_n = today_runs.iter().filter_map(|r| {
        if r.len() == today.len() {
            Some(1) // base date counts as run 1
        } else {
            r.get(today.len()..).and_then(|s| s.strip_prefix("-run")).and_then(|n| n.parse::<u32>().ok())
        }
    }).max().unwrap_or(1);
    format!("{}-run{}", today, max_n + 1)
}

#[tauri::command]
fn list_outputs(ticker: String, run_date: Option<String>) -> Vec<OutputFile> {
    let root = get_project_root();
    let base = PathBuf::from(&root)
        .join("data")
        .join("processed")
        .join(ticker.to_lowercase());

    // Find the run directory — use provided date or latest
    let run_dir = if let Some(date) = run_date {
        base.join(date)
    } else {
        // Find latest date folder
        let runs = list_analysis_runs(ticker);
        if let Some(latest) = runs.first() {
            base.join(latest)
        } else {
            return Vec::new();
        }
    };

    let mut files = Vec::new();
    scan_dir_recursive(&run_dir, &run_dir, &mut files);
    // Sort by folder then filename
    files.sort_by(|a, b| (&a.folder, &a.filename).cmp(&(&b.folder, &b.filename)));
    files
}

fn scan_dir_recursive(base: &PathBuf, dir: &PathBuf, files: &mut Vec<OutputFile>) {
    if let Ok(entries) = std::fs::read_dir(dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                scan_dir_recursive(base, &path, files);
            } else if path.is_file() {
                let name = entry.file_name().to_string_lossy().to_string();
                if name.starts_with('.') || name == "pipeline_state.json" {
                    continue;
                }
                let ext = path
                    .extension()
                    .map(|e| e.to_string_lossy().to_string())
                    .unwrap_or_default();
                let folder = path
                    .parent()
                    .and_then(|p| p.strip_prefix(base).ok())
                    .map(|p| p.to_string_lossy().to_string())
                    .unwrap_or_default();
                let meta = entry.metadata().ok();
                files.push(OutputFile {
                    filename: name,
                    path: path.to_string_lossy().to_string(),
                    size: meta.as_ref().map(|m| m.len()).unwrap_or(0),
                    modified: meta
                        .as_ref()
                        .and_then(|m| m.modified().ok())
                        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                        .map(|d| d.as_secs())
                        .unwrap_or(0),
                    file_type: ext,
                    folder,
                });
            }
        }
    }
}

#[tauri::command]
fn read_output_file(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path).map_err(|e| format!("Failed to read file: {}", e))
}

#[tauri::command]
async fn start_file_watcher(app: AppHandle, ticker: String) -> Result<(), String> {
    let root = get_project_root();
    let watch_dir = PathBuf::from(&root)
        .join("data")
        .join("processed")
        .join(ticker.to_lowercase());

    if !watch_dir.exists() {
        std::fs::create_dir_all(&watch_dir)
            .map_err(|e| format!("Failed to create dir: {}", e))?;
    }

    let (tx, mut rx) = mpsc::channel::<Event>(100);

    let mut watcher = recommended_watcher(move |res: Result<Event, notify::Error>| {
        if let Ok(event) = res {
            let _ = tx.blocking_send(event);
        }
    })
    .map_err(|e| format!("Failed to create watcher: {}", e))?;

    watcher
        .watch(&watch_dir, RecursiveMode::Recursive)
        .map_err(|e| format!("Failed to watch directory: {}", e))?;

    // Store watcher to keep it alive (replace any previous watcher)
    let holder = app.state::<WatcherHolder>();
    let mut ws = holder.0.lock().map_err(|e| format!("{}", e))?;
    ws.watcher = Some(Box::new(watcher));

    let app_clone = app.clone();
    let ticker_clone = ticker.clone();
    tokio::spawn(async move {
        while let Some(_event) = rx.recv().await {
            let files = list_outputs(ticker_clone.clone(), None);
            let _ = app_clone.emit("output-files-changed", &files);
        }
    });

    Ok(())
}

#[tauri::command]
fn save_pipeline_state(ticker: String, run_date: Option<String>, state: String) -> Result<(), String> {
    let root = get_project_root();
    let mut dir = PathBuf::from(&root)
        .join("data")
        .join("processed")
        .join(ticker.to_lowercase());
    if let Some(ref rd) = run_date {
        dir = dir.join(rd);
    }
    std::fs::create_dir_all(&dir).map_err(|e| format!("{}", e))?;
    let path = dir.join("pipeline_state.json");
    std::fs::write(&path, state).map_err(|e| format!("{}", e))?;
    Ok(())
}

#[tauri::command]
fn load_pipeline_state(ticker: String, run_date: Option<String>) -> Result<Option<String>, String> {
    let root = get_project_root();
    let mut dir = PathBuf::from(&root)
        .join("data")
        .join("processed")
        .join(ticker.to_lowercase());
    if let Some(ref rd) = run_date {
        dir = dir.join(rd);
    }
    let path = dir.join("pipeline_state.json");
    if path.exists() {
        let content = std::fs::read_to_string(&path).map_err(|e| format!("{}", e))?;
        Ok(Some(content))
    } else {
        // Fallback: try the old per-ticker location for backwards compat
        let fallback = PathBuf::from(&root)
            .join("data")
            .join("processed")
            .join(ticker.to_lowercase())
            .join("pipeline_state.json");
        if run_date.is_some() && fallback.exists() {
            let content = std::fs::read_to_string(&fallback).map_err(|e| format!("{}", e))?;
            Ok(Some(content))
        } else {
            Ok(None)
        }
    }
}

#[tauri::command]
fn open_in_browser(path: String) -> Result<(), String> {
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("{}", e))?;
    }
    Ok(())
}

#[tauri::command]
fn read_html_summary(path: String) -> Result<String, String> {
    let content = std::fs::read_to_string(&path)
        .map_err(|e| format!("Failed to read file: {}", e))?;

    // Extract executive summary section from the HTML
    if let Some(start) = content.find("Executive Summary") {
        let section = &content[start..];
        // Find the next major section heading (h2 or similar)
        let end = section[20..].find("<h2")
            .or_else(|| section[20..].find("<section"))
            .map(|i| i + 20)
            .unwrap_or(2000.min(section.len()));
        // Strip HTML tags for a plain text preview
        let snippet = &section[..end];
        let plain = snippet
            .replace("<br>", "\n")
            .replace("<br/>", "\n")
            .replace("</p>", "\n")
            .replace("</li>", "\n");
        // Remove remaining HTML tags
        let mut result = String::new();
        let mut in_tag = false;
        for ch in plain.chars() {
            match ch {
                '<' => in_tag = true,
                '>' => in_tag = false,
                _ if !in_tag => result.push(ch),
                _ => {}
            }
        }
        // Trim and limit
        let trimmed: String = result.lines()
            .map(|l| l.trim())
            .filter(|l| !l.is_empty())
            .take(20)
            .collect::<Vec<_>>()
            .join("\n");
        Ok(trimmed)
    } else {
        Ok("Report generated. Open to view full content.".to_string())
    }
}

#[tauri::command]
fn copy_tone_files(ticker: String, files: Vec<String>) -> Result<String, String> {
    let root = get_project_root();
    let dest_dir = PathBuf::from(&root)
        .join("data")
        .join("raw")
        .join(ticker.to_lowercase())
        .join("style-references");
    std::fs::create_dir_all(&dest_dir).map_err(|e| format!("{}", e))?;
    for file in &files {
        let src = PathBuf::from(file);
        if let Some(filename) = src.file_name() {
            let dest = dest_dir.join(filename);
            std::fs::copy(&src, &dest).map_err(|e| format!("Failed to copy {}: {}", file, e))?;
        }
    }
    Ok(dest_dir.to_string_lossy().to_string())
}

#[tauri::command]
fn ensure_source_dirs(ticker: String) -> Result<[String; 2], String> {
    let root = get_project_root();
    let base = PathBuf::from(&root).join("data").join("raw").join(ticker.to_lowercase());
    let sell_side = base.join("sell-side-data");
    let consulting = base.join("consulting-research");
    std::fs::create_dir_all(&sell_side).map_err(|e| format!("{}", e))?;
    std::fs::create_dir_all(&consulting).map_err(|e| format!("{}", e))?;
    Ok([
        sell_side.to_string_lossy().to_string(),
        consulting.to_string_lossy().to_string(),
    ])
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepCompletionInfo {
    pub step_index: usize,
    pub step_name: String,
    pub files_found: Vec<String>,
    pub complete: bool,
}

#[tauri::command]
fn detect_existing_session(ticker: String) -> Vec<StepCompletionInfo> {
    let root = get_project_root();
    let base = PathBuf::from(&root)
        .join("data")
        .join("processed")
        .join(ticker.to_lowercase());

    // Find latest run
    let runs = list_analysis_runs(ticker);
    let run_dir = if let Some(latest) = runs.first() {
        base.join(latest)
    } else {
        return Vec::new();
    };

    // Map pipeline steps to their expected subfolders and filenames
    let step_checks: Vec<(usize, &str, &str, Vec<&str>)> = vec![
        (0, "Map the Industry", "1-universe", vec!["peer_universe.json", "metric_taxonomy.json", "source_catalog.json"]),
        (1, "Gather Data", "2-data", vec!["quantitative_data.json", "strategy_profiles.json", "strategic_actions.json"]),
        (2, "Find What Drives Value", "3-analysis", vec!["standardized_data.json", "correlations.json", "driver_ranking.json", "final_peer_set.json"]),
        (3, "Deep-Dive Peers", "4-deep-dives", vec!["platform_profiles.json", "asset_class_analysis.json"]),
        (4, "Build the Playbook", "5-playbook", vec!["value_principles.md", "platform_playbook.json", "final_report.html"]),
        (5, "Review Analysis", "6-review", vec!["methodology_review.md", "results_review.md"]),
    ];

    step_checks
        .into_iter()
        .map(|(index, name, folder, expected_files)| {
            let folder_path = run_dir.join(folder);
            let found: Vec<String> = std::fs::read_dir(&folder_path)
                .map(|entries| {
                    entries
                        .flatten()
                        .map(|e| e.file_name().to_string_lossy().to_string())
                        .collect()
                })
                .unwrap_or_default();
            let complete = expected_files.iter().all(|f| found.iter().any(|e| e == f));
            StepCompletionInfo {
                step_index: index,
                step_name: name.to_string(),
                files_found: found,
                complete,
            }
        })
        .collect()
}

#[tauri::command]
fn write_output_file(path: String, content: String) -> Result<(), String> {
    std::fs::write(&path, content).map_err(|e| format!("Failed to write file: {}", e))
}

#[tauri::command]
fn read_json_as_table(path: String) -> Result<String, String> {
    let content = std::fs::read_to_string(&path)
        .map_err(|e| format!("Failed to read file: {}", e))?;
    let value: serde_json::Value = serde_json::from_str(&content)
        .map_err(|e| format!("Invalid JSON: {}", e))?;
    Ok(json_value_to_html(&value, 0))
}

const MAX_DEPTH: usize = 3;
const MAX_ROWS: usize = 100;

fn json_value_to_html(value: &serde_json::Value, depth: usize) -> String {
    if depth >= MAX_DEPTH {
        return format!(
            "<pre class=\"nested-json\">{}</pre>",
            html_escape(&serde_json::to_string_pretty(value).unwrap_or_default())
        );
    }
    match value {
        serde_json::Value::Array(arr) if !arr.is_empty() && arr.iter().all(|v| v.is_object()) => {
            let mut keys: Vec<String> = Vec::new();
            for item in arr {
                if let serde_json::Value::Object(map) = item {
                    for k in map.keys() {
                        if !keys.contains(k) {
                            keys.push(k.clone());
                        }
                    }
                }
            }
            let mut html = String::from("<table><thead><tr>");
            for k in &keys {
                html.push_str(&format!("<th>{}</th>", html_escape(k)));
            }
            html.push_str("</tr></thead><tbody>");
            let display_count = arr.len().min(MAX_ROWS);
            for item in arr.iter().take(display_count) {
                html.push_str("<tr>");
                if let serde_json::Value::Object(map) = item {
                    for k in &keys {
                        html.push_str("<td>");
                        match map.get(k) {
                            Some(v) if v.is_object() || v.is_array() => {
                                html.push_str(&json_value_to_html(v, depth + 1));
                            }
                            Some(v) => html.push_str(&html_escape(&json_display(v))),
                            None => html.push_str("<span class=\"null\">—</span>"),
                        }
                        html.push_str("</td>");
                    }
                }
                html.push_str("</tr>");
            }
            if arr.len() > MAX_ROWS {
                html.push_str(&format!(
                    "<tr><td colspan=\"{}\" class=\"truncated\">… {} more rows</td></tr>",
                    keys.len(),
                    arr.len() - MAX_ROWS
                ));
            }
            html.push_str("</tbody></table>");
            html
        }
        serde_json::Value::Array(arr) => {
            let mut html = String::from("<table><tbody>");
            let display_count = arr.len().min(MAX_ROWS);
            for (i, item) in arr.iter().enumerate().take(display_count) {
                html.push_str(&format!("<tr><th>{}</th><td>", i));
                if item.is_object() || item.is_array() {
                    html.push_str(&json_value_to_html(item, depth + 1));
                } else {
                    html.push_str(&html_escape(&json_display(item)));
                }
                html.push_str("</td></tr>");
            }
            if arr.len() > MAX_ROWS {
                html.push_str(&format!(
                    "<tr><td colspan=\"2\" class=\"truncated\">… {} more items</td></tr>",
                    arr.len() - MAX_ROWS
                ));
            }
            html.push_str("</tbody></table>");
            html
        }
        serde_json::Value::Object(map) => {
            let mut html = String::from("<table><tbody>");
            for (k, v) in map {
                html.push_str(&format!("<tr><th>{}</th><td>", html_escape(k)));
                if v.is_object() || v.is_array() {
                    html.push_str(&json_value_to_html(v, depth + 1));
                } else {
                    html.push_str(&html_escape(&json_display(v)));
                }
                html.push_str("</td></tr>");
            }
            html.push_str("</tbody></table>");
            html
        }
        other => html_escape(&json_display(other)),
    }
}

fn json_display(v: &serde_json::Value) -> String {
    match v {
        serde_json::Value::String(s) => s.clone(),
        serde_json::Value::Null => "null".to_string(),
        serde_json::Value::Bool(b) => b.to_string(),
        serde_json::Value::Number(n) => n.to_string(),
        other => other.to_string(),
    }
}

fn html_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

#[derive(Serialize)]
struct ContractResult {
    passed: bool,
    message: String,
}

#[tauri::command]
async fn validate_contract(run_dir: String) -> Result<ContractResult, String> {
    let root = get_project_root();
    let output = std::process::Command::new("python3")
        .arg("-m")
        .arg("src.validation.vda_contracts")
        .arg(&run_dir)
        .current_dir(&root)
        .output()
        .map_err(|e| format!("Failed to run validator: {}", e))?;

    let passed = output.status.success();
    let message = if passed {
        String::from_utf8_lossy(&output.stdout).trim().to_string()
    } else {
        String::from_utf8_lossy(&output.stderr).trim().to_string()
    };

    Ok(ContractResult { passed, message })
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LaunchConfig {
    pub ticker: Option<String>,
    pub auto_mode: bool,
    pub sector: Option<String>,
}

#[tauri::command]
fn get_launch_config() -> LaunchConfig {
    LaunchConfig {
        ticker: std::env::var("VDA_TICKER").ok().filter(|s| !s.is_empty()),
        auto_mode: std::env::var("VDA_AUTO").ok().map(|v| v == "true" || v == "1").unwrap_or(false),
        sector: std::env::var("VDA_SECTOR").ok().filter(|s| !s.is_empty()),
    }
}

// --- PTY terminal emulator ---

struct PtyState {
    writer: Option<Box<dyn IoWrite + Send>>,
    child: Option<Box<dyn portable_pty::Child + Send>>,
}

struct PtyHolder(Mutex<PtyState>);

#[tauri::command]
async fn pty_spawn(app: AppHandle, command: String, args: Vec<String>, cols: u16, rows: u16) -> Result<(), String> {
    let pty_system = native_pty_system();
    let pair = pty_system
        .openpty(PtySize {
            rows,
            cols,
            pixel_width: 0,
            pixel_height: 0,
        })
        .map_err(|e| format!("Failed to open PTY: {}", e))?;

    let mut cmd = CommandBuilder::new(&command);
    cmd.args(&args);

    // Set working directory to project root
    let root = get_project_root();
    cmd.cwd(&root);

    // Remove CLAUDECODE env var so claude CLI doesn't refuse to run
    cmd.env_remove("CLAUDECODE");

    // Ensure PATH includes common binary locations
    if let Ok(path) = std::env::var("PATH") {
        let home = std::env::var("HOME").unwrap_or_default();
        let extra = format!("{}/.cargo/bin:{}/.local/bin:/usr/local/bin:{}", home, home, path);
        cmd.env("PATH", extra);
    }

    let child = pair
        .slave
        .spawn_command(cmd)
        .map_err(|e| format!("Failed to spawn command: {}", e))?;

    let writer = pair
        .master
        .take_writer()
        .map_err(|e| format!("Failed to get PTY writer: {}", e))?;

    // Store PTY state — replace any existing session
    let holder = app.state::<PtyHolder>();
    let mut state = holder.0.lock().map_err(|e| format!("{}", e))?;
    // Kill any previous child
    if let Some(ref mut old_child) = state.child {
        let _ = old_child.kill();
    }
    state.writer = Some(writer);
    state.child = Some(child);
    drop(state);

    // Read PTY output in a background thread and emit events
    let mut reader = pair
        .master
        .try_clone_reader()
        .map_err(|e| format!("Failed to get PTY reader: {}", e))?;

    let app_clone = app.clone();
    std::thread::spawn(move || {
        use base64::Engine;
        let mut buf = [0u8; 16384];
        let mut pending = Vec::with_capacity(32768);
        let mut last_emit = std::time::Instant::now();
        let throttle = std::time::Duration::from_millis(16); // ~60fps max

        eprintln!("[PTY] Reader thread started");
        loop {
            match reader.read(&mut buf) {
                Ok(0) => {
                    eprintln!("[PTY] EOF");
                    // Flush remaining data
                    if !pending.is_empty() {
                        let encoded = base64::engine::general_purpose::STANDARD.encode(&pending);
                        let _ = app_clone.emit("pty-output", &encoded);
                    }
                    break;
                }
                Ok(n) => {
                    pending.extend_from_slice(&buf[..n]);
                    let now = std::time::Instant::now();
                    if now.duration_since(last_emit) >= throttle || pending.len() > 32768 {
                        let encoded = base64::engine::general_purpose::STANDARD.encode(&pending);
                        let _ = app_clone.emit("pty-output", &encoded);
                        pending.clear();
                        last_emit = now;
                    }
                }
                Err(e) => {
                    eprintln!("[PTY] Read error: {}", e);
                    if !pending.is_empty() {
                        let encoded = base64::engine::general_purpose::STANDARD.encode(&pending);
                        let _ = app_clone.emit("pty-output", &encoded);
                    }
                    break;
                }
            }
        }
        let _ = app_clone.emit("pty-exit", ());
    });

    Ok(())
}

#[tauri::command]
fn pty_write(app: AppHandle, data: String) -> Result<(), String> {
    let holder = app.state::<PtyHolder>();
    let mut state = holder.0.lock().map_err(|e| format!("{}", e))?;
    if let Some(ref mut writer) = state.writer {
        writer.write_all(data.as_bytes()).map_err(|e| format!("{}", e))?;
    }
    Ok(())
}

#[tauri::command]
fn pty_resize(app: AppHandle, cols: u16, rows: u16) -> Result<(), String> {
    // portable-pty resize is on the master, but we stored writer/child.
    // For now, resize is a no-op — xterm handles display sizing.
    let _ = (app, cols, rows);
    Ok(())
}

#[tauri::command]
fn pty_kill(app: AppHandle) -> Result<(), String> {
    let holder = app.state::<PtyHolder>();
    let mut state = holder.0.lock().map_err(|e| format!("{}", e))?;
    if let Some(ref mut child) = state.child {
        child.kill().map_err(|e| format!("{}", e))?;
    }
    state.writer = None;
    state.child = None;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(PtyHolder(Mutex::new(PtyState { writer: None, child: None })))
        .manage(WatcherHolder(Mutex::new(WatcherState { watcher: None })))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_notification::init())
        .register_uri_scheme_protocol("vdafile", |_ctx, request| {
            let uri = request.uri();
            // URI format: vdafile://localhost/absolute/path/to/file.html
            let raw_path = uri.path();
            let file_path = percent_decode_str(raw_path)
                .decode_utf8_lossy()
                .to_string();

            let mime = if file_path.ends_with(".html") {
                "text/html"
            } else if file_path.ends_with(".css") {
                "text/css"
            } else if file_path.ends_with(".js") {
                "application/javascript"
            } else if file_path.ends_with(".json") {
                "application/json"
            } else if file_path.ends_with(".png") {
                "image/png"
            } else if file_path.ends_with(".svg") {
                "image/svg+xml"
            } else {
                "text/plain"
            };

            match std::fs::read(&file_path) {
                Ok(content) => tauri::http::Response::builder()
                    .header("Content-Type", mime)
                    .header("Access-Control-Allow-Origin", "*")
                    .body(content)
                    .unwrap(),
                Err(_) => tauri::http::Response::builder()
                    .status(404)
                    .body(b"File not found".to_vec())
                    .unwrap(),
            }
        })
        .invoke_handler(tauri::generate_handler![
            get_project_root,
            list_analysis_runs,
            list_outputs,
            read_output_file,
            write_output_file,
            start_file_watcher,
            save_pipeline_state,
            load_pipeline_state,
            ensure_source_dirs,
            open_in_browser,
            read_html_summary,
            detect_existing_session,
            read_json_as_table,
            copy_tone_files,
            resolve_next_run_dir,
            get_launch_config,
            pty_spawn,
            pty_write,
            pty_resize,
            pty_kill,
            validate_contract,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
