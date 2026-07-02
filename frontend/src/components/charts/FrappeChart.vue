<template>
  <div ref="el" class="frappe-chart" />
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Chart } from 'frappe-charts'

const props = defineProps({
  // 'bar' | 'line' | 'percentage' | 'pie' | 'donut'
  type: { type: String, default: 'bar' },
  data: { type: Object, required: true },
  height: { type: Number, default: 280 },
  colors: { type: Array, default: () => ['#2490EF', '#34D399', '#F59E0B', '#A78BFA'] },
  options: { type: Object, default: () => ({}) },
})

const el = ref(null)
let chart = null

function render() {
  if (!el.value) return
  el.value.innerHTML = ''
  chart = new Chart(el.value, {
    type: props.type,
    height: props.height,
    colors: props.colors,
    animate: false,
    axisOptions: { xIsSeries: props.type === 'line' },
    barOptions: { spaceRatio: 0.4 },
    data: props.data,
    ...props.options,
  })
  // ponytail: frappe-charts clips pie/donut legends that wrap onto extra rows —
  // grow the svg to fit the rendered content
  nextTick(() => {
    const svg = el.value && el.value.querySelector('svg')
    if (!svg) return
    const needed = Math.ceil(svg.getBBox().y + svg.getBBox().height) + 10
    if (needed > Number(svg.getAttribute('height'))) svg.setAttribute('height', needed)
  })
}

onMounted(render)

// frappe-charts' update() is finicky across types — re-render on data/type changes.
watch(
  () => [props.data, props.type],
  () => render(),
  { deep: true },
)

onBeforeUnmount(() => {
  chart = null
  if (el.value) el.value.innerHTML = ''
})
</script>
