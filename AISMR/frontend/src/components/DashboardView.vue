<script setup lang="ts">
import { ref } from 'vue'
import Icon from './Icon.vue'
import Button from './Button.vue'
import StatusBadge from './StatusBadge.vue'
import type { ProcessStatus } from './StatusBadge.vue'

interface FileItem {
  id: string
  path: string
  relativePath: string
  name: string
  type: string
  status: ProcessStatus
}

defineProps<{
  files: FileItem[]
  isRunning: boolean
  importMenuRef: any
  showImportMenu: boolean
  setShowImportMenu: (value: boolean) => void
  handleImportFile: () => void
  handleImportFolder: () => void
  runQueue: () => void
  stopQueue: () => void
  removeFile: (e: MouseEvent, id: string) => void
  clearList: () => void
  logs: string[]
  setLogs: (logs: string[]) => void
  logEndRef: any
}>()
</script>

<template>
  <div class="flex-1 flex flex-col overflow-hidden animate-slide-up">
    <div class="h-24 flex items-center px-8 gap-6 bg-[#141417]/60 backdrop-blur-sm relative z-20 shrink-0">
      <div class="relative" ref="importMenuRef">
        <Button 
          :onClick="() => setShowImportMenu(!showImportMenu)"
          label="IMPORT MEDIA"
        >
          <template #icon><Icon name="Import" /></template>
        </Button>
        <div v-if="showImportMenu" class="absolute top-full left-0 mt-3 w-56 bg-[#1e1e24] border border-[#E16B8C]/20 rounded-xl shadow-2xl overflow-hidden z-50 animate-scale-in origin-top-left p-1.5">
          <button @click="handleImportFile" class="w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-[#E16B8C]/10 hover:text-[#F596AA] rounded-lg transition-colors flex items-center gap-3 mb-1">
            <span>📄</span> Import File
          </button>
          <button @click="handleImportFolder" class="w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-[#E16B8C]/10 hover:text-[#F596AA] rounded-lg transition-colors flex items-center gap-3">
            <span>📂</span> Import Folder
          </button>
        </div>
      </div>
      
      <div class="h-8 w-px bg-white/5"></div>
      
      <div class="flex-1 flex flex-col justify-center">
        <div class="text-[10px] text-gray-500 font-bold tracking-widest mb-1">QUEUE STATUS</div>
        <div class="text-gray-300 text-sm flex items-center gap-2">
          <span :class="isRunning ? 'text-[#E16B8C]' : 'text-gray-500'">●</span>
          {{ isRunning ? "PROCESSING ACTIVE" : "READY TO START" }}
        </div>
      </div>

      <Button
        :primary="true"
        :onClick="isRunning ? stopQueue : runQueue"
        :disabled="!isRunning && files.length === 0"
        :label="isRunning ? 'STOP' : 'START QUEUE'"
        className="px-8 py-3 text-base"
      >
        <template #icon><Icon :name="isRunning ? 'Clear' : 'Play'" /></template>
      </Button>
    </div>

    <div class="flex-1 overflow-hidden p-8 pt-2 flex flex-col gap-6">
      <div class="flex-1 bg-[#0c0c0e] rounded-2xl border border-gray-800/60 overflow-hidden flex flex-col shadow-inner relative transition-colors duration-500 hover:border-gray-700/50">
        <div class="h-12 border-b border-gray-800/60 flex items-center justify-between px-6 bg-[#141417] select-none">
          <div class="text-[10px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
            <span class="text-[#E16B8C]/50">●</span> FILE QUEUE ({{ files.length }})
          </div>
          <button v-if="files.length > 0 && !isRunning" @click="clearList" class="flex items-center gap-1.5 text-[10px] text-gray-500 hover:text-[#F596AA] px-3 py-1.5 rounded-lg hover:bg-[#E16B8C]/10 transition-colors">
            <Icon name="Clear" /> <span>CLEAR ALL</span>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
          <div v-if="files.length === 0" class="h-full flex flex-col items-center justify-center opacity-30 select-none pointer-events-none">
            <div class="w-24 h-24 text-gray-600 mb-6 scale-125 opacity-20"><Icon name="Import" /></div>
            <p class="text-sm font-mono tracking-[0.2em] text-gray-500">DROP FILES HERE</p>
          </div>
          <div v-else v-for="file in files" :key="file.id" :class="[
            'relative group flex items-center gap-5 px-5 py-4 rounded-xl border transition-all duration-300',
            file.status === 'done' ? 'opacity-40 grayscale bg-transparent border-transparent' : 'bg-[#18181b] border-[#E16B8C]/10 hover:border-[#E16B8C]/40 shadow-sm'
          ]">
            <div class="p-3 rounded-xl bg-[#E16B8C]/10 text-[#F596AA]">
              <Icon :name="file.type === 'video' ? 'Video' : 'Audio'" />
            </div>
            <div class="flex-1 min-w-0 flex flex-col justify-center">
              <div :class="['font-medium text-sm truncate', file.status === 'done' ? 'text-gray-500' : 'text-gray-200']">{{ file.name }}</div>
              <div class="text-[10px] text-gray-600 font-mono truncate opacity-60 mt-1">{{ file.relativePath }}</div>
            </div>
            <StatusBadge :status="file.status" />
            <button v-if="!isRunning" @click="(e) => removeFile(e, file.id)" class="absolute right-4 p-2 rounded-lg bg-[#18181b] text-gray-500 hover:text-red-400 hover:bg-red-500/10 border border-gray-700 hover:border-red-500/30 opacity-0 group-hover:opacity-100 shadow-xl translate-x-4 group-hover:translate-x-0 transition-all duration-300">
              <Icon name="Trash" />
            </button>
          </div>
        </div>
      </div>

      <div class="h-40 bg-[#0c0c0e] rounded-2xl border border-gray-800/60 overflow-hidden flex flex-col shadow-inner relative transition-colors duration-500 hover:border-gray-700/50 shrink-0">
        <div class="h-10 border-b border-gray-800/60 flex items-center justify-between px-6 bg-[#141417] select-none">
          <div class="text-[10px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-2">
            <div :class="['w-1.5 h-1.5 rounded-full', isRunning ? 'bg-[#E16B8C] animate-pulse' : 'bg-gray-700']"></div>
            SYSTEM OUTPUT
          </div>
          <button @click="setLogs([])" class="text-[10px] text-gray-600 hover:text-gray-400 px-2 py-1 rounded hover:bg-white/5 transition-colors">
            CLEAR LOGS
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-1 text-gray-500 custom-scrollbar font-mono text-[11px]">
          <div v-for="(log, i) in logs" :key="i" class="wrap-break-word border-l-2 border-transparent pl-2 hover:bg-white/5 opacity-80 hover:opacity-100 hover:border-gray-800 transition-colors">
            {{ log }}
          </div>
          <div ref="logEndRef" />
        </div>
      </div>
    </div>
  </div>
</template>
