<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { SelectFile, SelectFolder, RunScript, StopScript, ProcessPaths, GetCacheInfo, ClearCache, GetSettings, SetSettings, ScanModels, DownloadModels } from "../wailsjs/go/main/App"
import { WindowMinimise, Quit, EventsOn, EventsOff, OnFileDrop } from "../wailsjs/runtime/runtime"
import Icon from './components/Icon.vue'
import Button from './components/Button.vue'
import ModelInitModal from './components/ModelInitModal.vue'
import SettingsView from './components/SettingsView.vue'
import DashboardView from './components/DashboardView.vue'
import type { ProcessStatus } from './components/StatusBadge.vue'

interface FileItem {
  id: string
  path: string
  relativePath: string
  name: string
  type: string
  status: ProcessStatus
}

const THEME = {
  bg: 'bg-[#121214]',
  panel: 'bg-[#18181b]',
  sakura: '#E16B8C',
  sakuraLight: '#F596AA',
}

const files = ref<FileItem[]>([])
const logs = ref<string[]>([])
const isRunning = ref(false)
const currentIndex = ref<number | null>(null)
const showImportMenu = ref(false)
const isDragging = ref(false)

const currentView = ref<'dashboard' | 'settings'>('dashboard')
const cacheSize = ref<number>(0)
const cacheStrategy = ref<string>("off")

const initStep = ref<'idle' | 'check' | 'prompt' | 'downloading'>('idle')
const missingModels = ref<string[]>([])
const downloadProgress = ref(0)
const downloadStatus = ref("")

const logEndRef = ref<HTMLDivElement | null>(null)
const currentIndexRef = ref<number | null>(null)
const importMenuRef = ref<HTMLDivElement | null>(null)
const filesRef = ref(files.value)

// Watchers
watch(currentIndex, (val) => { currentIndexRef.value = val })
watch(files, (val) => { filesRef.value = val }, { deep: true })

// Click outside handler
const handleClickOutside = (event: MouseEvent) => {
  if (importMenuRef.value && !importMenuRef.value.contains(event.target as Node)) {
    showImportMenu.value = false
  }
}

// Drag handlers
const handleDragEnter = () => { isDragging.value = true }
const handleDragLeave = (e: MouseEvent) => {
  if (e.clientX <= 0 || e.clientY <= 0 || e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) {
    isDragging.value = false
  }
}

// Update status
const updateStatus = (index: number, status: ProcessStatus) => {
  if (files.value[index]) {
    files.value[index].status = status
  }
}

// Add log
const addLog = (msg: string) => {
  logs.value.push(msg)
}

// Scroll logs
watch(logs, async () => {
  await nextTick()
  logEndRef.value?.scrollIntoView({ behavior: "smooth" })
}, { deep: true })

// Event handlers
const refreshCacheInfo = async () => {
  const info = await GetCacheInfo()
  cacheSize.value = Number(info.size) / (1024 * 1024 * 1024)
}

const handleStrategyChange = (val: string) => {
  cacheStrategy.value = val
  SetSettings({ cacheStrategy: val })
}

const handleClearCache = async () => {
  await ClearCache()
  refreshCacheInfo()
  addLog("[System] Cache cleared manually.")
}

const performModelCheck = async () => {
  initStep.value = 'check'
  const missing = await ScanModels()
  if (missing && missing.length > 0) {
    missingModels.value = missing
    initStep.value = 'prompt'
  } else {
    initStep.value = 'idle'
  }
}

const handleStartDownload = async () => {
  initStep.value = 'downloading'
  await DownloadModels()
}

const handleManualCheck = async () => {
  performModelCheck()
}

const handleNewPaths = async (paths: string[]) => {
  if (!paths || paths.length === 0) return
  if (currentView.value === 'settings') currentView.value = 'dashboard'
  
  const processedItems = await ProcessPaths(paths)
  if (!processedItems || processedItems.length === 0) {
    addLog("[System] No valid media files found.")
    return
  }
  
  const newItems = processedItems.filter((item: any) => 
    !files.value.some(f => f.path === item.path)
  ).map((item: any) => ({ ...item, status: 'pending' as ProcessStatus }))
  
  if (newItems.length > 0) {
    files.value.push(...newItems)
    addLog(`[System] Added ${newItems.length} files.`)
  }
  showImportMenu.value = false
}

