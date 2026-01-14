package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	stdruntime "runtime"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

type App struct {
	ctx        context.Context
	isRunning  bool
	mu         sync.Mutex
	config     AppConfig
	configPath string
}

type AppConfig struct {
	CacheStrategy string `json:"cacheStrategy"`
}

type FileItem struct {
	ID           string `json:"id"`
	Path         string `json:"path"`
	RelativePath string `json:"relativePath"`
	Name         string `json:"name"`
	Type         string `json:"type"`
}

func NewApp() *App {
	return &App{
		config: AppConfig{CacheStrategy: "off"},
	}
}

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	cwd, _ := os.Getwd()
	a.configPath = filepath.Join(cwd, "config.json")
	a.loadConfig()
	a.performTimeBasedCleanup()
}

func (a *App) loadConfig() {
	data, err := os.ReadFile(a.configPath)
	if err == nil {
		json.Unmarshal(data, &a.config)
	}
}

func (a *App) saveConfig() {
	data, _ := json.MarshalIndent(a.config, "", "  ")
	os.WriteFile(a.configPath, data, 0644)
}

func (a *App) GetSettings() AppConfig {
	return a.config
}

func (a *App) SetSettings(cfg AppConfig) {
	a.config = cfg
	a.saveConfig()
}

func (a *App) GetCacheInfo() map[string]interface{} {
	cwd, _ := os.Getwd()
	cacheDir := filepath.Join(cwd, "core", "cache")

	var size int64 = 0
	exists := false

	if info, err := os.Stat(cacheDir); err == nil && info.IsDir() {
		exists = true
		filepath.Walk(cacheDir, func(_ string, info os.FileInfo, err error) error {
			if !info.IsDir() {
				size += info.Size()
			}
			return nil
		})
	}

	return map[string]interface{}{
		"path":   cacheDir,
		"size":   size,
		"exists": exists,
	}
}

func (a *App) ClearCache() string {
	cwd, _ := os.Getwd()
	cacheDir := filepath.Join(cwd, "core", "cache")
	err := os.RemoveAll(cacheDir)
	if err != nil {
		return "Error: " + err.Error()
	}
	os.MkdirAll(cacheDir, 0755)
	return "Success"
}

func (a *App) performTimeBasedCleanup() {
	if a.config.CacheStrategy != "3days" && a.config.CacheStrategy != "7days" {
		return
	}

	days := 3
	if a.config.CacheStrategy == "7days" {
		days = 7
	}
	threshold := time.Now().AddDate(0, 0, -days)

	cwd, _ := os.Getwd()
	cacheDir := filepath.Join(cwd, "core", "cache")

	entries, _ := os.ReadDir(cacheDir)
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		info, err := entry.Info()
		if err == nil && info.ModTime().Before(threshold) {
			os.RemoveAll(filepath.Join(cacheDir, entry.Name()))
			a.log("Auto-cleaned old cache: " + entry.Name())
		}
	}
}

func (a *App) ScanModels() []string {
	cwd, _ := os.Getwd()
	coreDir := filepath.Join(cwd, "core")
	pythonExe := filepath.Join(coreDir, "python", "python.exe")
	utilsPath := filepath.Join(coreDir, "scripts", "utils.py")

	cmd := exec.Command(pythonExe, utilsPath, "--scan")
	cmd.Dir = filepath.Join(coreDir, "scripts")
	if stdruntime.GOOS == "windows" {
		cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000}
	}

	output, err := cmd.Output()
	if err != nil {
		return []string{}
	}

	var missing []string
	json.Unmarshal(output, &missing)
	return missing
}

func (a *App) DownloadModels() error {
	cwd, _ := os.Getwd()
	coreDir := filepath.Join(cwd, "core")
	pythonExe := filepath.Join(coreDir, "python", "python.exe")
	utilsPath := filepath.Join(coreDir, "scripts", "utils.py")

	cmd := exec.Command(pythonExe, utilsPath, "--download")
	cmd.Dir = filepath.Join(coreDir, "scripts")
	if stdruntime.GOOS == "windows" {
		cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000}
	}

	stdout, _ := cmd.StdoutPipe()
	if err := cmd.Start(); err != nil {
		return err
	}

	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "PROGRESS:") {
			runtime.EventsEmit(a.ctx, "model-download-progress", line)
		} else if strings.HasPrefix(line, "STATUS:") {
			runtime.EventsEmit(a.ctx, "model-download-status", line)
		} else if line == "DONE" {
			runtime.EventsEmit(a.ctx, "model-download-done", true)
		}
	}
	return cmd.Wait()
}

