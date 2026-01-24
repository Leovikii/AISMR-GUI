<script setup lang="ts">
import Icon from './Icon.vue'
import Button from './Button.vue'
import CustomSelect from './CustomSelect.vue'
import ProgressBar from './ProgressBar.vue'

defineProps<{
  onBack: () => void
  cacheSize: number
  cacheStrategy: string
  onStrategyChange: (value: string) => void
  onClearCache: () => void
}>()
</script>

<template>
  <div class="flex-1 p-10 flex flex-col gap-8 animate-slide-up w-full">
    <div class="flex items-center gap-4 border-b border-white/5 pb-6">
      <div class="p-3 bg-[#E16B8C]/10 rounded-xl text-[#E16B8C]">
        <Icon name="Settings" />
      </div>
      <div>
        <h2 class="text-2xl font-bold text-white tracking-wide">SETTINGS</h2>
        <p class="text-gray-500 text-sm mt-1">Configure application preferences and storage.</p>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-8 w-full max-w-none">
      <div class="bg-[#18181b] border border-[#E16B8C]/10 rounded-2xl p-6 space-y-6 hover:border-[#E16B8C]/30 transition-colors duration-300 w-full">
        <div class="flex items-center gap-3 mb-2">
          <Icon name="Cache" />
          <h3 class="text-sm font-bold text-[#E16B8C] tracking-widest">STORAGE & CACHE</h3>
        </div>
        
        <ProgressBar :value="cacheSize" :max="10" label="Current Cache Usage" />
        
        <div class="flex items-end justify-between gap-6">
          <div class="flex-1">
            <CustomSelect 
              label="AUTO-CLEANUP STRATEGY"
              :value="cacheStrategy"
              :onChange="onStrategyChange"
              :options="[
                { value: 'off', label: 'Manual Only (Default)' },
                { value: 'immediate', label: 'Clean After Completion' },
                { value: '3days', label: 'Keep for 3 Days' },
                { value: '7days', label: 'Keep for 7 Days' },
              ]"
            />
          </div>
          <Button 
            :onClick="onClearCache"
            label="CLEAR NOW"
            className="bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20 hover:border-red-500/40 hover:text-red-300 h-11.5"
          >
            <template #icon><Icon name="Clear" /></template>
          </Button>
        </div>
        <p class="text-[10px] text-gray-600 font-mono pt-2 border-t border-white/5">
          Cache Path: ./core/cache
        </p>
      </div>
    </div>
  </div>
</template>
