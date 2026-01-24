<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Icon from './Icon.vue'

interface Option {
  value: string
  label: string
}

const props = defineProps<{
  value: string
  onChange: (value: string) => void
  options: Option[]
  label?: string
}>()

const isOpen = ref(false)
const containerRef = ref<HTMLDivElement | null>(null)

const selectedLabel = computed(() => {
  return props.options.find(o => o.value === props.value)?.label || props.value
})

const handleClickOutside = (event: MouseEvent) => {
  if (containerRef.value && !containerRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})

const selectOption = (value: string) => {
  props.onChange(value)
  isOpen.value = false
}
</script>

<template>
  <div class="flex flex-col gap-2 w-full" ref="containerRef">
    <label v-if="label" class="text-[10px] uppercase tracking-wider text-gray-500 font-bold ml-1">
      {{ label }}
    </label>
    <div class="relative">
      <button
        @click="isOpen = !isOpen"
        :class="[
          'w-full flex items-center justify-between bg-[#1e1e24] border border-[#E16B8C]/20 text-gray-300 text-sm rounded-lg px-4 py-3 hover:border-[#E16B8C]/50 transition-all duration-300',
          isOpen ? 'border-[#E16B8C]/50 shadow-[0_0_10px_rgba(225,107,140,0.1)]' : ''
        ]"
      >
        <span>{{ selectedLabel }}</span>
        <div :class="['text-[#E16B8C] transition-transform duration-300', isOpen ? 'rotate-180' : '']">
          <Icon name="ChevronDown" />
        </div>
      </button>

      <div v-if="isOpen" class="absolute top-full left-0 right-0 mt-2 bg-[#1e1e24] border border-[#E16B8C]/20 rounded-lg shadow-xl overflow-hidden z-50 animate-scale-in origin-top">
        <button
          v-for="opt in options"
          :key="opt.value"
          @click="selectOption(opt.value)"
          :class="[
            'w-full text-left px-4 py-3 text-sm flex items-center justify-between transition-colors',
            value === opt.value ? 'bg-[#E16B8C]/10 text-[#F596AA]' : 'text-gray-300 hover:bg-white/5'
          ]"
        >
          <span>{{ opt.label }}</span>
          <Icon v-if="value === opt.value" name="Check" />
        </button>
      </div>
    </div>
  </div>
</template>
