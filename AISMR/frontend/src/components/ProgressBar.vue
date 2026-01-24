<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  value: number
  max: number
  label: string
}>()

const percent = computed(() => {
  return Math.min(100, Math.max(0, (props.value / props.max) * 100))
})
</script>

<template>
  <div class="w-full">
    <div class="flex justify-between text-[10px] uppercase tracking-wider font-bold mb-2">
      <span class="text-gray-500">{{ label }}</span>
      <span class="text-[#F596AA] font-mono">{{ value.toFixed(2) }} GB / {{ max }} GB</span>
    </div>
    <div class="h-2 w-full bg-[#1e1e24] rounded-full overflow-hidden border border-white/5">
      <div 
        class="h-full bg-[#E16B8C] shadow-[0_0_15px_rgba(225,107,140,0.5)] transition-all duration-700 ease-out" 
        :style="{ width: `${percent}%` }"
      />
    </div>
  </div>
</template>
