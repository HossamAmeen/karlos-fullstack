<template>
  <div class="ui-card">
    <div v-if="$slots.header || $slots.title || $slots.description" class="ui-card-header">
      <slot name="header">
        <h2 v-if="$slots.title" class="ui-card-title"><slot name="title" /></h2>
        <p v-if="$slots.description" class="ui-card-description"><slot name="description" /></p>
      </slot>
    </div>
    <div class="ui-card-content">
      <slot />
    </div>
  </div>
</template>
