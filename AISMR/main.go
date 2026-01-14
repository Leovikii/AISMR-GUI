package main

import (
	"embed"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
	"github.com/wailsapp/wails/v2/pkg/options/windows"
)

//go:embed all:frontend/dist
var assets embed.FS

func main() {
	// Create an instance of the app structure
	app := NewApp()

	// Create application with options
	err := wails.Run(&options.App{
		Title:  "AISMR",
		Width:  1024,
		Height: 768,
		// 保持无边框
		Frameless: true,

		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		BackgroundColour: &options.RGBA{R: 27, G: 38, B: 54, A: 0},

		// 【关键修改】配置拖放行为
		DragAndDrop: &options.DragAndDrop{
			EnableFileDrop:     true,                  // 启用 Wails 的文件拖放事件
			DisableWebViewDrop: true,                  // 禁用 WebView 默认的“打开文件”行为
			CSSDropProperty:    "--wails-drop-target", // 可选：用于 CSS 样式的标记
			CSSDropValue:       "drop",
		},

		OnStartup: app.startup,
		Bind: []interface{}{
			app,
		},
		Windows: &windows.Options{
			WebviewIsTransparent: true,
			WindowIsTranslucent:  true,
			BackdropType:         windows.Mica,
			Theme:                windows.Dark,
			DisableWindowIcon:    true,
		},
	})

	if err != nil {
		println("Error:", err.Error())
	}
}
