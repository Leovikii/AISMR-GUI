<script setup lang="ts">
// 主题配置
export const THEME = {
  bg: 'bg-[#121214]',
  panel: 'bg-[#18181b]',
  sakura: '#E16B8C',
  sakuraLight: '#F596AA',
}

// 处理状态类型
export type ProcessStatus = 'pending' | 'preparing' | 'normalizing' | 'analyzing' | 'whispering' | 'correcting' | 'translating' | 'exporting' | 'done' | 'error'
</script>

<template>
  <div></div>
</template>
