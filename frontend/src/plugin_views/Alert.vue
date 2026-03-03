<script setup>
import { onMounted, ref } from 'vue'
import api from '../api/client'

const health = ref({ status: 'checking...', message: '' })

onMounted(async () => {
  const res = await api.get('/health')
  health.value = res.data
})
</script>

<template>
  <div>
    <h1 style="margin:0 0 12px;">alert</h1>

    <div style="padding:16px; background:#fff; border-radius:14px; border:1px solid #e5e7eb;">
      <div><b>Backend status:</b> {{ health.status }}</div>
      <div><b>message:</b> {{ health.message }}</div>
    </div>
  </div>
</template>