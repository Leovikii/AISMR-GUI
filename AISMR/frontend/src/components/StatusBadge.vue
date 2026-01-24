<script setup lang="ts">
export type ProcessStatus = 'pending' | 'preparing' | 'normalizing' | 'analyzing' | 'whispering' | 'correcting' | 'translating' | 'exporting' | 'done' | 'error'

defineProps<{
  status: ProcessStatus
}>()

const colors: Record<ProcessStatus, string> = {
  'pending': 'text-gray-400 border-gray-800 bg-gray-800/40',
  'preparing': 'text-[#F596AA] border-[#E16B8C]/30 bg-[#E16B8C]/10 shadow-[0_0_10px_rgba(225,107,140,0.2)]',
  'normalizing': 'text-[#F596AA] border-[#E16B8C]/30 bg-[#E16B8C]/10 shadow-[0_0_10px_rgba(225,107,140,0.2)]',
  'analyzing': 'text-[#F596AA] border-[#E16B8C]/30 bg-[#E16B8C]/10 shadow-[0_0_10px_rgba(225,107,140,0.2)]',
  'whispering': 'text-blue-200 border-blue-500/30 bg-blue-500/10 shadow-[0_0_10px_rgba(59,130,246,0.1)]',
  'correcting': 'text-purple-200 border-purple-500/30 bg-purple-500/10 shadow-[0_0_10px_rgba(168,85,247,0.1)]',
  'translating': 'text-indigo-200 border-indigo-500/30 bg-indigo-500/10 shadow-[0_0_10px_rgba(99,102,241,0.1)]',
  'exporting': 'text-cyan-200 border-cyan-500/30 bg-cyan-500/10 shadow-[0_0_10px_rgba(6,182,212,0.1)]',
  'done': 'text-emerald-300 border-emerald-500/20 bg-emerald-500/5',
  'error': 'text-red-400 border-red-500/30 bg-red-500/10',
}

const statusText: Record<ProcessStatus, string> = {
  'pending': 'WAITING', 'preparing': 'PREPARE', 'normalizing': 'NORMALIZING', 'analyzing': 'ANALYZING', 'whispering': 'WHISPER',
  'correcting': 'CORRECT', 'translating': 'TRANSLATE', 'exporting': 'EXPORT',
  'done': 'FINISHED', 'error': 'ERROR'
}
</script>

<template>
  <div :class="['px-2 py-1 rounded text-[10px] font-bold tracking-wider border transition-all duration-500', colors[status]]">
    {{ statusText[status] }}
  </div>
</template>
