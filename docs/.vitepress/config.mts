import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "RaspVisionCar",
  description: "A VitePress Site",
  base: '/',
  srcDir: './docs',
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Examples', link: '/prologue '}
    ],

    sidebar: [
      {
        text: '快速开始',
        items: [
          { text: '简介', link: '/prologue' },
          { text: '硬件清单', link: '/hardware-list' },
          { text: '树莓派配置', link: '/quick-start/raspi' },
          { text: 'STM32配置', link: '/quick-start/stm32' },
        ]
      },
      {
        text: '决策系统',
        items: [
          { text: '树莓派USART通信', link: '/guide/usart' },
        ]
      }, 
      {
        text: '下位控制',
        items: [
          { text: 'Motor', link: '/guide/motor' },
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/vuejs/vitepress' }
    ]
  }
})
