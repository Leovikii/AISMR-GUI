<script setup lang="ts">
defineProps<{
  onClick?: () => void
  disabled?: boolean
  primary?: boolean
  label: string
  className?: string
}>()
</script>

<template>
  <button 
    @click="onClick"
    :disabled="disabled"
    :class="[
      'px-6 py-2.5 rounded-lg flex items-center gap-2 font-bold tracking-wide text-sm select-none transition-all duration-300 ease-out active:scale-95 justify-center',
      disabled 
        ? 'bg-[#1e1e24] text-gray-600 border border-gray-800 cursor-not-allowed' 
        : primary 
          ? 'bg-[#E16B8C] text-white hover:bg-[#d0597a] shadow-[0_0_20px_rgba(225,107,140,0.4)] hover:shadow-[0_0_25px_rgba(225,107,140,0.6)]' 
          : 'bg-[#1e1e24] hover:bg-[#272730] text-[#F596AA] border border-[#E16B8C]/20 hover:border-[#E16B8C]/40 shadow-[0_0_0_1px_rgba(225,107,140,0.05)] hover:shadow-[0_0_15px_rgba(225,107,140,0.2)]',
      className
    ]"
  >
    <slot name="icon"></slot>
    <span>{{ label }}</span>
  </button>
</template>
