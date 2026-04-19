<template>
  <div class="page-skeleton" aria-hidden="true">
    <div class="page-skeleton__header">
      <Skeleton class="page-skeleton__title" height="52px" />
      <Skeleton class="page-skeleton__subtitle page-skeleton__subtitle--wide" height="16px" />
      <Skeleton class="page-skeleton__subtitle page-skeleton__subtitle--narrow" height="16px" />
    </div>

    <div class="page-skeleton__grid">
      <div class="page-skeleton__card">
        <Skeleton class="page-skeleton__line page-skeleton__line--heading" height="18px" />
        <Skeleton class="page-skeleton__line" height="14px" />
        <Skeleton class="page-skeleton__line page-skeleton__line--short" height="14px" />
      </div>

      <div class="page-skeleton__card page-skeleton__card--muted">
        <Skeleton class="page-skeleton__line page-skeleton__line--heading" height="18px" />
        <Skeleton class="page-skeleton__line" height="14px" />
        <Skeleton class="page-skeleton__line page-skeleton__line--medium" height="14px" />
        <Skeleton class="page-skeleton__line page-skeleton__line--short" height="14px" />
      </div>
    </div>
  </div>
</template>
