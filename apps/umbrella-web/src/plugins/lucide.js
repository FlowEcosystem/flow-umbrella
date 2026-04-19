import * as lucideIcons from "lucide-vue-next";

export default {
  install(app) {
    Object.entries(lucideIcons).forEach(([name, component]) => {
      app.component(name, component);
    });
  },
};