const handleImportFile = async () => {
  const path = await SelectFile()
  if (path) handleNewPaths([path])
}

const handleImportFolder = async () => {
  const dir = await SelectFolder()
  if (dir) handleNewPaths([dir])
}

const removeFile = (e: MouseEvent, id: string) => {
  e.stopPropagation()
  if (isRunning.value) return
  files.value = files.value.filter(f => f.id !== id)
}

const clearList = () => {
  if (isRunning.value) return
  files.value = []
  addLog("[System] List cleared.")
}

const runQueue = async () => {
  if (isRunning.value) return
  isRunning.value = true
  for (let i = 0; i < files.value.length; i++) {
    if (files.value[i].status === 'done') continue
    currentIndex.value = i
    updateStatus(i, 'preparing')
    addLog(`=== Processing [${i+1}/${files.value.length}]: ${files.value[i].name} ===`)
    try {
      await RunScript(files.value[i].path)
      updateStatus(i, 'done')
    } catch (e: any) {
      if (e && e.toString().includes("stopped")) {
        addLog("=== Queue Stopped by User ===")
        break
      }
      updateStatus(i, 'error')
      addLog(`=== Error: ${e} ===`)
    }
  }
  currentIndex.value = null
  isRunning.value = false
  refreshCacheInfo()
  addLog("=== Queue Finished ===")
}

const stopQueue = async () => {
  if (!isRunning.value) return
  try {
    await StopScript()
  } catch (e: any) {
    addLog(`=== Stop Error: ${e} ===`)
  }
}

// Lifecycle hooks
onMounted(() => {
  document.addEventListener("mousedown", handleClickOutside)
  window.addEventListener('dragenter', handleDragEnter)
  window.addEventListener('dragleave', handleDragLeave)
  
  OnFileDrop((x, y, paths) => {
    isDragging.value = false
    handleNewPaths(paths)
  }, false)
  
  const logHandler = (msg: string) => {
    logs.value.push(msg)
    const idx = currentIndexRef.value
    if (idx === null) return
    
    if (msg.includes("STATUS: Audio Normalization")) updateStatus(idx, 'normalizing')
    else if (msg.includes("STATUS: Context Analysis") || msg.includes("STATUS: Extracting Terms")) updateStatus(idx, 'analyzing')
    else if (msg.includes("RUNNING: _0_prepare.py")) updateStatus(idx, 'preparing')
    else if (msg.includes("RUNNING: _1_whisper.py") || msg.includes("STATUS: Loading Whisper Model") || msg.includes("STATUS: Transcribing Audio")) updateStatus(idx, 'whispering')
    else if (msg.includes("RUNNING: _2_correct.py") || msg.includes("STATUS: Loading Correction Data") || msg.includes("STATUS: Correcting Text")) updateStatus(idx, 'correcting')
    else if (msg.includes("RUNNING: _3_translate.py") || msg.includes("STATUS: Loading Translation Data") || msg.includes("STATUS: Translating Text")) updateStatus(idx, 'translating')
    else if (msg.includes("RUNNING: _4_output.py") || msg.includes("STATUS: Generating Final Output")) updateStatus(idx, 'exporting')
  }
  
  const dlProgress = (msg: string) => {
    const p = parseInt(msg.replace("PROGRESS: ", ""))
    if (!isNaN(p)) downloadProgress.value = p
  }
  const dlStatus = (msg: string) => {
    downloadStatus.value = msg.replace("STATUS: ", "")
  }
  const dlDone = () => {
    initStep.value = 'idle'
  }
  
  EventsOn("log-message", logHandler)
  EventsOn("model-download-progress", dlProgress)
  EventsOn("model-download-status", dlStatus)
  EventsOn("model-download-done", dlDone)
  
  refreshCacheInfo()
  GetSettings().then(cfg => {
    if(cfg && cfg.cacheStrategy) cacheStrategy.value = cfg.cacheStrategy
  })
  performModelCheck()
})

