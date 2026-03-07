use notify::{recommended_watcher, Event, RecursiveMode, Watcher};
use percent_encoding::percent_decode_str;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter, Manager};
use tokio::sync::mpsc;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputFile {
    pub filename: String,
    pub path: String,
    pub size: u64,
    pub modified: u64,
    pub file_type: String,
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
    _watcher: Box<dyn Watcher + Send>,
}

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

#[tauri::command]
fn list_outputs(ticker: String) -> Vec<OutputFile> {
    let root = get_project_root();
    let dir = PathBuf::from(&root)
        .join("data")
        .join("processed")
        .join(ticker.to_lowercase());

    let mut files = Vec::new();
    if let Ok(entries) = std::fs::read_dir(&dir) {
        for entry in entries.flatten() {
            if let Ok(meta) = entry.metadata() {
                if meta.is_file() {
                    let name = entry.file_name().to_string_lossy().to_string();
                    if name.starts_with("peer_vd_") {
                        let ext = entry
                            .path()
                            .extension()
                            .map(|e| e.to_string_lossy().to_string())
                            .unwrap_or_default();
                        files.push(OutputFile {
                            filename: name,
                            path: entry.path().to_string_lossy().to_string(),
                            size: meta.len(),
                            modified: meta
                                .modified()
                                .ok()
                                .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                                .map(|d| d.as_secs())
                                .unwrap_or(0),
                            file_type: ext,
                        });
                    }
                }
            }
        }
    }
    files.sort_by(|a, b| a.filename.cmp(&b.filename));
    files
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
        .watch(&watch_dir, RecursiveMode::NonRecursive)
        .map_err(|e| format!("Failed to watch directory: {}", e))?;

    // Store watcher to keep it alive
    app.manage(Arc::new(Mutex::new(WatcherState {
        _watcher: Box::new(watcher),
    })));

    let app_clone = app.clone();
    let ticker_clone = ticker.clone();
    tokio::spawn(async move {
        while let Some(_event) = rx.recv().await {
            let files = list_outputs(ticker_clone.clone());
            let _ = app_clone.emit("output-files-changed", &files);
        }
    });

    Ok(())
}

#[tauri::command]
fn save_pipeline_state(ticker: String, state: String) -> Result<(), String> {
    let root = get_project_root();
    let dir = PathBuf::from(&root)
        .join("data")
        .join("processed")
        .join(ticker.to_lowercase());
    std::fs::create_dir_all(&dir).map_err(|e| format!("{}", e))?;
    let path = dir.join("pipeline_state.json");
    std::fs::write(&path, state).map_err(|e| format!("{}", e))?;
    Ok(())
}

#[tauri::command]
fn load_pipeline_state(ticker: String) -> Result<Option<String>, String> {
    let root = get_project_root();
    let path = PathBuf::from(&root)
        .join("data")
        .join("processed")
        .join(ticker.to_lowercase())
        .join("pipeline_state.json");
    if path.exists() {
        let content = std::fs::read_to_string(&path).map_err(|e| format!("{}", e))?;
        Ok(Some(content))
    } else {
        Ok(None)
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
    let dir = PathBuf::from(&root)
        .join("data")
        .join("processed")
        .join(ticker.to_lowercase());

    // Map pipeline steps to their expected output file prefixes
    let step_files: Vec<(usize, &str, Vec<&str>)> = vec![
        (0, "Map the Industry", vec!["peer_vd_a0_", "peer_vd_a1_", "peer_vd_b0_"]),
        (1, "Gather Data", vec!["peer_vd_a2_", "peer_vd_b1_", "peer_vd_b2_"]),
        (2, "Find What Drives Value", vec!["peer_vd_a3_", "peer_vd_a4", "peer_vd_a5_", "peer_vd_c1_"]),
        (3, "Deep-Dive Peers", vec!["peer_vd_d1_", "peer_vd_d2_"]),
        (4, "Build the Playbook", vec!["peer_vd_p1_", "peer_vd_p2_", "peer_vd_p3_", "peer_vd_final_report"]),
        (5, "Review Analysis", vec!["peer_vd_review_"]),
    ];

    let existing_files: Vec<String> = std::fs::read_dir(&dir)
        .map(|entries| {
            entries
                .flatten()
                .filter_map(|e| {
                    let name = e.file_name().to_string_lossy().to_string();
                    if name.starts_with("peer_vd_") { Some(name) } else { None }
                })
                .collect()
        })
        .unwrap_or_default();

    step_files
        .into_iter()
        .map(|(index, name, prefixes)| {
            let files_found: Vec<String> = existing_files
                .iter()
                .filter(|f| prefixes.iter().any(|p| f.starts_with(p)))
                .cloned()
                .collect();
            let complete = prefixes.iter().all(|p| existing_files.iter().any(|f| f.starts_with(p)));
            StepCompletionInfo {
                step_index: index,
                step_name: name.to_string(),
                files_found,
                complete,
            }
        })
        .collect()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
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
            list_outputs,
            read_output_file,
            start_file_watcher,
            save_pipeline_state,
            load_pipeline_state,
            ensure_source_dirs,
            open_in_browser,
            read_html_summary,
            detect_existing_session,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