func (a *App) ProcessPaths(paths []string) []FileItem {
	var result []FileItem
	validExts := map[string]string{
		".mp4": "video", ".mkv": "video", ".avi": "video", ".mov": "video",
		".mp3": "audio", ".wav": "audio", ".flac": "audio", ".m4a": "audio", ".aac": "audio",
	}

	for _, p := range paths {
		info, err := os.Stat(p)
		if err != nil {
			continue
		}

		if info.IsDir() {
			filepath.Walk(p, func(path string, fInfo os.FileInfo, err error) error {
				if err != nil || fInfo.IsDir() {
					return nil
				}
				ext := strings.ToLower(filepath.Ext(path))
				if fileType, ok := validExts[ext]; ok {
					rel, _ := filepath.Rel(filepath.Dir(p), path)
					result = append(result, FileItem{
						ID:           path,
						Path:         path,
						RelativePath: rel,
						Name:         fInfo.Name(),
						Type:         fileType,
					})
				}
				return nil
			})
		} else {
			ext := strings.ToLower(filepath.Ext(p))
			if fileType, ok := validExts[ext]; ok {
				result = append(result, FileItem{
					ID:           p,
					Path:         p,
					RelativePath: info.Name(),
					Name:         info.Name(),
					Type:         fileType,
				})
			}
		}
	}
	return result
}

func (a *App) SelectFile() string {
	path, err := runtime.OpenFileDialog(a.ctx, runtime.OpenDialogOptions{
		Title: "选择媒体文件",
		Filters: []runtime.FileFilter{
			{DisplayName: "Media Files", Pattern: "*.mp4;*.mkv;*.avi;*.mov;*.mp3;*.wav;*.flac;*.m4a;*.aac"},
		},
	})
	if err != nil {
		return ""
	}
	return path
}

func (a *App) SelectFolder() string {
	path, err := runtime.OpenDirectoryDialog(a.ctx, runtime.OpenDialogOptions{
		Title: "选择包含媒体的文件夹",
	})
	if err != nil {
		return ""
	}
	return path
}

func (a *App) RunScript(targetPath string) error {
	a.mu.Lock()
	if a.isRunning {
		a.mu.Unlock()
		return fmt.Errorf("任务正在运行中")
	}
	a.isRunning = true
	a.mu.Unlock()

	defer func() {
		a.mu.Lock()
		a.isRunning = false
		a.mu.Unlock()

		if a.config.CacheStrategy == "immediate" {
			go func() {
				cwd, _ := os.Getwd()
				baseName := strings.TrimSuffix(filepath.Base(targetPath), filepath.Ext(targetPath))
				cachePath := filepath.Join(cwd, "core", "cache", baseName)
				if _, err := os.Stat(cachePath); err == nil {
					os.RemoveAll(cachePath)
					a.log("Auto-cleaned cache for: " + baseName)
				}
			}()
		}
	}()

	cwd, _ := os.Getwd()
	coreDir := filepath.Join(cwd, "core")
	pythonExe := filepath.Join(coreDir, "python", "python.exe")
	scriptPath := filepath.Join(coreDir, "scripts", "run.py")

	if _, err := os.Stat(pythonExe); os.IsNotExist(err) {
		a.log("严重错误: 未找到内置 Python 环境: " + pythonExe)
		return err
	}

	a.log("调用引擎: " + pythonExe)

	cmd := exec.Command(pythonExe, scriptPath, targetPath)
	cmd.Dir = filepath.Join(coreDir, "scripts")

	env := os.Environ()
	binPath := filepath.Join(coreDir, "bin")
	ffmpegPath := filepath.Join(binPath, "ffmpeg")
	llamaPath := filepath.Join(binPath, "llama")

	pathKey := "PATH"
	if stdruntime.GOOS == "windows" {
		pathKey = "Path"
	}
	newPath := fmt.Sprintf("%s%c%s%c%s%c%s", ffmpegPath, os.PathListSeparator, llamaPath, os.PathListSeparator, os.Getenv(pathKey), os.PathListSeparator, binPath)
	env = append(env, fmt.Sprintf("%s=%s", pathKey, newPath))
	cmd.Env = env

	if stdruntime.GOOS == "windows" {
		cmd.SysProcAttr = &syscall.SysProcAttr{
			HideWindow:    true,
			CreationFlags: 0x08000000,
		}
	}

	stdout, _ := cmd.StdoutPipe()
	stderr, _ := cmd.StderrPipe()

	if err := cmd.Start(); err != nil {
		a.log("启动失败: " + err.Error())
		return err
	}

	scannerOut := bufio.NewScanner(stdout)
	scannerErr := bufio.NewScanner(stderr)

	var wg sync.WaitGroup
	wg.Add(2)

	go func() {
		defer wg.Done()
		for scannerOut.Scan() {
			a.log(scannerOut.Text())
		}
	}()

	go func() {
		defer wg.Done()
		for scannerErr.Scan() {
			a.log("ERR: " + scannerErr.Text())
		}
	}()

	wg.Wait()

	if err := cmd.Wait(); err != nil {
		return err
	}

	return nil
}

func (a *App) log(message string) {
	fmt.Println(message)
	runtime.EventsEmit(a.ctx, "log-message", message)
}
