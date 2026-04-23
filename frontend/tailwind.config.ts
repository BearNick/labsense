import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#10222d",
        mist: "#eef5f3",
        mint: "#dff5ea",
        alert: "#ffe4cf",
        danger: "#ffd6d1",
        line: "#cddad7"
      },
      boxShadow: {
        panel: "0 20px 60px rgba(16, 34, 45, 0.10)"
      },
      borderRadius: {
        "2xl": "1.5rem"
      }
    }
  },
  plugins: []
};

export default config;
