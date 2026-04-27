<script setup>
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  LineElement, PointElement, LinearScale, TimeScale,
  Filler, Tooltip as ChartTooltip,
} from 'chart.js'
import 'chartjs-adapter-date-fns'

ChartJS.register(LineElement, PointElement, LinearScale, TimeScale, Filler, ChartTooltip)

const props = defineProps({
  history:  { type: Array, default: () => [] },  // newest first
  field:    { type: String, required: true },     // 'cpu_percent' | 'ram_pct' | 'disk_pct'
  color:    { type: String, default: '#10b981' },
  maxY:     { type: Number, default: 100 },
})

const points = computed(() => {
  return [...props.history]
    .reverse()
    .map(m => {
      let y
      if (props.field === 'cpu_percent')  y = m.cpu_percent ?? 0
      else if (props.field === 'ram_pct') y = m.ram_total_mb ? Math.round((m.ram_used_mb / m.ram_total_mb) * 100) : 0
      else if (props.field === 'disk_pct') y = m.disk_total_gb ? Math.round((m.disk_used_gb / m.disk_total_gb) * 100) : 0
      return { x: new Date(m.collected_at), y }
    })
})

const chartData = computed(() => ({
  datasets: [{
    data: points.value,
    borderColor: props.color,
    backgroundColor: props.color + '18',
    borderWidth: 1.5,
    pointRadius: 0,
    fill: true,
    tension: 0.3,
  }],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1c1917',
      borderColor: 'rgba(255,255,255,0.08)',
      borderWidth: 1,
      titleColor: '#a8a29e',
      bodyColor: '#e7e5e4',
      titleFont: { size: 11 },
      bodyFont: { size: 12, family: 'monospace' },
      padding: 8,
      callbacks: {
        title: items => {
          const d = new Date(items[0].parsed.x)
          return d.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
        },
        label: item => ` ${item.parsed.y.toFixed(1)}%`,
      },
    },
  },
  scales: {
    x: {
      type: 'time',
      time: { unit: 'hour', displayFormats: { hour: 'HH:mm' } },
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: 'rgba(255,255,255,0.3)', maxTicksLimit: 6, font: { size: 10 } },
      border: { display: false },
    },
    y: {
      min: 0,
      max: props.maxY,
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: 'rgba(255,255,255,0.3)', maxTicksLimit: 4, font: { size: 10 }, callback: v => v + '%' },
      border: { display: false },
    },
  },
}
</script>

<template>
  <div class="h-full w-full">
    <Line v-if="points.length > 1" :data="chartData" :options="chartOptions" />
    <div v-else class="h-full flex items-center justify-center">
      <p class="text-xs text-fg-subtle/40">Нет данных</p>
    </div>
  </div>
</template>
