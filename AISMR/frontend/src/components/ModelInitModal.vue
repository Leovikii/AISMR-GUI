<script setup lang="ts">
import Icon from './Icon.vue'
import Button from './Button.vue'

defineProps<{
  step: 'idle' | 'check' | 'prompt' | 'downloading'
  missing: string[]
  progress: number
  status: string
  onDownload: () => void
  onManualCheck: () => void
}>()
</script>

<template>
  <div v-if="step !== 'idle'" class="absolute inset-0 z-100 bg-[#121214]/95 backdrop-blur-xl flex flex-col items-center justify-center animate-fade-in">
    <div class="w-full max-w-lg p-10 flex flex-col items-center gap-8 bg-[#18181b]/50 border border-[#E16B8C]/10 rounded-3xl shadow-2xl">
      
      <!-- Check Step -->
      <template v-if="step === 'check'">
        <div class="p-6 rounded-full bg-[#E16B8C]/10 text-[#E16B8C] animate-pulse">
          <Icon name="Cache" />
        </div>
        <h2 class="text-xl font-bold text-white tracking-widest">CHECKING RESOURCES...</h2>
      </template>

      <!-- Prompt Step -->
      <template v-if="step === 'prompt'">
        <div class="p-6 rounded-full bg-yellow-500/10 text-yellow-500 shadow-[0_0_40px_rgba(234,179,8,0.2)]">
          <Icon name="Missing" />
        </div>
        <div class="text-center space-y-2">
          <h2 class="text-xl font-bold text-white tracking-widest">MISSING MODELS DETECTED</h2>
          <p class="text-gray-400 text-sm">The following AI models are required to run the application:</p>
        </div>
        <div class="w-full bg-[#1e1e24] rounded-xl p-4 border border-white/5">
          <ul class="space-y-2">
            <li v-for="(m, i) in missing" :key="i" class="text-xs text-[#F596AA] font-mono flex items-center gap-2">
              <span class="text-[#E16B8C]">●</span> {{ m }}
            </li>
          </ul>
        </div>
        <div class="flex flex-col gap-3 w-full pt-2">
          <Button 
            :primary="true"
            :onClick="onDownload" 
            label="DOWNLOAD AUTOMATICALLY"
            className="w-full py-4"
          >
            <template #icon><Icon name="Download" /></template>
          </Button>
          <button 
            @click="onManualCheck"
            class="text-xs text-gray-500 hover:text-gray-300 transition-colors py-2"
          >
            I have placed them manually (Re-scan)
          </button>
        </div>
      </template>

      <!-- Downloading Step -->
      <template v-if="step === 'downloading'">
        <div class="p-6 rounded-full bg-[#E16B8C]/10 text-[#E16B8C] animate-bounce shadow-[0_0_40px_rgba(225,107,140,0.3)]">
          <Icon name="Download" />
        </div>
        <div class="text-center space-y-2">
          <h2 class="text-2xl font-bold text-white tracking-widest">INSTALLING</h2>
          <p class="text-[#F596AA] font-mono text-sm">{{ status || "Initializing..." }}</p>
        </div>
        <div class="w-full space-y-2">
          <div class="h-2 w-full bg-[#1e1e24] rounded-full overflow-hidden border border-white/10">
            <div 
              class="h-full bg-[#E16B8C] shadow-[0_0_15px_rgba(225,107,140,0.8)] transition-all duration-300 ease-out" 
              :style="{ width: `${progress}%` }"
            />
          </div>
          <div class="flex justify-end text-[10px] font-mono text-gray-500">
            {{ progress }}% COMPLETE
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
