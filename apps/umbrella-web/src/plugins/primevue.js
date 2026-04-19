import PrimeVue from 'primevue/config'
import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'

const cssVar = (name) => `var(${name})`

const accentScale = {
  50: cssVar('--color-accent-50'),
  100: cssVar('--color-accent-100'),
  200: cssVar('--color-accent-200'),
  300: cssVar('--color-accent-300'),
  400: cssVar('--color-accent-400'),
  500: cssVar('--color-accent-500'),
  600: cssVar('--color-accent-600'),
  700: cssVar('--color-accent-700'),
  800: cssVar('--color-accent-800'),
  900: cssVar('--color-accent-900'),
  950: cssVar('--color-accent-950'),
}

const surfaceScale = {
  0: cssVar('--color-surface-0'),
  50: cssVar('--color-surface-50'),
  100: cssVar('--color-surface-100'),
  200: cssVar('--color-surface-200'),
  300: cssVar('--color-surface-300'),
  400: cssVar('--color-surface-400'),
  500: cssVar('--color-surface-500'),
  600: cssVar('--color-surface-600'),
  700: cssVar('--color-surface-700'),
  800: cssVar('--color-surface-800'),
  900: cssVar('--color-surface-900'),
  950: cssVar('--color-surface-950'),
}

const UmbrellaPreset = definePreset(Aura, {
  semantic: {
    primary: accentScale,
    colorScheme: {
      light: {
        surface: surfaceScale,
        primary: {
          color: cssVar('--color-accent'),
          contrastColor: cssVar('--color-text-on-accent'),
          hoverColor: cssVar('--color-accent-hover'),
          activeColor: cssVar('--color-accent-active'),
        },
        highlight: {
          background: cssVar('--color-accent-subtle'),
          focusBackground: '#442f24',
          color: cssVar('--color-accent'),
          focusColor: '#e58a58',
        },
        mask: {
          background: 'rgba(10, 10, 9, 0.5)',
          color: cssVar('--color-text'),
        },
        formField: {
          background: cssVar('--color-surface'),
          disabledBackground: cssVar('--color-surface-subtle'),
          filledBackground: cssVar('--color-surface'),
          filledHoverBackground: cssVar('--color-surface-hover'),
          filledFocusBackground: cssVar('--color-surface'),
          borderColor: cssVar('--color-border'),
          hoverBorderColor: cssVar('--color-border-strong'),
          focusBorderColor: cssVar('--color-accent'),
          invalidBorderColor: cssVar('--color-danger'),
          color: cssVar('--color-text'),
          disabledColor: cssVar('--color-text-muted'),
          placeholderColor: cssVar('--color-text-muted'),
          iconColor: cssVar('--color-text-secondary'),
          shadow: 'none',
        },
        text: {
          color: cssVar('--color-text'),
          hoverColor: cssVar('--color-text'),
          mutedColor: cssVar('--color-text-secondary'),
          hoverMutedColor: cssVar('--color-text'),
        },
        content: {
          background: cssVar('--color-surface'),
          hoverBackground: cssVar('--color-surface-hover'),
          borderColor: cssVar('--color-border'),
          color: cssVar('--color-text'),
          hoverColor: cssVar('--color-text'),
        },
        overlay: {
          select: {
            background: cssVar('--color-shell-overlay'),
            borderColor: cssVar('--color-border'),
            color: cssVar('--color-text'),
          },
          popover: {
            background: cssVar('--color-shell-overlay'),
            borderColor: cssVar('--color-border'),
            color: cssVar('--color-text'),
          },
          modal: {
            background: cssVar('--color-surface'),
            borderColor: cssVar('--color-border'),
            color: cssVar('--color-text'),
          },
        },
        navigation: {
          item: {
            focusBackground: '#2f2c28',
            activeBackground: cssVar('--color-accent-subtle'),
            color: cssVar('--color-text-secondary'),
            focusColor: cssVar('--color-text'),
            activeColor: cssVar('--color-accent'),
            icon: {
              color: cssVar('--color-text-secondary'),
              focusColor: cssVar('--color-text'),
              activeColor: cssVar('--color-accent'),
            },
          },
          submenuLabel: {
            background: 'transparent',
            color: cssVar('--color-text-muted'),
          },
          submenuIcon: {
            color: cssVar('--color-text-secondary'),
            focusColor: cssVar('--color-text'),
            activeColor: cssVar('--color-accent'),
          },
        },
      },
    },
    focusRing: {
      width: '2px',
      style: 'solid',
      color: cssVar('--color-accent'),
      offset: '2px',
      shadow: 'none',
    },
  },
})

export default {
  install(app) {
    app.use(PrimeVue, {
      theme: {
        preset: UmbrellaPreset,
        options: {
          darkModeSelector: '.app-dark',
        },
      },
      locale: {
        accept: 'Подтвердить',
        reject: 'Отмена',
        choose: 'Выбрать',
        upload: 'Загрузить',
        cancel: 'Отмена',
        clear: 'Очистить',
        today: 'Сегодня',
        weekHeader: 'Нед',
        firstDayOfWeek: 1,
        dayNames: ['воскресенье', 'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота'],
        dayNamesShort: ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'],
        dayNamesMin: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'],
        monthNames: [
          'январь',
          'февраль',
          'март',
          'апрель',
          'май',
          'июнь',
          'июль',
          'август',
          'сентябрь',
          'октябрь',
          'ноябрь',
          'декабрь',
        ],
        monthNamesShort: ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'],
        showPassword: 'Показать пароль',
        hidePassword: 'Скрыть пароль',
        passwordPrompt: 'Введите пароль',
        weak: 'Слабый',
        medium: 'Средний',
        strong: 'Надёжный',
        emptyMessage: 'Нет данных',
        emptyFilterMessage: 'Ничего не найдено',
      },
    })
    app.use(ToastService)
    app.use(ConfirmationService)
    app.directive('tooltip', Tooltip)
  },
}