onUnmounted(() => {
  document.removeEventListener("mousedown", handleClickOutside)
  window.removeEventListener('dragenter', handleDragEnter)
  window.removeEventListener('dragleave', handleDragLeave)
  EventsOff("log-message")
  EventsOff("model-download-progress")
  EventsOff("model-download-status")
  EventsOff("model-download-done")
})
</script>

<template>
  <div :class="['h-screen flex flex-col', THEME.bg, 'text-gray-200 font-sans overflow-hidden border border-gray-800/50 relative']">
    
    <ModelInitModal 
      :step="initStep"
      :missing="missingModels"
      :progress="downloadProgress"
      :status="downloadStatus"
      :onDownload="handleStartDownload"
      :onManualCheck="handleManualCheck"
    />

    <div v-if="isDragging" class="absolute inset-0 z-50 bg-[#121214]/90 backdrop-blur-md flex flex-col items-center justify-center border-4 border-[#E16B8C]/30 border-dashed rounded-lg animate-fade-in pointer-events-none">
      <div class="p-6 rounded-full bg-[#E16B8C]/10 mb-4 animate-bounce shadow-[0_0_30px_rgba(225,107,140,0.3)]">
        <Icon name="Import" />
      </div>
      <h2 class="text-2xl font-bold text-[#F596AA] tracking-widest drop-shadow-md">RELEASE TO IMPORT</h2>
    </div>

    <div class="h-10 flex items-center justify-between bg-[#18181b] select-none border-b border-white/5 shrink-0" style="width: 100%; --wails-draggable: drag">
      <div class="flex items-center gap-3 px-4 w-full h-full">
        <div class="w-3 h-3 rounded-full bg-[#E16B8C] shadow-[0_0_10px_rgba(225,107,140,0.6)]"></div>
        <span class="text-xs font-bold tracking-[0.2em] text-gray-400">AISMR STUDIO</span>
      </div>
      <div class="flex h-full no-drag items-center" style="--wails-draggable: no-drag">
        <button v-if="currentView === 'dashboard'" @click="() => { refreshCacheInfo(); currentView = 'settings'; }" class="w-10 h-full flex items-center justify-center hover:bg-white/5 text-gray-500 hover:text-[#E16B8C] transition-colors">
          <Icon name="Settings" />
        </button>
        <button v-else @click="currentView = 'dashboard'" class="w-10 h-full flex items-center justify-center hover:bg-white/5 text-[#E16B8C] bg-[#E16B8C]/5 transition-colors">
          <Icon name="Back" />
        </button>
        <div class="w-px h-3 bg-white/10 mx-1"></div>
        <button @click="WindowMinimise" class="w-12 h-full flex items-center justify-center hover:bg-white/5 text-gray-500 hover:text-gray-200">
          <Icon name="Min" />
        </button>
        <button @click="Quit" class="w-12 h-full flex items-center justify-center hover:bg-[#E16B8C]/80 hover:text-white text-gray-500">
          <Icon name="Close" />
        </button>
      </div>
    </div>

    <SettingsView v-if="currentView === 'settings'"
      :onBack="() => currentView = 'dashboard'"
      :cacheSize="cacheSize"
      :cacheStrategy="cacheStrategy"
      :onStrategyChange="handleStrategyChange"
      :onClearCache="handleClearCache"
    />
    
    <DashboardView v-else
      :files="files"
      :isRunning="isRunning"
      :importMenuRef="importMenuRef"
      :showImportMenu="showImportMenu"
      :setShowImportMenu="(val: boolean) => showImportMenu = val"
      :handleImportFile="handleImportFile"
      :handleImportFolder="handleImportFolder"
      :runQueue="runQueue"
      :stopQueue="stopQueue"
      :removeFile="removeFile"
      :clearList="clearList"
      :logs="logs"
      :setLogs="(val: string[]) => logs = val"
      :logEndRef="logEndRef"
    />
  </div>
</template>

<style>
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #27272a; border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #3f3f46; }
</style>
