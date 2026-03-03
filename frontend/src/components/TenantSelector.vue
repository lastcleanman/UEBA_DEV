<script setup>
const props = defineProps({
  value: { type: String, required: true },
  tenants: { type: Array, default: () => [] },
})
const emit = defineEmits(['change'])

function onChange(e) {
  emit('change', e.target.value)
}
</script>

<template>
  <label style="display:flex; gap:10px; align-items:center;">
    <span style="font-weight:600;">Tenant</span>
    <select :value="value" @change="onChange"
            style="padding:6px 10px; border-radius:10px; border:1px solid #e5e7eb;">
      <option v-for="t in tenants" :key="t" :value="t">{{ t }}</option>
    </select>
  </label>
</template>