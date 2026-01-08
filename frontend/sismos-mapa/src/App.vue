<template>
  <MapView />
</template>

<script setup>
import MapView from './MapView.vue'
</script>

<style>
html,
body,
#app {
  margin: 0;
  padding: 0;
  height: 100%;
}

/* Evitar fondos raros */
body {
  background: #ffffff;
}
</style>