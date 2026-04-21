import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  PanelLeft,
  PanelLeftClose,
  X,
  LayoutGrid,
  ChevronRight,
  ChevronDown,
  Settings,
  LogOut,
  House,
  MapPinned,
  Monitor,
  Users,
  AlertCircle,
} from 'lucide-vue-next'

const icons = {
  Shield,
  ShieldAlert,
  ShieldCheck,
  PanelLeft,
  PanelLeftClose,
  X,
  LayoutGrid,
  ChevronRight,
  ChevronDown,
  Settings,
  LogOut,
  House,
  MapPinned,
  Monitor,
  Users,
  AlertCircle,
}

export default {
  install(app) {
    Object.entries(icons).forEach(([name, component]) => {
      app.component(name, component)
    })
  },
}
