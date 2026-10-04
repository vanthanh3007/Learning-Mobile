/**
 * Design tokens dung chung cho toan bo portfolio.
 *
 * Phai nap SAU thu tay cdn.tailwindcss.com va TRUOC khi </head> dong lai —
 * Tailwind Play CDN doc window.tailwind.config o thoi diem quet DOM.
 *
 * He mau ke thua tu cv-tran-van-thanh.html de 2 ban CV nhin nhu mot.
 */
tailwind.config = {
  theme: {
    extend: {
      fontFamily: {
        heading: ['Poppins', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      colors: {
        primary: '#18181B',   // text chinh / nen chip dac
        secondary: '#3F3F46',  // body text
        accent: '#2563EB',     // link, nhan manh, trang thai active
        surface: '#FAFAFA',    // nen trang
        border: '#E4E4E7',     // duong ke
        muted: '#71717A',      // text phu — van dat 4.5:1 tren nen #FAFAFA
      },
      maxWidth: {
        // Mot gia tri duy nhat cho moi container de cac trang thang hang nhau.
        content: '64rem',
      },
    },
  },
}
